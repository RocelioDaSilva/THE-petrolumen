from fastapi import APIRouter, Depends, HTTPException, Body
from auth_utils import get_current_active_user
from ...pvt import (
    calculate_zfactor,
    gas_viscosity_lee,
    oil_bubble_point_standing,
)

router = APIRouter()


@router.post("/z-factor")
async def get_z_factor(
    pressure: float = Body(...),
    temperature: float = Body(...),
    gamma_g: float = Body(...),
    user=Depends(get_current_active_user),
):
    try:
        z = calculate_zfactor(pressure, temperature, gamma_g)
        return {"z_factor": z}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/gas-viscosity")
async def get_gas_viscosity(
    pressure: float = Body(...),
    temperature: float = Body(...),
    gamma_g: float = Body(...),
    z: float = Body(...),
    user=Depends(get_current_active_user),
):
    try:
        mu_g = gas_viscosity_lee(pressure, temperature, gamma_g, z)
        return {"gas_viscosity": mu_g}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/oil-bubble-point")
async def get_oil_bubble_point(
    rs: float = Body(...),
    gamma_g: float = Body(...),
    api: float = Body(...),
    temperature: float = Body(...),
    user=Depends(get_current_active_user),
):
    try:
        pb = oil_bubble_point_standing(rs, gamma_g, api, temperature)
        return {"bubble_point": pb}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
