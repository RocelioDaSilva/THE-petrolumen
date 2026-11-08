"""Pydantic v2 schemas for the Guthrie-Greenberger endpoint."""
from pydantic import BaseModel, Field


class GuthrieGreenbergerRequest(BaseModel):
    k_md: float = Field(..., gt=0.0)
    Swi: float = Field(..., ge=0.0, lt=1.0)
    mu_o_cp: float = Field(..., gt=0.0)
    phi: float = Field(..., gt=0.0, lt=1.0)
    h_ft: float = Field(..., gt=0.0)


class GuthrieGreenbergerResponse(BaseModel):
    RF: float
    term_k: float
    term_Swi: float
    term_mu: float
    term_phi: float
    term_h: float
    out_of_physical_range: bool
