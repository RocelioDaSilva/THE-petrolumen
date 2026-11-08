"""Pydantic v2 schemas for the bottom-water influx endpoint."""

from pydantic import BaseModel, Field, model_validator


class BWHistoryPoint(BaseModel):
    t_days: float = Field(..., ge=0.0)
    p_psia: float = Field(..., gt=0.0)


class BottomWaterRequest(BaseModel):
    k_md: float = Field(..., gt=0.0)
    phi: float = Field(..., gt=0.0, lt=1.0)
    mu_w_cp: float = Field(..., gt=0.0)
    ct_psi_inv: float = Field(..., gt=0.0)
    h_ft: float = Field(..., gt=0.0)
    r_R_ft: float = Field(..., gt=0.0)
    F_k: float = Field(..., gt=0.0, le=1.0)
    r_e_over_r_R: float = Field(..., gt=1.0)
    p_history: list[BWHistoryPoint] = Field(..., min_length=2)

    @model_validator(mode="after")
    def _monotone(self) -> "BottomWaterRequest":
        for i in range(1, len(self.p_history)):
            if self.p_history[i].t_days <= self.p_history[i-1].t_days:
                raise ValueError(
                    f"p_history times must increase at index {i}"
                )
        return self


class BottomWaterResponse(BaseModel):
    B_double_prime_bbl_psi: float = Field(..., gt=0.0)
    r_D_prime: float = Field(..., gt=1.0)
    z_D_prime: float = Field(..., gt=0.0)
    we_cumulative_bbl: float
    we_at_points_bbl: list[float]
    wed_per_step: list[float]
