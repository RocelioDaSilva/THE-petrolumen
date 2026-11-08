"""Pydantic v2 schemas for the Schilthuis influx endpoint."""

from typing import Literal
from pydantic import BaseModel, Field, model_validator


class SchilthuisHistoryPoint(BaseModel):
    t_days: float = Field(..., ge=0.0)
    p_psia: float = Field(..., gt=0.0)


class SchilthuisRequest(BaseModel):
    mode: Literal["stabilized", "cumulative"]
    # stabilized inputs
    dNp_dt_stb_d: float | None = Field(default=None, ge=0.0)
    R_scf_stb: float | None = Field(default=None, ge=0.0)
    Rsoi_scf_stb: float | None = Field(default=None, ge=0.0)
    dWp_dt_stb_d: float | None = Field(default=None, ge=0.0)
    B_t_bbl_stb: float | None = Field(default=None, gt=0.0)
    B_g_bbl_scf: float | None = Field(default=None, gt=0.0)
    B_w_bbl_stb: float | None = Field(default=None, gt=0.0)
    pi_psia: float = Field(..., gt=0.0)
    ps_psia: float | None = Field(default=None, gt=0.0)
    # cumulative inputs
    k_prime: float | None = Field(default=None, gt=0.0)
    p_history: list[SchilthuisHistoryPoint] | None = Field(default=None)

    @model_validator(mode="after")
    def _check(self) -> "SchilthuisRequest":
        if self.mode == "stabilized":
            for name in ("dNp_dt_stb_d", "R_scf_stb", "Rsoi_scf_stb",
                         "dWp_dt_stb_d", "B_t_bbl_stb", "B_g_bbl_scf",
                         "B_w_bbl_stb", "ps_psia"):
                if getattr(self, name) is None:
                    raise ValueError(f"{name} required for stabilized mode")
            if self.ps_psia is not None and self.ps_psia >= self.pi_psia:
                raise ValueError("pi_psia must exceed ps_psia")
        else:
            if self.k_prime is None or self.p_history is None:
                raise ValueError("k_prime and p_history required for cumulative mode")
            if len(self.p_history) < 2:
                raise ValueError("p_history must have at least 2 points")
            for i in range(1, len(self.p_history)):
                if self.p_history[i].t_days <= self.p_history[i-1].t_days:
                    raise ValueError(
                        f"p_history times must increase at index {i}"
                    )
        return self


class SchilthuisResponse(BaseModel):
    k_prime: float = Field(..., gt=0.0)
    we_cumulative_bbl: float = Field(..., ge=0.0)
    we_at_points_bbl: list[float]
    daily_voidage_bbl: float | None = None
