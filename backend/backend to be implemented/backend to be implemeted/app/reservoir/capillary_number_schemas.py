"""Pydantic v2 schemas for the capillary-number endpoint."""

from typing import Literal
from pydantic import BaseModel, Field


class CapillaryNumberRequest(BaseModel):
    k_o_md: float = Field(..., gt=0.0)
    delta_p_psi: float = Field(..., gt=0.0)
    L_ft: float = Field(..., gt=0.0)
    phi: float = Field(..., gt=0.0, lt=1.0)
    sigma_ow_dyn_cm: float = Field(..., gt=0.0)
    Sor_before: float | None = Field(default=None, ge=0.0, lt=1.0)


class CapillaryNumberResponse(BaseModel):
    N_w: float = Field(..., gt=0.0)
    gradient_psi_ft: float = Field(..., gt=0.0)
    sor_reduction_fraction: float = Field(..., gt=0.0, le=1.0)
    sor_after: float | None = None
    category: Literal["below_threshold", "transition", "aggressive_EOR"]
