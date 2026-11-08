"""Pydantic v2 schemas for the drawdown endpoint."""

from pydantic import BaseModel, Field


class DrawdownPoint(BaseModel):
    t_hr: float = Field(..., gt=0.0, description="Time, hr")
    pwf_psia: float = Field(..., gt=0.0, description="pwf, psia")


class DrawdownRequest(BaseModel):
    q_stb_d: float = Field(..., gt=0.0)
    mu_cp: float = Field(..., gt=0.0)
    B_bbl_stb: float = Field(..., gt=0.0)
    h_ft: float = Field(..., gt=0.0)
    phi: float = Field(..., gt=0.0, lt=1.0)
    ct_psi_inv: float = Field(..., gt=0.0)
    rw_ft: float = Field(..., gt=0.0)
    pi_psia: float = Field(..., gt=0.0)
    semilog_points: list[DrawdownPoint] = Field(..., min_length=2)
    pseudosteady_points: list[DrawdownPoint] | None = Field(default=None)


class DrawdownResponse(BaseModel):
    m_psi_per_cycle: float = Field(..., lt=0.0)
    p1hr_psia: float = Field(..., gt=0.0)
    k_md: float = Field(..., gt=0.0)
    skin: float
    r_squared_semilog: float
    drainage_area_ft2: float | None = None
    m_prime_psi_per_hr: float | None = None
    r_squared_cartesian: float | None = None
