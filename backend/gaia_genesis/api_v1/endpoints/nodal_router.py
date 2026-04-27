from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
import numpy as np
from gaia_genesis.nodal import solve_nodal
from auth_utils import get_current_active_user

router = APIRouter(tags=["Nodal"])

class NodalRequest(BaseModel):
    p_res: float
    q_max: float
    p_wh: float
    depth: float

@router.post("/solve")
async def analyze_nodal(data: NodalRequest, user=Depends(get_current_active_user)):
    return solve_nodal(data.p_res, data.q_max, data.p_wh, data.depth)
