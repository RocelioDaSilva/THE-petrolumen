"""Pydantic v2 schemas for the anisotropy-weighted perm endpoint."""
from pydantic import BaseModel, Field


class LayerIn(BaseModel):
    kh_md: float = Field(..., gt=0.0)
    kv_md: float = Field(..., gt=0.0)
    h_ft: float = Field(..., gt=0.0)


class AnisotropyWeightedRequest(BaseModel):
    layers: list[LayerIn] = Field(..., min_length=1)


class AnisotropyWeightedResponse(BaseModel):
    kh_eff_md: float = Field(..., gt=0.0)
    kv_eff_md: float = Field(..., gt=0.0)
    kappa: float = Field(..., gt=0.0)
    total_h_ft: float = Field(..., gt=0.0)
    per_layer_kh_contribution: list[float]
    per_layer_kv_resistance: list[float]
