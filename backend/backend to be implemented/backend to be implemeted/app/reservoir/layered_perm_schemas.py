"""Pydantic v2 schemas for the layered-permeability endpoint."""

from typing import Literal
from pydantic import BaseModel, Field, model_validator


class LayerPermListRequest(BaseModel):
    mode: Literal["linear_series", "linear_parallel", "radial_parallel"]
    k_list: list[float] = Field(..., min_length=1)
    L_or_h_list: list[float] = Field(..., min_length=1)

    @model_validator(mode="after")
    def _checks(self) -> "LayerPermListRequest":
        for i, v in enumerate(self.k_list):
            if v <= 0.0:
                raise ValueError(f"k_list[{i}] must be > 0")
        for i, v in enumerate(self.L_or_h_list):
            if v <= 0.0:
                raise ValueError(f"L_or_h_list[{i}] must be > 0")
        if len(self.k_list) != len(self.L_or_h_list):
            raise ValueError("k_list and L_or_h_list must be same length")
        return self


class RadialSeriesRequest(BaseModel):
    k_e: float = Field(..., gt=0.0)
    k_a: float = Field(..., gt=0.0)
    r_e: float = Field(..., gt=0.0)
    r_a: float = Field(..., gt=0.0)
    r_w: float = Field(..., gt=0.0)

    @model_validator(mode="after")
    def _order(self) -> "RadialSeriesRequest":
        if not (self.r_e > self.r_a > self.r_w):
            raise ValueError("radial ordering r_e > r_a > r_w required")
        return self


class LayerPermResponse(BaseModel):
    k_avg_md: float = Field(..., gt=0.0)
    total_length_or_thickness: float = Field(..., gt=0.0)
    total_capacity_md_ft: float | None = None
