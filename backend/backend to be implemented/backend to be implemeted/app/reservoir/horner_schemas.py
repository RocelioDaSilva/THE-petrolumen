"""Pydantic v2 schemas for the Horner endpoint."""

from pydantic import BaseModel, Field


class HornerPoint(BaseModel):
    dt_hr: float = Field(..., gt=0.0, description="Shut-in time, hr")
    pws_psia: float = Field(..., gt=0.0, description="Shut-in BHP, psia")


class HornerRequest(BaseModel):
    q_stb_d: float = Field(..., gt=0.0)
    mu_cp: float = Field(..., gt=0.0)
    B_bbl_stb: float = Field(..., gt=0.0)
    h_ft: float = Field(..., gt=0.0)
    phi: float = Field(..., gt=0.0, lt=1.0)
    ct_psi_inv: float = Field(..., gt=0.0)
    rw_ft: float = Field(..., gt=0.0)
    tp_hr: float = Field(..., gt=0.0)
    pwf_at_shutin_psia: float = Field(..., gt=0.0)
    horner_points: list[HornerPoint] = Field(..., min_length=2)


class HornerResponse(BaseModel):
    m_psi_per_cycle: float = Field(..., lt=0.0)
    p1hr_psia: float = Field(..., gt=0.0)
    k_md: float = Field(..., gt=0.0)
    skin: float
    p_star_psia: float = Field(..., gt=0.0)
    r_squared: float
