from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
from gaia_genesis.reservoir_engineering_calcs import (
    calculate_ogip_volumetric,
    calculate_stoiip_volumetric,
    pz_analysis,
)
from auth_utils import get_current_active_user

router = APIRouter(tags=["Reservoir"])


class OGIPVolRequest(BaseModel):
    area: float
    thickness: float
    porosity: float
    sw: float
    bg: float


@router.post("/ogip-volumetric")
async def get_ogip_vol(data: OGIPVolRequest, user=Depends(get_current_active_user)):
    return {
        "ogip": calculate_ogip_volumetric(
            data.area, data.thickness, data.porosity, data.sw, data.bg
        )
    }


class PZRequest(BaseModel):
    pressure: List[float]
    z: List[float]
    gp: List[float]


@router.post("/pz-analysis")
async def analyze_pz(data: PZRequest, user=Depends(get_current_active_user)):
    return pz_analysis(np.array(data.pressure), np.array(data.z), np.array(data.gp))
