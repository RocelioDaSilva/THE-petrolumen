from typing import Literal
from pydantic import BaseModel, Field

class DamageRadiusRequest(BaseModel):
    S: float = Field(..., ge=0.0)
    k_e_md: float = Field(..., gt=0.0)
    k_a_md: float = Field(..., gt=0.0)
    r_w_ft: float = Field(..., gt=0.0)

class DamagePermRequest(BaseModel):
    S: float = Field(...)
    k_e_md: float = Field(..., gt=0.0)
    r_a_ft: float = Field(..., gt=0.0)
    r_w_ft: float = Field(..., gt=0.0)

class DamageDepthResponse(BaseModel):
    method: Literal["radius", "permeability"]
    r_a_ft: float
    r_a_over_rw: float
    k_a_md: float
    k_e_md: float
    S: float
    remediation: str
