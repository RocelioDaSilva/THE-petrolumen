"""Pydantic v2 schemas for the constraint-swap endpoint."""
from pydantic import BaseModel, Field, model_validator


class SwapCheckRequest(BaseModel):
    p1_psia: float = Field(..., gt=0.0)
    q1_stb_d: float = Field(..., gt=0.0)
    p_avg_psia: float = Field(..., gt=0.0)
    k_md: float = Field(..., gt=0.0)
    h_ft: float = Field(..., gt=0.0)
    mu_cp: float = Field(..., gt=0.0)
    B_bbl_stb: float = Field(..., gt=0.0)
    r_e_ft: float = Field(..., gt=0.0)
    r_w_ft: float = Field(..., gt=0.0)
    S: float = Field(0.0)
    p2_psia: float | None = Field(default=None, gt=0.0)
    q2_stb_d: float | None = Field(default=None, gt=0.0)

    @model_validator(mode="after")
    def _chk(self) -> "SwapCheckRequest":
        if self.r_e_ft <= self.r_w_ft:
            raise ValueError("r_e_ft must exceed r_w_ft")
        if self.p1_psia >= self.p_avg_psia:
            raise ValueError("p1_psia must be < p_avg_psia")
        if self.p2_psia is not None and self.p2_psia >= self.p_avg_psia:
            raise ValueError("p2_psia must be < p_avg_psia")
        if (self.p2_psia is None) == (self.q2_stb_d is None):
            # Both provided or both omitted: OK
            pass
        return self


class SwapCheckResponse(BaseModel):
    PI_stb_d_psi: float = Field(..., gt=0.0)
    q2_predicted_stb_d: float
    p2_predicted_psia: float
    observed_ratio_q: float | None = None
    observed_ratio_p: float | None = None
    consistent: bool
    diagnostic: str
