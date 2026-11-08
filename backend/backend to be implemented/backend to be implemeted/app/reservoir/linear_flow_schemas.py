"""Pydantic v2 schemas for the linear-flow endpoint."""

from typing import Literal
from pydantic import BaseModel, Field, model_validator


class LinearFlowRequest(BaseModel):
    form: Literal[
        "incompressible",
        "slightly_compressible",
        "gas_low_p",
        "gas_high_p",
    ]
    k: float = Field(..., gt=0.0, description="Permeability, md")
    Ac: float = Field(..., gt=0.0, description="Area, ft^2")
    L: float = Field(..., gt=0.0, description="Length, ft")
    p1: float = Field(..., gt=0.0, description="Upstream pressure, psia")
    p2: float = Field(..., gt=0.0, description="Downstream pressure, psia")
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
    def _regime(self) -> "LinearFlowRequest":
        if self.p1 <= self.p2:
            raise ValueError("p1 must exceed p2")
        if self.form == "incompressible":
            if self.mu is None or self.B is None:
                raise ValueError("mu and B required for incompressible")
        elif self.form == "slightly_compressible":
            if self.mu is None or self.c is None or self.pR is None:
                raise ValueError("mu, c, pR required for slightly_compressible")
        elif self.form == "gas_low_p":
            for name in ("T_sc", "p_sc", "T", "z", "mu"):
                if getattr(self, name) is None:
                    raise ValueError(f"{name} required for gas_low_p")
        elif self.form == "gas_high_p":
            for name in ("T_sc", "p_sc", "T", "mu_z_over_p"):
                if getattr(self, name) is None:
                    raise ValueError(f"{name} required for gas_high_p")
        return self


class LinearFlowResponse(BaseModel):
    q: float
    form: Literal[
        "incompressible",
        "slightly_compressible",
        "gas_low_p",
        "gas_high_p",
    ]
    q_units: Literal["STB/day", "SCF/day"]
