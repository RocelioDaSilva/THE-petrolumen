"""Pydantic v2 schemas for the gas-compressibility endpoint."""

from pydantic import BaseModel, Field, field_validator


class GasCompressibilityRequest(BaseModel):
    p_psia: float = Field(..., gt=0.0, description="Pressure, psia (>0)")
    T_F: float = Field(
        ..., gt=-459.67, description="Temperature, deg F (above abs zero)"
    )
    gas_sg: float = Field(
        ..., gt=0.0, lt=2.0, description="Gas specific gravity (air=1)"
    )
    z_at_p: float | None = Field(
        default=None, gt=0.0, description="Optional precomputed z(p)"
    )

    @field_validator("T_F")
    @classmethod
    def _temp_ok(cls, v: float) -> float:
        if v <= -459.67:
            raise ValueError("T_F must be above absolute zero")
        return v


class GasCompressibilityResponse(BaseModel):
    cg_psi_inv: float = Field(..., description="cg in psi^-1")
    z_at_p: float = Field(..., gt=0.0)
    dz_dp_psi_inv: float = Field(..., description="dz/dp in psi^-1")
