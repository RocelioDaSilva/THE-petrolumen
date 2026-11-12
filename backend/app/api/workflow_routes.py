"""Workflow API routes for integrated reservoir evaluation workflows."""

from __future__ import annotations

import os
import shutil
import tempfile
import time
from typing import Any, Literal
from uuid import uuid4

import lasio
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter()

SESSIONS: dict[str, dict[str, Any]] = {}
SESSION_TTL_SECONDS = 3600.0


def _cleanup_expired_sessions() -> None:
    """Evict sessions that have exceeded the TTL."""
    now = time.time()
    expired_keys = [
        key
        for key, session in SESSIONS.items()
        if now - session.get("created_at", 0.0) > SESSION_TTL_SECONDS
    ]
    for key in expired_keys:
        SESSIONS.pop(key, None)


# ============================================================
# MODELS
# ============================================================

class OoipUploadResponse(BaseModel):
    session_id: str
    well_summary: dict[str, Any]
    curve_list: list[str]
    depth_range: list[float]


class ArchieParams(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    a: float = Field(default=1.0, gt=0)
    m: float = Field(default=2.0, gt=0)
    n: float = Field(default=2.0, gt=0)
    Rw: float = Field(
        default=0.1,
        gt=0,
        description="Formation water resistivity (ohm-m)",
    )


class OoipRunRequest(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    session_id: str
    area_acres: float = Field(gt=0, example=100.0)
    net_to_gross_cutoff: float = Field(default=0.5, ge=0, le=1)
    water_saturation_method: Literal["archie"] = "archie"
    archie_params: ArchieParams = Field(default_factory=ArchieParams)


class OoipRunResponse(BaseModel):
    net_pay_ft: float
    gross_pay_ft: float
    net_to_gross: float
    average_porosity: float
    average_sw: float
    ooip_bbl: float
    ooip_stb_per_acre_ft: float
    facies_breakdown: dict[str, dict[str, float]]
    per_curve_summary: dict[str, dict[str, float]]
    note: str


# ============================================================
# ENDPOINTS
# ============================================================

@router.post(
    "/workflow/ooip/upload",
    tags=["Workflow"],
    response_model=OoipUploadResponse,
)
async def upload_ooip_las(file: UploadFile = File(...)) -> OoipUploadResponse:
    """Upload and parse a .las well log file, storing it in an in-memory session."""
    _cleanup_expired_sessions()

    filename = file.filename or ""
    if not filename.lower().endswith(".las"):
        raise HTTPException(
            status_code=422,
            detail="Invalid file format. Only .las files are supported.",
        )

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".las", delete=False) as tmp:
            temp_path = tmp.name
            shutil.copyfileobj(file.file, tmp)

        try:
            las = lasio.read(temp_path)
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Failed to parse LAS file: {exc}",
            ) from exc

        well_metadata: dict[str, Any] = {}
        for item in las.well:
            val = item.value
            if isinstance(val, (np.integer, np.floating)):
                val = val.item()
            well_metadata[item.mnemonic] = val

        curves_dict: dict[str, np.ndarray] = {}
        curve_names: list[str] = []
        for curve in las.curves:
            mnemonic = curve.mnemonic
            curve_names.append(mnemonic)
            curves_dict[mnemonic] = np.asarray(curve.data, dtype=float)

        depth_array = np.asarray(las.index, dtype=float)
        if len(depth_array) > 0:
            depth_range = [float(depth_array[0]), float(depth_array[-1])]
        else:
            depth_range = [0.0, 0.0]

        session_id = uuid4().hex
        SESSIONS[session_id] = {
            "curves": curves_dict,
            "depth": depth_array,
            "well": well_metadata,
            "created_at": time.time(),
        }

        return OoipUploadResponse(
            session_id=session_id,
            well_summary=well_metadata,
            curve_list=curve_names,
            depth_range=depth_range,
        )

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        await file.close()


