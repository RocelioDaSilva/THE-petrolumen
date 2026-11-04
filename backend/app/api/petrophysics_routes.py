"""HTTP endpoints for Petrophysics operations."""

from __future__ import annotations

import os
import shutil
import tempfile
from typing import Any

import lasio
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

router = APIRouter()


class CurveStats(BaseModel):
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    null_count: int


class LasParseResponse(BaseModel):
    well: dict[str, Any]
    curves: list[str]
    row_count: int
    depth_range: list[float]
    curve_stats: dict[str, CurveStats]


@router.post("/petrophysics/las/parse", tags=["Petrophysics"], response_model=LasParseResponse)
async def parse_las(file: UploadFile = File(...)) -> LasParseResponse:
    """Parse an uploaded .las file and return well metadata, curve names, and statistics."""
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

        # Extract well section metadata
        well_metadata: dict[str, Any] = {}
        for item in las.well:
            val = item.value
            # Convert numpy types to native Python types for JSON serialization
            if isinstance(val, (np.integer, np.floating)):
                val = val.item()
            well_metadata[item.mnemonic] = val

        # Extract curve names
        curve_names = [curve.mnemonic for curve in las.curves]
        row_count = len(las.index)

        # Extract depth range
        if len(las.index) > 0:
            depth_start = float(las.index[0])
            depth_stop = float(las.index[-1])
            depth_range = [depth_start, depth_stop]
        else:
            depth_range = [0.0, 0.0]

        # Calculate curve statistics
        curve_stats: dict[str, CurveStats] = {}
        for curve in las.curves:
            data = curve.data
            nan_mask = np.isnan(data)
            null_count = int(np.sum(nan_mask))
            valid_data = data[~nan_mask]

            if len(valid_data) > 0:
                c_min = float(np.min(valid_data))
                c_max = float(np.max(valid_data))
                c_mean = float(np.mean(valid_data))
            else:
                c_min = None
                c_max = None
                c_mean = None

            curve_stats[curve.mnemonic] = CurveStats(
                min=c_min,
                max=c_max,
                mean=c_mean,
                null_count=null_count,
            )

        return LasParseResponse(
            well=well_metadata,
            curves=curve_names,
            row_count=row_count,
            depth_range=depth_range,
            curve_stats=curve_stats,
        )

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        await file.close()
