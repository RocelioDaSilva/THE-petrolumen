"""Validated API routes for reservoir compressibility calculations."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import Field

from .base import APIModel as BaseModel

from app.engines.reservoir.compressibility import (
    GasCompressibilityResult,
    LIMESTONE_PHI_RANGE,
    SANDSTONE_PHI_RANGE,
    formation_compressibility,
    gas_compressibility_from_z_curve,
    total_compressibility,
)
from app.engines.reservoir.pvt import calculate_z_factor_hall_yarborough_unrounded

router = APIRouter()


class RockCompressibilityRequest(BaseModel):
    phi: float = Field(gt=0.0, lt=1.0, allow_inf_nan=False)
    rock_type: Literal["sandstone", "limestone"]
    strict: bool = False


class RockCompressibilityResponse(BaseModel):
    cf_psi_inv: float
    rock_type: Literal["sandstone", "limestone"]
    in_validity_range: bool


class GasCompressibilityRequest(BaseModel):
    p_psia: float = Field(gt=0.0, allow_inf_nan=False)
    temperature_f: float = Field(gt=-459.67, allow_inf_nan=False)
    gas_sg: float = Field(gt=0.0, lt=2.0, allow_inf_nan=False)
    h_psi: float | None = Field(default=None, gt=0.0, allow_inf_nan=False)


class GasCompressibilityResponse(BaseModel):
    cg_psi_inv: float
    z_at_p: float
    dz_dp_psi_inv: float
    h_psi: float
    method: Literal["central", "forward"]
    z_correlation: Literal[
        "Hall-Yarborough with Sutton pseudocritical properties"
    ] = "Hall-Yarborough with Sutton pseudocritical properties"


class TotalCompressibilityRequest(GasCompressibilityRequest):
    phi: float = Field(gt=0.0, lt=1.0, allow_inf_nan=False)
    rock_type: Literal["sandstone", "limestone"]
    strict_rock_range: bool = False
    co_psi_inv: float = Field(ge=0.0, allow_inf_nan=False)
    cw_psi_inv: float = Field(ge=0.0, allow_inf_nan=False)
    sg: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    so: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    sw: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)


class TotalCompressibilityResponse(BaseModel):
    ct_psi_inv: float
    cg_psi_inv: float
    cf_psi_inv: float
    z_at_p: float
    dz_dp_psi_inv: float
    in_rock_validity_range: bool
    z_correlation: Literal[
        "Hall-Yarborough with Sutton pseudocritical properties"
    ] = "Hall-Yarborough with Sutton pseudocritical properties"


@router.post(
    "/engine/reservoir/compressibility/rock",
    tags=["Reservoir"],
    response_model=RockCompressibilityResponse,
)
def calculate_rock_compressibility(
    payload: RockCompressibilityRequest,
) -> RockCompressibilityResponse:
    """Estimate pore-volume compressibility using Newman's correlation."""
    validity_range = _rock_phi_range(payload.rock_type)
    try:
        cf = formation_compressibility(
            phi=payload.phi,
            rock_type=payload.rock_type,
            strict=payload.strict,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RockCompressibilityResponse(
        cf_psi_inv=cf,
        rock_type=payload.rock_type,
        in_validity_range=validity_range[0] <= payload.phi <= validity_range[1],
    )


@router.post(
    "/engine/reservoir/compressibility/gas",
    tags=["Reservoir"],
    response_model=GasCompressibilityResponse,
)
def calculate_gas_compressibility(
    payload: GasCompressibilityRequest,
) -> GasCompressibilityResponse:
    """Calculate gas isothermal compressibility from the Hall-Yarborough Z curve."""
    try:
        result = _calculate_gas(payload)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return GasCompressibilityResponse(
        cg_psi_inv=result.cg_psi_inv,
        z_at_p=result.z_at_p,
        dz_dp_psi_inv=result.dz_dp_psi_inv,
        h_psi=result.h_psi,
        method=result.method,
    )


@router.post(
    "/engine/reservoir/compressibility/total",
    tags=["Reservoir"],
    response_model=TotalCompressibilityResponse,
)
def calculate_total_compressibility(
    payload: TotalCompressibilityRequest,
) -> TotalCompressibilityResponse:
    """Calculate total compressibility from phase properties and saturations."""
    try:
        gas = _calculate_gas(payload)
        cf = formation_compressibility(
            phi=payload.phi,
            rock_type=payload.rock_type,
            strict=payload.strict_rock_range,
        )
        ct = total_compressibility(
            cg_psi_inv=gas.cg_psi_inv,
            co_psi_inv=payload.co_psi_inv,
            cw_psi_inv=payload.cw_psi_inv,
            cf_psi_inv=cf,
            sg=payload.sg,
            so=payload.so,
            sw=payload.sw,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    validity_range = _rock_phi_range(payload.rock_type)
    return TotalCompressibilityResponse(
        ct_psi_inv=ct,
        cg_psi_inv=gas.cg_psi_inv,
        cf_psi_inv=cf,
        z_at_p=gas.z_at_p,
        dz_dp_psi_inv=gas.dz_dp_psi_inv,
        in_rock_validity_range=(
            validity_range[0] <= payload.phi <= validity_range[1]
        ),
    )


def _calculate_gas(payload: GasCompressibilityRequest) -> GasCompressibilityResult:
    def z_func(pressure: float) -> float:
        return calculate_z_factor_hall_yarborough_unrounded(
            pressure, payload.temperature_f, payload.gas_sg
        )

    return gas_compressibility_from_z_curve(
        p_psia=payload.p_psia,
        z_func=z_func,
        h_psi=payload.h_psi,
    )


def _rock_phi_range(
    rock_type: Literal["sandstone", "limestone"],
) -> tuple[float, float]:
    if rock_type == "sandstone":
        return SANDSTONE_PHI_RANGE
    return LIMESTONE_PHI_RANGE
