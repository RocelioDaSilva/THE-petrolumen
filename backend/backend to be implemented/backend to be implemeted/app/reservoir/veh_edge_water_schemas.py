"""Pydantic v2 schemas for the vEH edge-water endpoint."""

from pydantic import BaseModel, Field, model_validator


class VehHistoryPoint(BaseModel):
    t_days: float = Field(..., ge=0.0)
    p_psia: float = Field(..., gt=0.0)


class VehRequest(BaseModel):
    k_md: float = Field(..., gt=0.0)
    phi: float = Field(..., gt=0.0, lt=1.0)
    mu_w_cp: float = Field(..., gt=0.0)
    ct_psi_inv: float = Field(..., gt=0.0)
    h_ft: float = Field(..., gt=0.0)
    r_R_ft: float = Field(..., gt=0.0)
    theta_deg: float = Field(..., gt=0.0, le=360.0)
    p_history: list[VehHistoryPoint] = Field(..., min_length=2)
    r_e_over_r_R: float | None = Field(default=None, ge=1.0)

    @model_validator(mode="after")
    def _monotone(self) -> "VehRequest":
        for i in range(1, len(self.p_history)):
            if self.p_history[i].t_days <= self.p_history[i-1].t_days:
                raise ValueError(
                    f"p_history times must increase at index {i}"
                )
        return self


class VehResponse(BaseModel):
    B_prime_bbl_psi: float = Field(..., gt=0.0)
    we_cumulative_bbl: float
    we_at_points_bbl: list[float]
    delta_p_per_step_psi: list[float]
    t_D_per_step: list[float]
    wed_per_step: list[float]
