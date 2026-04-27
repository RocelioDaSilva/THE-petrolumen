from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np
import structlog
from gaia_genesis.rta import fmb_gas, fmb_oil
from auth_utils import get_current_active_user, UserResponse

logger = structlog.get_logger()
router = APIRouter(tags=["RTA"])

class RTAGasRequest(BaseModel):
    pwf: List[float]
    gp: List[float]
    pi: float
    tf: float
    gamma_g: float

@router.post("/fmb-gas")
async def analyze_fmb_gas(data: RTAGasRequest, user: UserResponse = Depends(get_current_active_user)):
    log = logger.bind(user_id=str(user.id))
    log.info("Running FMB Gas analysis")
    try:
        return fmb_gas(np.array(data.pwf), np.array(data.gp), data.pi, data.tf, data.gamma_g)
    except Exception as e:
        log.error("FMB Gas analysis failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
