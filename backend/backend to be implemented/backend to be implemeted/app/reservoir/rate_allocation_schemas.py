from pydantic import BaseModel, Field, model_validator


class RateAllocBlockIn(BaseModel):
    k_md: float = Field(..., gt=0.0)
    h_ft: float = Field(..., gt=0.0)
    S: float = Field(0.0)
    mu_cp: float = Field(..., gt=0.0)
    B_bbl_stb: float = Field(..., gt=0.0)
    r_e_ft: float = Field(..., gt=0.0)
    r_w_ft: float = Field(..., gt=0.0)
    p_avg_psia: float = Field(4000.0, gt=0.0)

    @model_validator(mode="after")
    def _chk(self):
        if self.r_e_ft <= self.r_w_ft:
            raise ValueError("r_e_ft must exceed r_w_ft")
        return self


class RateAllocRequest(BaseModel):
    Q_stb_d: float = Field(..., gt=0.0)
    blocks: list[RateAllocBlockIn] = Field(..., min_length=2)


class RateAllocResponse(BaseModel):
    q_alloc_stb_d: list[float]
    p_w_psia: list[float]
    dp_kh_error_psi: float
    error_fraction: float
    classification: str
    recommendation: str
