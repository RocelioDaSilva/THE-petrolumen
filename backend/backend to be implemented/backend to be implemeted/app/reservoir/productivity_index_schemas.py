"""Pydantic v2 schemas for the productivity-index endpoint."""

from typing import Literal
from pydantic import BaseModel, Field, model_validator


class PIRequest(BaseModel):
    mode: Literal["empirical", "theoretical", "ratio"]
    # Empirical
    q_stb_d: float | None = Field(default=None, ge=0.0)
    p_avg_psia: float | None = Field(default=None, gt=0.0)
    p_wf_psia: float | None = Field(default=None, gt=0.0)
    h_ft: float | None = Field(default=None, gt=0.0)
    injection: bool = Field(default=False)
    # Theoretical
    k_md: float | None = Field(default=None, gt=0.0)
    mu_cp: float | None = Field(default=None, gt=0.0)
    B_bbl_stb: float | None = Field(default=None, gt=0.0)
    r_e_ft: float | None = Field(default=None, gt=0.0)
    r_w_ft: float | None = Field(default=None, gt=0.0)
    S: float = Field(default=0.0)
    # Ratio
    J: float | None = Field(default=None, gt=0.0)
    J_std: float | None = Field(default=None, gt=0.0)

    @model_validator(mode="after")
    def _check(self) -> "PIRequest":
        if self.mode == "empirical":
            for name in ("q_stb_d", "p_avg_psia", "p_wf_psia"):
                if getattr(self, name) is None:
                    raise ValueError(f"{name} required for empirical")
        elif self.mode == "theoretical":
            for name in ("k_md", "h_ft", "mu_cp", "B_bbl_stb",
                         "r_e_ft", "r_w_ft"):
                if getattr(self, name) is None:
                    raise ValueError(f"{name} required for theoretical")
        else:
            for name in ("J", "J_std"):
                if getattr(self, name) is None:
                    raise ValueError(f"{name} required for ratio")
        return self


class PIResponse(BaseModel):
    J_stb_per_psi: float | None = None
    Js_stb_per_psi_ft: float | None = None
    injectivity_index: float | None = None
    productivity_ratio: float | None = None
