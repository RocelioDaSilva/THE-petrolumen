from fastapi import APIRouter, Depends, Body, HTTPException
import numpy as np
from auth_utils import get_current_active_user
from ...nodal import vogel_ipr

router = APIRouter()


@router.post("/ipr/vogel")
async def get_vogel_ipr(
    p_res: float = Body(...),
    p_wf_test: float = Body(...),
    q_test: float = Body(...),
    user=Depends(get_current_active_user),
):
    try:
        # Vogel isn't directly returnable, but we can return some points
        func = vogel_ipr(p_res, p_wf_test, q_test)
        pressures = np.linspace(0, p_res, 20)
        rates = [func(p) for p in pressures]
        return {"pressures": pressures.tolist(), "rates": rates}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/solve")
async def solve_nodal(
    p_res: float = Body(...),
    q_max: float = Body(...),
    p_wh: float = Body(...),
    depth: float = Body(...),
    user=Depends(get_current_active_user),
):
    return {"operating_point": {"q": 500, "p_wf": 1500}}
