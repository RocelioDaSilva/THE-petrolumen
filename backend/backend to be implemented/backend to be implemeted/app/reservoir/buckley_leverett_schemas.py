"""Pydantic v2 schemas for the Buckley-Leverett endpoint."""

from typing import Literal
from pydantic import BaseModel, Field, model_validator


class BuckLeverettRequest(BaseModel):
    mode: Literal["single", "advance"]
    mu_w: float = Field(..., gt=0.0, description="Water viscosity, cp")
    mu_o: float = Field(..., gt=0.0, description="Oil viscosity, cp")
    a: float = Field(..., gt=0.0, description="Eq 9.3 intercept")
    b: float = Field(..., gt=0.0, description="Eq 9.3 slope, 1/fraction")
    Sw_list: list[float] = Field(..., min_length=1)
    qi_bbl_d: float | None = Field(default=None, gt=0.0)
    phi: float | None = Field(default=None, gt=0.0, lt=1.0)
    Ac_ft2: float | None = Field(default=None, gt=0.0)
    times_days: list[float] | None = Field(default=None)

    @model_validator(mode="after")
    def _check(self) -> "BuckLeverettRequest":
        for i, Sw in enumerate(self.Sw_list):
            if not (0.0 < Sw < 1.0):
                raise ValueError(f"Sw_list[{i}] must be in (0, 1)")
        if self.mode == "advance":
            if (self.qi_bbl_d is None or self.phi is None
                    or self.Ac_ft2 is None or self.times_days is None):
                raise ValueError(
                    "qi_bbl_d, phi, Ac_ft2, times_days required for "
                    "advance mode"
                )
            if len(self.times_days) == 0:
                raise ValueError("times_days must be non-empty")
            for i, t in enumerate(self.times_days):
                if t < 0.0:
                    raise ValueError(
                        f"times_days[{i}] must be >= 0"
                    )
        else:
            if len(self.Sw_list) != 1:
                raise ValueError("single mode requires exactly one Sw")
        return self


class FracFlowPointOut(BaseModel):
    Sw: float
    ko_over_kw: float
    fw: float
    dfw_dSw: float


class BuckLeverettResponse(BaseModel):
    mode: Literal["single", "advance"]
    points: list[FracFlowPointOut]
    x_by_Sw_by_time: list[list[float]]
    times_days: list[float]
