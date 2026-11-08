"""Pydantic v2 schemas for the Fetkovich influx endpoint."""

from typing import Literal
from pydantic import BaseModel, Field, model_validator

Boundary = Literal["no_flow", "constant_pressure"]


class FetkovichPoint(BaseModel):
    t_days: float = Field(..., ge=0.0)
    p_R_psia: float = Field(..., gt=0.0)


class FetkovichRequest(BaseModel):
    mode: Literal["productivity_index", "cumulative"]
    # productivity index inputs
    k_md: float | None = Field(default=None, gt=0.0)
    h_ft: float | None = Field(default=None, gt=0.0)
    mu_cp: float | None = Field(default=None, gt=0.0)
    r_e_ft: float | None = Field(default=None, gt=0.0)
    r_R_ft: float | None = Field(default=None, gt=0.0)
    theta_deg: float | None = Field(default=None, gt=0.0, le=360.0)
    outer_boundary: Boundary | None = Field(default=None)
    # cumulative inputs
    W_ei_bbl: float | None = Field(default=None, gt=0.0)
    p_i_psia: float | None = Field(default=None, gt=0.0)
    J_bpd_psi: float | None = Field(default=None, gt=0.0)
    p_history: list[FetkovichPoint] | None = Field(default=None)

    @model_validator(mode="after")
    def _check(self) -> "FetkovichRequest":
        if self.mode == "productivity_index":
            for name in ("k_md", "h_ft", "mu_cp", "r_e_ft",
                         "r_R_ft", "theta_deg", "outer_boundary"):
                if getattr(self, name) is None:
                    raise ValueError(
                        f"{name} required for productivity_index mode"
                    )
            if (self.r_e_ft is not None and self.r_R_ft is not None
                    and self.r_e_ft <= self.r_R_ft):
                raise ValueError("r_e_ft must exceed r_R_ft")
        else:
            for name in ("W_ei_bbl", "p_i_psia", "J_bpd_psi", "p_history"):
                if getattr(self, name) is None:
                    raise ValueError(
                        f"{name} required for cumulative mode"
                    )
            if self.p_history is not None:
                if len(self.p_history) < 2:
                    raise ValueError("p_history must have at least 2 points")
                for i in range(1, len(self.p_history)):
                    if (self.p_history[i].t_days
                            <= self.p_history[i-1].t_days):
                        raise ValueError(
                            f"p_history times must increase at index {i}"
                        )
                for i, pt in enumerate(self.p_history):
                    if self.p_i_psia is not None and pt.p_R_psia > self.p_i_psia:
                        raise ValueError(
                            f"p_history[{i}].p_R_psia exceeds p_i_psia"
                        )
        return self


class FetkovichResponse(BaseModel):
    J_bpd_psi: float | None = None
    we_cumulative_bbl: float = Field(..., ge=0.0)
    we_at_points_bbl: list[float]
    delta_we_per_step_bbl: list[float]
    pbar_per_step_psia: list[float]
