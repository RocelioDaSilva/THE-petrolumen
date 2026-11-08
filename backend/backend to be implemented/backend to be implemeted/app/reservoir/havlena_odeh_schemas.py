"""Pydantic v2 schemas for the Havlena-Odeh endpoint."""

from pydantic import BaseModel, Field


class HavlenaOdehPoint(BaseModel):
    Np: float = Field(..., ge=0.0, description="Cumulative oil, STB")
    Rp: float = Field(..., ge=0.0, description="Cumulative GOR, SCF/STB")
    Wp: float = Field(..., ge=0.0, description="Cumulative water, STB")
    We: float = Field(..., ge=0.0, description="Water influx, bbl")
    Bw: float = Field(..., gt=0.0, description="Water FVF, bbl/STB")
    Bt: float = Field(..., gt=0.0, description="Two-phase FVF, bbl/STB")
    Bg: float = Field(..., gt=0.0, description="Gas FVF, bbl/SCF")
    delta_p: float = Field(..., ge=0.0, description="Pressure drop, psi")


class HavlenaOdehRequest(BaseModel):
    Bti: float = Field(..., gt=0.0, description="Initial Bt, bbl/STB")
    Bgi: float = Field(..., gt=0.0, description="Initial Bg, bbl/SCF")
    Rsoi: float = Field(..., ge=0.0, description="Initial Rso, SCF/STB")
    Swi: float = Field(..., ge=0.0, lt=1.0, description="Connate water frac")
    cw: float = Field(..., ge=0.0, description="Water compressibility, psi^-1")
    cf: float = Field(..., ge=0.0, description="Formation compressibility, psi^-1")
    m: float = Field(0.0, ge=0.0, description="Gas cap / oil zone ratio")
    points: list[HavlenaOdehPoint] = Field(
        ..., min_length=2, description="At least two observation points"
    )


class HavlenaOdehResponse(BaseModel):
    n_hat: float = Field(..., description="Through-origin slope = N, STB")
    intercept: float = Field(
        ..., description="Free-intercept fit intercept (should be ~0)"
    )
    r_squared: float = Field(..., description="R^2 of the through-origin fit")
    per_point_n: list[float] = Field(
        ..., description="Per-point N_i = F_i / X_i"
    )
    residuals: list[float] = Field(
        ..., description="F_i - N_hat*X_i per point"
    )
    f_values: list[float] = Field(..., description="F_i per point, bbl")
    x_values: list[float] = Field(
        ..., description="X_i per point (composite expansion)"
    )
