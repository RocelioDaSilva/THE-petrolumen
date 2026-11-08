"""Pydantic v2 schemas for the history-match endpoint."""

from pydantic import BaseModel, Field, model_validator


class HistoryPointIn(BaseModel):
    t_days: float = Field(..., ge=0.0)
    p_obs_psia: float = Field(..., gt=0.0)
    Np_obs_stb: float = Field(..., ge=0.0)
    Gp_obs_scf: float = Field(..., ge=0.0)
    pwf_psia: float = Field(..., gt=0.0)


class PVTCurvePointIn(BaseModel):
    p_psia: float = Field(..., gt=0.0)
    Bo_bbl_stb: float = Field(..., gt=0.0)
    Bt_bbl_stb: float = Field(..., gt=0.0)
    Bg_bbl_scf: float = Field(..., gt=0.0)
    Rso_scf_stb: float = Field(..., ge=0.0)


class HistoryMatchRequest(BaseModel):
    obs: list[HistoryPointIn] = Field(..., min_length=4)
    pvt: list[PVTCurvePointIn] = Field(..., min_length=2)
    We_hat_bbl: list[float] = Field(..., min_length=1)
    Wp_bbl: list[float] = Field(..., min_length=1)
    Swi: float = Field(..., ge=0.0, lt=1.0)
    cw_psi_inv: float = Field(0.0, ge=0.0)
    cf_psi_inv: float = Field(0.0, ge=0.0)
    N_guess_stb: float = Field(..., gt=0.0)
    J_guess_stb_d_psi: float = Field(..., gt=0.0)
    f_W_guess: float = Field(1.0, ge=0.0)
    sigma_p_psi: float | None = Field(default=None, gt=0.0)

    @model_validator(mode="after")
    def _checks(self) -> "HistoryMatchRequest":
        if len(self.We_hat_bbl) != len(self.obs):
            raise ValueError(
                "We_hat_bbl length must equal obs length"
            )
        if len(self.Wp_bbl) != len(self.obs):
            raise ValueError("Wp_bbl length must equal obs length")
        for i in range(1, len(self.obs)):
            if self.obs[i].t_days <= self.obs[i-1].t_days:
                raise ValueError(
                    f"obs times must strictly increase at index {i}"
                )
        return self


class HistoryMatchResponse(BaseModel):
    N_stb: float = Field(..., gt=0.0)
    J_stb_d_psi: float = Field(..., gt=0.0)
    f_W: float = Field(..., ge=0.0)
    rmse_psi: float = Field(..., ge=0.0)
    chi2_per_dof: float = Field(..., ge=0.0)
    n_iter: int = Field(..., ge=0)
    jacobian_condition: float = Field(..., gt=0.0)
    status: int
    message: str
    p_model_psia: list[float]
    residuals_psi: list[float]
