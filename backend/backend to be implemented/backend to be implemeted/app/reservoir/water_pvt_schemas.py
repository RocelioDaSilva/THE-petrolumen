"""Pydantic v2 schemas for the water-PVT endpoint."""

from pydantic import BaseModel, Field, field_validator


class WaterPVTRequest(BaseModel):
    p_psia: float = Field(..., gt=0.0, description="Pressure, psia (>0)")
    T_F: float = Field(
        ..., gt=0.0,
        description="Temperature, deg F (>0 for T^-0.285854 in Eq. 1.38)",
    )
    salinity_pct: float = Field(
        ..., gt=0.0, lt=40.0, description="Salinity, % by weight solids"
    )
    c_nacl_g_l: float | None = Field(
        default=None, ge=0.0, le=200.0,
        description="Optional NaCl concentration, g/L (defaults to 10*pct)",
    )

    @field_validator("T_F")
    @classmethod
    def _temp_ok(cls, v: float) -> float:
        if v <= 0.0:
            raise ValueError(
                "T_F must be > 0 deg F for T^-0.285854 in Eq. 1.38"
            )
        return v


class WaterPVTResponse(BaseModel):
    bw_bbl_stb: float = Field(..., gt=0.0, description="Bw, bbl/STB")
    rswp_scf_stb: float = Field(..., ge=0.0, description="Rswp, SCF/STB")
    rsw_scf_stb: float = Field(..., ge=0.0, description="Rsw, SCF/STB")
    cw_psi_inv: float = Field(..., gt=0.0, description="cw, psi^-1")
    mu_w_cp: float = Field(..., gt=0.0, description="mu_w, cp")
    bw_in_validity: bool
    rsw_in_validity: bool
    cw_in_validity: bool
    mu_w_in_validity: bool
