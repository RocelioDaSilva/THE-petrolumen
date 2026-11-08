from pydantic import BaseModel, Field

class StratTransRequest(BaseModel):
    Z_m: list[list[list[float]]]
    k_md: list[list[list[float]]]
    dx_m: float = Field(..., gt=0.0)
    dy_m: float = Field(..., gt=0.0)

class StratTransResponse(BaseModel):
    TX: list[list[list[float]]]
    TY: list[list[list[float]]]
    TZ: list[list[list[float]]]
    hz_min: float
    hz_max: float
