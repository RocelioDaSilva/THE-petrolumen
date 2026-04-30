from fastapi import APIRouter, Depends, Body, HTTPException
from typing import List, Dict, Optional
from pydantic import BaseModel
from auth_utils import get_current_active_user
from ...economics import run_economics

router = APIRouter()


class EconomicsAnalysisRequest(BaseModel):
    forecast: List[Dict]
    oil_price: float
    opex_fixed: float
    opex_var: float
    capex: float
    tax_rate: Optional[float] = 0.2
    discount_rate: Optional[float] = 0.1


@router.post("/analysis")
async def calculate_economics(
    data: EconomicsAnalysisRequest, user=Depends(get_current_active_user)
):
    try:
        return run_economics(
            data.forecast,
            data.oil_price,
            data.opex_fixed,
            data.opex_var,
            data.capex,
            data.tax_rate,
            data.discount_rate,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class EconomicsRunRequest(BaseModel):
    forecast_time: List[float]
    forecast_rate: List[float]
    oil_price: float
    opex_fixed: float
    opex_var: float
    capex: float
    tax_rate: Optional[float] = 0.2
    discount_rate: Optional[float] = 0.1


@router.post("/run")
async def run_economics_test(
    data: EconomicsRunRequest, user=Depends(get_current_active_user)
):
    try:
        forecast = [
            {"time": t, "rate": r}
            for t, r in zip(data.forecast_time, data.forecast_rate)
        ]
        return run_economics(
            forecast,
            data.oil_price,
            data.opex_fixed,
            data.opex_var,
            data.capex,
            data.tax_rate,
            data.discount_rate,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
