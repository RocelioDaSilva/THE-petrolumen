"""Pydantic v2 schemas for the pseudosteady endpoint."""

from typing import Literal
from pydantic import BaseModel, Field, model_validator


class PseudosteadyRequest(BaseModel):
    mode: Literal["pwf", "area_from_slope", "re_from_area", "tpss"]
    # pwf mode
    pi_psia: float | None = Field(default=None, gt=0.0)
    q_stb_d: float | None = Field(default=None, gt=0.0)
    mu_cp: float | None = Field(default=None, gt=0.0)
    B_bbl_stb: float | None = Field(default=None, gt=0.0)
    k_md: float | None = Field(default=None, gt=0.0)
    h_ft: float | None = Field(default=None, gt=0.0)
    A_ft2: float | None = Field(default=None, gt=0.0)
    CA: float | None = Field(default=None, gt=0.0)
    rw_ft: float | None = Field(default=None, gt=0.0)
    t_hr: float | None = Field(default=None, ge=0.0)
    phi: float | None = Field(default=None, gt=0.0, lt=1.0)
    ct_psi_inv: float | None = Field(default=None, gt=0.0)
    # area_from_slope mode
    m_prime_psi_per_hr: float | None = Field(default=None)
    # tpss mode
    re_ft: float | None = Field(default=None, gt=0.0)

    @model_validator(mode="after")
    def _check(self) -> "PseudosteadyRequest":
        if self.mode == "pwf":
            for name in ("pi_psia", "q_stb_d", "mu_cp", "B_bbl_stb",
                         "k_md", "h_ft", "A_ft2", "CA", "rw_ft",
                         "t_hr", "phi", "ct_psi_inv"):
                if getattr(self, name) is None:
                    raise ValueError(f"{name} required for pwf mode")
        elif self.mode == "area_from_slope":
            for name in ("m_prime_psi_per_hr", "q_stb_d", "B_bbl_stb",
                         "h_ft", "phi", "ct_psi_inv"):
                if getattr(self, name) is None:
                    raise ValueError(
                        f"{name} required for area_from_slope mode"
                    )
            if self.m_prime_psi_per_hr is not None and \
               self.m_prime_psi_per_hr >= 0.0:
                raise ValueError(
                    "m_prime_psi_per_hr must be < 0 for production"
                )
        elif self.mode == "re_from_area":
            if self.A_ft2 is None:
                raise ValueError("A_ft2 required for re_from_area mode")
        else:  # tpss
            for name in ("phi", "mu_cp", "ct_psi_inv", "re_ft", "k_md"):
                if getattr(self, name) is None:
                    raise ValueError(f"{name} required for tpss mode")
        return self


class PseudosteadyResponse(BaseModel):
    mode: Literal["pwf", "area_from_slope", "re_from_area", "tpss"]
    pwf_psia: float | None = None
    log_term_psi: float | None = None
    time_term_psi: float | None = None
    area_ft2: float | None = None
    r_e_ft: float | None = None
    t_pss_hr: float | None = None
