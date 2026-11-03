from pydantic import BaseModel
from typing import Optional


class ZFactorRequest(BaseModel):
    pressure: float  # in psia
    temperature: (
        float  # in Rankine for some correlations, ensure consistency or convert
    )
    gas_specific_gravity: float


class ZFactorResponse(BaseModel):
    z_factor: float


class FormationVolumeFactorRequest(BaseModel):
    pressure: float
    temperature: float
    fluid_type: str  # 'oil' or 'gas'
    api_gravity: Optional[float] = None
    gas_specific_gravity: Optional[float] = None


class FormationVolumeFactorResponse(BaseModel):
    fvf: float  # Formation Volume Factor (Bo or Bg)


class ViscosityRequest(BaseModel):
    pressure: float
    temperature: float
    fluid_type: str  # 'oil' or 'gas'
    api_gravity: Optional[float] = None
    gas_specific_gravity: Optional[float] = None


class ViscosityResponse(BaseModel):
    viscosity: float  # in cP


class SolutionGasRatioRequest(BaseModel):
    pressure: float
    temperature: float
    api_gravity: float
    gas_specific_gravity: float


class SolutionGasRatioResponse(BaseModel):
    rs: float  # Solution Gas-Oil Ratio (scf/stb)
