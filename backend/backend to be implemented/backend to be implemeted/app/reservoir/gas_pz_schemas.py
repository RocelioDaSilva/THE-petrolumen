"""Pydantic v2 schemas for the gas p/z endpoint."""

from pydantic import BaseModel, Field


class GasPZPoint(BaseModel):
    p_psia: float = Field(..., gt=0.0, description="Pressure, psia")
    Gp_scf: float = Field(..., ge=0.0, description="Cumulative gas, SCF")
    z: float = Field(..., gt=0.0, description="Gas z-factor")


class GasPZRequest(BaseModel):
    points: list[GasPZPoint] = Field(
        ..., min_length=2, description="At least two survey points"
    )
    abandon_pz: float | None = Field(
        default=None, gt=0.0,
        description="Abandonment p/z, psia (optional)"
    )


class GasPZResponse(BaseModel):
    g_initial_scf: float = Field(..., gt=0.0, description="Initial G, SCF")
    slope: float = Field(..., lt=0.0, description="Fitted slope (must be < 0)")
    intercept: float = Field(..., gt=0.0, description="Fitted intercept (pi/zi)")
    r_squared: float = Field(..., description="R^2 of the linear fit")
    gp_at_abandonment_scf: float | None = Field(default=None)
    linearity_suspect: bool = Field(
        ..., description="True when R^2 < 0.90 (possible water drive)"
    )
    intercept_suspect: bool = Field(
        ..., description="True when intercept deviates >5% from first p/z"
    )
    predicted_pz: list[float] = Field(..., description="Fitted p/z values")
    predicted_gp: list[float] = Field(..., description="Gp values (same order)")
