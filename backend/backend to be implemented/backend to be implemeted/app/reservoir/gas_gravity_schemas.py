"""Pydantic v2 schemas for the gas-gravity endpoint."""

from typing import Literal
from pydantic import BaseModel, Field, model_validator


class GasGravityRequest(BaseModel):
    mode: Literal["fractional_flow", "frontal_advance"]
    # fractional-flow inputs
    Sg: float | None = Field(default=None, ge=0.0, lt=1.0)
    So: float | None = Field(default=None, gt=0.0, le=1.0)
    k_ro: float | None = Field(default=None, ge=0.0)
    k_rg: float | None = Field(default=None, ge=0.0)
    mu_o: float = Field(..., gt=0.0)
    mu_g: float = Field(..., gt=0.0)
    k_md: float = Field(..., gt=0.0)
    Ac_ft2: float = Field(..., gt=0.0)
    qt_bbl_d: float = Field(..., gt=0.0)
    alpha_deg: float = Field(..., gt=-90.0, lt=90.0)
    rho_o_lb_ft3: float = Field(..., gt=0.0)
    rho_g_lb_ft3: float = Field(..., ge=0.0)
    # frontal-advance inputs
    Sg_list: list[float] | None = Field(default=None)
    fg_list: list[float] | None = Field(default=None)
    times_days: list[float] | None = Field(default=None)
    phi: float | None = Field(default=None, gt=0.0, lt=1.0)

    @model_validator(mode="after")
    def _check(self) -> "GasGravityRequest":
        if self.rho_o_lb_ft3 <= self.rho_g_lb_ft3:
            raise ValueError("rho_o must exceed rho_g")
        if self.mode == "fractional_flow":
            for name in ("Sg", "So", "k_ro", "k_rg"):
                if getattr(self, name) is None:
                    raise ValueError(
                        f"{name} required for fractional_flow"
                    )
            if self.Sg is not None and self.Sg > 0.0 and \
               self.k_rg == 0.0:
                raise ValueError("k_rg must be > 0 when Sg > 0")
        else:
            for name in ("Sg_list", "fg_list", "times_days", "phi"):
                if getattr(self, name) is None:
                    raise ValueError(
                        f"{name} required for frontal_advance"
                    )
            if self.Sg_list is not None and self.fg_list is not None:
                if len(self.Sg_list) != len(self.fg_list):
                    raise ValueError("Sg_list and fg_list lengths differ")
                if len(self.Sg_list) < 3:
                    raise ValueError("at least 3 Sg points")
                for i in range(1, len(self.Sg_list)):
                    if self.Sg_list[i] <= self.Sg_list[i-1]:
                        raise ValueError(
                            f"Sg_list not strictly increasing at {i}"
                        )
        return self


class GasGravityResponse(BaseModel):
    mode: Literal["fractional_flow", "frontal_advance"]
    f_g: float | None = None
    lambda_gravity: float | None = None
    denom_visc: float | None = None
    counter_current: bool | None = None
    x_by_Sg_by_time: list[list[float]] = Field(default_factory=list)
    times_days: list[float] = Field(default_factory=list)
