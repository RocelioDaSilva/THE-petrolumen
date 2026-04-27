from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
import structlog
from gaia_genesis.dca_advanced import arps_hyperbolic, perform_duong, monte_carlo_eur
from auth_utils import get_current_active_user, UserResponse

logger = structlog.get_logger()
router = APIRouter(tags=["DCA"])

class DCARequest(BaseModel):
    time: List[float]
    rate: List[float]

@router.post("/duong")
async def analyze_duong(data: DCARequest, user: UserResponse = Depends(get_current_active_user)):
    log = logger.bind(user_id=str(user.id))
    log.info("Running Duong analysis", num_points=len(data.time))
    try:
        result = perform_duong(np.array(data.time), np.array(data.rate))
        return result
    except Exception as e:
        log.error("Duong analysis failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/monte-carlo-eur")
async def get_mc_eur(data: DCARequest, user: UserResponse = Depends(get_current_active_user)):
    log = logger.bind(user_id=str(user.id))
    try:
        return monte_carlo_eur(np.array(data.time), np.array(data.rate))
    except Exception as e:
        log.error("Monte Carlo EUR failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
