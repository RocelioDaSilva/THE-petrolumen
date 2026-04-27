from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
import numpy as np
from gaia_genesis.economics import run_economics
from auth_utils import get_current_active_user

router = APIRouter(tags=["Economics"])

class EconomicsRequest(BaseModel):
    forecast_time: List[float]
    forecast_rate: List[float]
    oil_price: float
    capex: float
    opex_fixed: float
    opex_var: float
    discount_rate: float

@router.post("/run")
async def analyze_economics(data: EconomicsRequest, user=Depends(get_current_active_user)):
    return run_economics(
        np.array(data.forecast_time),
        np.array(data.forecast_rate),
        data.oil_price,
        data.capex,
        data.opex_fixed,
        data.opex_var,
        data.discount_rate
    )
