"""Pydantic v2 schemas for the Craze-Buckley Sor endpoint."""
from pydantic import BaseModel, Field


class CrazeBuckleyRequest(BaseModel):
    mu_o_cp: float = Field(..., gt=0.0)
    k_md: float = Field(..., gt=0.0)


class CrazeBuckleyResponse(BaseModel):
    Sor: float = Field(..., ge=0.0, le=1.0)
    Sor_pct: float = Field(..., ge=0.0, le=100.0)
    base_pct: float
    adj_pct: float
    out_of_table_range: bool