@router.post(
    "/workflow/ooip/run",
    tags=["Workflow"],
    response_model=OoipRunResponse,
)
def run_ooip_calculation(payload: OoipRunRequest) -> OoipRunResponse:
    """Execute volumetric OOIP calculation over stored session log data."""
    _cleanup_expired_sessions()

    session = SESSIONS.get(payload.session_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired",
        )

    curves: dict[str, np.ndarray] = session.get("curves", {})
    depth: np.ndarray = session.get("depth", np.array([]))

    if len(depth) == 0:
        raise HTTPException(
            status_code=422,
            detail="LAS file contains no depth samples.",
        )

    # Find porosity curve (case-insensitive match)
    porosity_candidates = ["PHIE", "PHI", "POR", "NPHI"]
    porosity_curve_name = None
    for cand in porosity_candidates:
        for cname in curves:
            if cname.upper() == cand.upper():
                porosity_curve_name = cname
                break
        if porosity_curve_name:
            break

    if not porosity_curve_name:
        raise HTTPException(
            status_code=422,
            detail="No porosity curve in LAS. Need one of PHIE/PHI/POR/NPHI.",
        )

    porosity = curves[porosity_curve_name].copy()

    # Find resistivity curve (case-insensitive match)
    resistivity_candidates = ["RT", "RES", "LLD", "ILD", "RESD"]
    resistivity_curve_name = None
    for cand in resistivity_candidates:
        for cname in curves:
            if cname.upper() == cand.upper():
                resistivity_curve_name = cname
                break
        if resistivity_curve_name:
            break

    if resistivity_curve_name:
        rt = curves[resistivity_curve_name].copy()
    else:
        # Default fallback resistivity if none is logged
        rt = np.full_like(porosity, 20.0)

    # Compute Sw via Archie per sample: Sw = ((a * Rw) / (Rt * phi**m)) ** (1/n)
    # Clamp to [0,1]. Skip samples where Rt<=0 or phi<=0.
    a = payload.archie_params.a
    m = payload.archie_params.m
    n = payload.archie_params.n
    rw = payload.archie_params.Rw

    sw = np.full_like(porosity, np.nan, dtype=float)
    valid_archie = (rt > 0) & (porosity > 0) & np.isfinite(rt) & np.isfinite(porosity)

    with np.errstate(divide="ignore", invalid="ignore"):
        denom = rt[valid_archie] * (porosity[valid_archie] ** m)
        ratio = (a * rw) / denom
        computed_sw = np.power(ratio, 1.0 / n)
        computed_sw = np.clip(computed_sw, 0.0, 1.0)
        sw[valid_archie] = computed_sw

    # depth_step = median of diff(depth array)
    if len(depth) > 1:
        depth_step = float(np.median(np.diff(depth)))
        if depth_step <= 0:
            depth_step = 1.0
    else:
        depth_step = 1.0

    gross_pay_ft = float(depth.max() - depth.min() + depth_step)

    # mask = porosity > net_to_gross_cutoff AND finite porosity AND finite sw
    mask = (porosity > payload.net_to_gross_cutoff) & np.isfinite(porosity) & np.isfinite(sw)
    mask_count = int(mask.sum())

    net_pay_ft = float(mask_count * depth_step)

    if mask_count > 0:
        average_porosity = float(porosity[mask].mean())
        average_sw = float(sw[mask].mean())
    else:
        average_porosity = 0.0
        average_sw = 0.0

    net_to_gross = float(net_pay_ft / gross_pay_ft) if gross_pay_ft > 0 else 0.0

    bo = 1.2
    ooip_bbl = float(
        7758.0 * payload.area_acres * net_pay_ft * average_porosity * (1.0 - average_sw) / bo
    )
    ooip_stb_per_acre_ft = float(
        7758.0 * average_porosity * (1.0 - average_sw) / bo
    )

    # Facies breakdown
    facies_breakdown: dict[str, dict[str, float]] = {}
    facies_curve_name = None
    for cname in curves:
        if cname.upper() == "FACIES":
            facies_curve_name = cname
            break

    if facies_curve_name is not None and mask_count > 0:
        facies_data = curves[facies_curve_name][mask]
        unique_facies = np.unique(facies_data)
        for f_val in unique_facies:
            count = int(np.sum(facies_data == f_val))
            thickness = float(count * depth_step)
            pct = float(count / mask_count * 100.0)
            facies_breakdown[str(f_val)] = {
                "thickness_ft": thickness,
                "percentage": pct,
            }

    # Per curve summary
    per_curve_summary: dict[str, dict[str, float]] = {}

    def _add_curve_summary(name: str, arr: np.ndarray, used_mask: np.ndarray) -> None:
        sub = arr[used_mask]
        finite_sub = sub[np.isfinite(sub)]
        if len(finite_sub) > 0:
            per_curve_summary[name] = {
                "min": float(np.min(finite_sub)),
                "max": float(np.max(finite_sub)),
                "mean": float(np.mean(finite_sub)),
                "samples_used": float(len(finite_sub)),
            }
        else:
            per_curve_summary[name] = {
                "min": 0.0,
                "max": 0.0,
                "mean": 0.0,
                "samples_used": 0.0,
            }

    _add_curve_summary(porosity_curve_name, porosity, mask)
    if resistivity_curve_name:
        _add_curve_summary(resistivity_curve_name, rt, mask)
    _add_curve_summary("SW", sw, mask)

    note = (
        "Bo=1.2 default (no PVT data in LAS); "
        "net pay defined as porosity > cutoff; "
        "Sw via Archie with a/m/n/Rw from request"
    )

    return OoipRunResponse(
        net_pay_ft=net_pay_ft,
        gross_pay_ft=gross_pay_ft,
        net_to_gross=net_to_gross,
        average_porosity=average_porosity,
        average_sw=average_sw,
        ooip_bbl=ooip_bbl,
        ooip_stb_per_acre_ft=ooip_stb_per_acre_ft,
        facies_breakdown=facies_breakdown,
        per_curve_summary=per_curve_summary,
        note=note,
    )
