"""Pydantic v2 schemas for the oil-Bo endpoint."""

from pydantic import BaseModel, Field, field_validator


class OilBoRequest(BaseModel):
    p_psia: float = Field(..., gt=0.0, description="Pressure, psia (>0)")
    pb_psia: float = Field(
        ..., gt=0.0, description="Bubble-point pressure, psia (>0)"
    )
    T_F: float = Field(
        ..., gt=-459.67, description="Temperature, deg F (above abs zero)"
    )
    gas_sg: float = Field(
        ..., gt=0.0, lt=2.0, description="Gas specific gravity, air=1"
    )
    oil_api: float = Field(
        ..., gt=-10.0, lt=100.0, description="Stock-tank oil gravity, deg API"
    )
    co_psi_inv: float | None = Field(
        default=None, gt=0.0,
        description="Optional oil compressibility override, psi^-1",
    )

    @field_validator("T_F")
    @classmethod
    def _temp_ok(cls, v: float) -> float:
        if v <= -459.67:
            raise ValueError("T_F must be above absolute zero")
        return v


class OilBoResponse(BaseModel):
    bo_bbl_stb: float = Field(..., gt=0.0, description="Bo, bbl/STB")
    f_term: float = Field(..., description="Standing F parameter")
    gamma_o: float = Field(..., gt=0.0, description="Oil specific gravity")
    clamped: bool = Field(
        ..., description="True if p > pb (Eq. 1.30 applied)"
    )
    in_validity_range: bool = Field(
        ...,
        description=(
            "True if pb, T, gas_sg, oil_api, and Bo are all inside the "
            "book's stated envelope (p. 36)"
        ),
    )
    co_used: float | None = Field(
        default=None,
        description="Oil compressibility used above pb, psi^-1 (None if p <= pb)",
    )
