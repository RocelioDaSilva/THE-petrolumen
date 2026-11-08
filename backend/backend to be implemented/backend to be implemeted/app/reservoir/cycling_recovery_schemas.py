from pydantic import BaseModel, Field


class CyclingRequest(BaseModel):
    E_d: float = Field(..., ge=0.0, le=1.0)
    E_a: float = Field(..., ge=0.0, le=1.0)
    E_s: float = Field(..., ge=0.0, le=1.0)


class CyclingResponse(BaseModel):
    E_total: float
    sens_E_d: float
    sens_E_a: float
    sens_E_s: float
