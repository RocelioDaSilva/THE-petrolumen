from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import structlog
from gaia_genesis.pvt import calculate_zfactor, gas_viscosity_lee, oil_bubble_point_standing, oil_fvf_standing
from auth_utils import get_current_active_user, UserResponse

logger = structlog.get_logger()
router = APIRouter(tags=["PVT"])

class ZFactorRequest(BaseModel):
    pressure: float = Field(..., gt=0)
    temperature: float = Field(..., gt=-460)
    gamma_g: float = Field(..., gt=0)

class ZFactorResponse(BaseModel):
    z_factor: float

@router.post("/z-factor", response_model=ZFactorResponse)
async def get_z_factor(data: ZFactorRequest, user: UserResponse = Depends(get_current_active_user)):
    log = logger.bind(user_id=str(user.id))
    log.info("Calculating Z-factor", pressure=data.pressure, temp=data.temperature)
    try:
        z = calculate_zfactor(data.pressure, data.temperature, data.gamma_g)
        return {"z_factor": z}
    except Exception as e:
        log.error("Z-factor calculation failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

class ViscosityRequest(BaseModel):
    pressure: float
    temperature: float
    gamma_g: float
    z: float

@router.post("/gas-viscosity")
async def get_gas_viscosity(data: ViscosityRequest, user: UserResponse = Depends(get_current_active_user)):
    log = logger.bind(user_id=str(user.id))
    try:
        mu = gas_viscosity_lee(data.pressure, data.temperature, data.gamma_g, data.z)
        return {"viscosity": mu}
    except Exception as e:
        log.error("Gas viscosity calculation failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/oil-bubble-point")
async def get_oil_bubble_point(rs: float, gamma_g: float, api: float, temp: float, user: UserResponse = Depends(get_current_active_user)):
    return {"pb": oil_bubble_point_standing(rs, gamma_g, api, temp)}
