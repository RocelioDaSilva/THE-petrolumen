from pydantic import BaseModel, Field


class TransientEiRequest(BaseModel):
    pi_psia: float = Field(..., gt=0.0)
    q_stb_d: float = Field(..., gt=0.0)
    mu_cp: float = Field(..., gt=0.0)
    B_bbl_stb: float = Field(..., gt=0.0)
    k_md: float = Field(..., gt=0.0)
    h_ft: float = Field(..., gt=0.0)
    phi: float = Field(..., gt=0.0, lt=1.0)
    ct_psi_inv: float = Field(..., gt=0.0)
    r_ft: float = Field(..., gt=0.0)
    t_hr: float = Field(..., gt=0.0)


class TransientEiResponse(BaseModel):
    p_psia: float
    dp_psi: float
    x_arg: float
    used_log_approx: bool
