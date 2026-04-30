from fastapi import APIRouter, Depends, Body, HTTPException
from typing import List, Dict
import numpy as np
from auth_utils import get_current_active_user
from ...dca_advanced import perform_arps_fit, perform_duong_fit

router = APIRouter()


@router.post("/fit")
async def fit_dca(
    time: List[float] = Body(...),
    rate: List[float] = Body(...),
    model_type: str = Body("hyperbolic"),
    user=Depends(get_current_active_user),
):
    t_np = np.array(time)
    r_np = np.array(rate)

    if model_type == "duong":
        result = perform_duong_fit(t_np, r_np)
    else:
        result = perform_arps_fit(t_np, r_np)


@router.post("/duong")
async def fit_duong(
    time: List[float] = Body(...),
    rate: List[float] = Body(...),
    user=Depends(get_current_active_user),
):
    result = perform_duong_fit(np.array(time), np.array(rate))
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
