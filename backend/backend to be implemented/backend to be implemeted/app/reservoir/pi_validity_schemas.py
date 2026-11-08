"""Pydantic v2 schemas for the PI-validity endpoint."""
from typing import Literal
from pydantic import BaseModel, Field, model_validator

WellType = Literal["vertical", "deviated", "horizontal", "multilateral"]


class PIValidityRequest(BaseModel):
    PI_sim_stb_d_psi: float = Field(..., gt=0.0)
    k_md: float = Field(..., gt=0.0)
    h_ft: float = Field(..., gt=0.0)
    mu_cp: float = Field(..., gt=0.0)
    B_bbl_stb: float = Field(..., gt=0.0)
    r_e_ft: float = Field(..., gt=0.0)
    r_w_ft: float = Field(..., gt=0.0)
    S: float = Field(0.0)
    well_type: WellType = Field(default="vertical")
    num_laterals: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _chk(self) -> "PIValidityRequest":
        if self.r_e_ft <= self.r_w_ft:
            raise ValueError("r_e_ft must exceed r_w_ft")
        return self


class PIValidityResponse(BaseModel):
    PI_analytical_stb_d_psi: float = Field(..., gt=0.0)
    PI_simulated_stb_d_psi: float = Field(..., gt=0.0)
    ratio: float = Field(..., gt=0.0)
    classification: str
    recommendation: str
