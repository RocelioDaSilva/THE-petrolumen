"""Pydantic v2 schemas for the Havlena-Odeh gas-cap endpoint."""
from pydantic import BaseModel, Field


class HOGC_PointIn(BaseModel):
    Np: float = Field(..., ge=0.0)
    Rp: float = Field(..., ge=0.0)
    Wp: float = Field(..., ge=0.0)
    We: float = Field(..., ge=0.0)
    Bw: float = Field(..., gt=0.0)
    Bt: float = Field(..., gt=0.0)
    Bg: float = Field(..., gt=0.0)


class HOGC_Request(BaseModel):
    points: list[HOGC_PointIn] = Field(..., min_length=2)
    Bti: float = Field(..., gt=0.0)
    Bgi: float = Field(..., gt=0.0)
    Rsoi: float = Field(..., ge=0.0)
    m: float = Field(..., ge=0.0)


class HOGC_Response(BaseModel):
    n_hat: float = Field(..., gt=0.0)
    free_slope: float
    free_intercept: float
    r_squared: float
    slope_diagnostic_ok: bool
    per_point_n: list[float]
    residuals: list[float]
    f_prime: list[float]
    x_values: list[float]
