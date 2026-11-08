from typing import Literal
from pydantic import BaseModel, Field

class PZPoint(BaseModel):
    pz_psia: float
    Gp_scf: float = Field(..., ge=0.0)

class PZDiagRequest(BaseModel):
    points: list[PZPoint] = Field(..., min_length=4)

class PZDiagResponse(BaseModel):
    linear_r2: float
    quadratic_r2: float
    quadratic_ratio: float
    classification: Literal["volumetric", "partial_water_drive",
                            "complete_water_drive"]
    b_linear: float
    c_quadratic: float
