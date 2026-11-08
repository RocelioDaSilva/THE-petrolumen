"""Pydantic v2 schemas for the gas-condensate initial-in-place endpoint."""

from pydantic import BaseModel, Field


class GCInitialRateRequest(BaseModel):
    pi_psia: float = Field(..., gt=0.0)
    T_F: float = Field(..., gt=-459.67)
    phi_frac: float = Field(..., gt=0.0, lt=1.0)
    Swi_frac: float = Field(..., ge=0.0, lt=1.0)
    oil_rate_stb_d: float = Field(..., gt=0.0)
    gas_sep_rate_scf_d: float = Field(..., gt=0.0)
    gas_sep_sg: float = Field(..., gt=0.0, lt=2.0)
    gas_tank_rate_scf_d: float = Field(0.0, ge=0.0)
    gas_tank_sg: float = Field(..., gt=0.0, lt=2.0)
    oil_api: float = Field(..., gt=8.811, lt=100.0)
    z_at_pi: float = Field(..., gt=0.0)


class GCInitialRateResponse(BaseModel):
    gamma_o: float = Field(..., gt=0.0, lt=1.008)
    mw_o: float = Field(..., gt=0.0)
    r1_sep_scf_stb: float = Field(..., ge=0.0)
    r3_tank_scf_stb: float = Field(..., ge=0.0)
    gamma_w: float = Field(..., gt=0.0, lt=2.0)
    f_s_gas_frac: float = Field(..., gt=0.0, lt=1.0)
    g_unit_mmscf_per_acft: float = Field(..., gt=0.0)
    g_gas_unit_mmscf_per_acft: float = Field(..., gt=0.0)
    n_oil_unit_stb_per_acft: float = Field(..., gt=0.0)
    in_validity: bool
