from pydantic import BaseModel, Field, model_validator


class MuZIn(BaseModel):
    p_psia: float = Field(..., gt=0.0)
    mu_cp: float = Field(..., gt=0.0)
    z: float = Field(..., gt=0.0)


class GasDelivRequest(BaseModel):
    pi_psia: float = Field(..., gt=0.0)
    q_scf_d: float = Field(..., gt=0.0)
    T_F: float = Field(..., gt=-459.67)
    k_md: float = Field(..., gt=0.0)
    h_ft: float = Field(..., gt=0.0)
    phi: float = Field(..., gt=0.0, lt=1.0)
    ct_psi_inv: float = Field(..., gt=0.0)
    rw_ft: float = Field(..., gt=0.0)
    t_hr: float = Field(..., gt=0.0)
    mu_z_table: list[MuZIn] = Field(..., min_length=2)

    @model_validator(mode="after")
    def _mono(self):
        for i in range(1, len(self.mu_z_table)):
            if self.mu_z_table[i].p_psia <= self.mu_z_table[i-1].p_psia:
                raise ValueError("mu_z_table must increase in p")
        return self


class GasDelivResponse(BaseModel):
    m_pw: float
    pwf_psia: float
    m_pi: float
    dp_drawdown_psi: float
