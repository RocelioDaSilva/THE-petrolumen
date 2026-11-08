"""Pydantic v2 schemas for the radial-flow endpoint."""

from typing import Literal
from pydantic import BaseModel, Field, model_validator


class RadialFlowRequest(BaseModel):
    form: Literal[
        "incompressible",
        "slightly_compressible",
        "gas_low_p",
        "gas_high_p",
    ]
    k: float = Field(..., gt=0.0)
    h: float = Field(..., gt=0.0)
    p_e: float = Field(..., gt=0.0)
    p_w: float = Field(..., gt=0.0)
    r_e: float = Field(..., gt=0.0)
    r_w: float = Field(..., gt=0.0)
    mu: float | None = Field(default=None, gt=0.0)
    B: float | None = Field(default=None, gt=0.0)
    c: float | None = Field(default=None, gt=0.0)
    pR: float | None = Field(default=None, gt=0.0)
    T_sc: float | None = Field(default=None, gt=0.0)
    p_sc: float | None = Field(default=None, gt=0.0)
    T: float | None = Field(default=None, gt=0.0)
    z: float | None = Field(default=None, gt=0.0)
    mu_z_over_p: float | None = Field(default=None, gt=0.0)

    @model_validator(mode="after")
    def _checks(self) -> "RadialFlowRequest":
        if self.p_e <= self.p_w:
            raise ValueError("p_e must exceed p_w")
        if self.r_e <= self.r_w:
            raise ValueError("r_e must exceed r_w")
        if self.form == "incompressible":
            if self.mu is None or self.B is None:
                raise ValueError("mu and B required")
        elif self.form == "slightly_compressible":
            if self.mu is None or self.c is None or self.pR is None:
                raise ValueError("mu, c, pR required")
        elif self.form == "gas_low_p":
            for name in ("T_sc", "p_sc", "T", "z", "mu"):
                if getattr(self, name) is None:
                    raise ValueError(f"{name} required")
        elif self.form == "gas_high_p":
            for name in ("T_sc", "p_sc", "T", "mu_z_over_p"):
                if getattr(self, name) is None:
                    raise ValueError(f"{name} required")
        return self


class RadialFlowResponse(BaseModel):
    q: float
    form: Literal[
        "incompressible",
        "slightly_compressible",
        "gas_low_p",
        "gas_high_p",
    ]
    ln_re_over_rw: float
    q_units: Literal["STB/day", "SCF/day"]
