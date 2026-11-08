from pydantic import BaseModel, Field

class PoroAvgCompRequest(BaseModel):
    phi: float = Field(..., gt=0.0, lt=1.0)
    c_fluid_psi_inv: float = Field(..., ge=0.0)
    c_rock_psi_inv: float = Field(..., ge=0.0)

class PoroAvgCompResponse(BaseModel):
    c_eff_psi_inv: float = Field(..., ge=0.0)
    fluid_fraction: float
    rock_fraction: float
