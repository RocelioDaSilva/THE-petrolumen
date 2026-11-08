"""Pydantic v2 schemas for the geopressured-p/z endpoint."""

from pydantic import BaseModel, Field


class GeopressuredPZPoint(BaseModel):
    p_psia: float = Field(..., gt=0.0, description="Pressure, psia")
    Gp_scf: float = Field(..., ge=0.0, description="Cumulative gas, SCF")
    z: float = Field(..., gt=0.0, description="Gas z-factor")


class GeopressuredPZRequest(BaseModel):
    points: list[GeopressuredPZPoint] = Field(
        ..., min_length=3,
        description="At least three survey points",
    )
    pi_psia: float | None = Field(
        default=None, gt=0.0,
        description="Optional initial pressure (default: first point)",
    )
    zi: float | None = Field(
        default=None, gt=0.0,
        description="Optional initial z (default: first point)",
    )


class GeopressuredPZResponse(BaseModel):
    g_initial_scf: float = Field(..., gt=0.0, description="G, SCF")
    c_prime_psi_inv: float = Field(
        ..., description="Bernard C' constant, psi^-1"
    )
    a_primes: list[float] = Field(..., description="A' per point")
    b_primes: list[float] = Field(..., description="B' per point")
    residuals: list[float] = Field(..., description="p/z residuals")
    likely_normal: bool = Field(
        ..., description="True if C' ~ 0 (use Feature 12 instead)"
    )
    late_time_diverge: bool = Field(
        ...,
        description="True if 1 - C'*dp approaches zero at some point",
    )
