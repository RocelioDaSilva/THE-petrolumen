from fastapi import APIRouter, Depends, Body, HTTPException
from typing import List
import numpy as np
from auth_utils import get_current_active_user
from ...rta import fmb_gas

router = APIRouter()


@router.post("/fmb-gas")
async def rta_fmb_gas(
    pwf: List[float] = Body(...),
    gp: List[float] = Body(...),
    pi: float = Body(...),
    tf: float = Body(...),
    gamma_g: float = Body(...),
    user=Depends(get_current_active_user),
):
    try:
        return fmb_gas(np.array(pwf), np.array(gp), pi, tf, gamma_g)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
