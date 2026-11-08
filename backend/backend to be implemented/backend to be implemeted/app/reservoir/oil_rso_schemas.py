"""Pydantic v2 schemas for the oil solution-GOR endpoint."""

from pydantic import BaseModel, Field, field_validator


class OilRsoRequest(BaseModel):
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

    @field_validator("T_F")
    @classmethod
    def _temp_ok(cls, v: float) -> float:
        if v <= -459.67:
            raise ValueError("T_F must be above absolute zero")
        return v


class OilRsoResponse(BaseModel):
    rso_scf_stb: float = Field(..., ge=0.0, description="Rso in SCF/STB")
    y_g: float = Field(..., description="Standing Yg intermediate")
    clamped: bool = Field(
        ..., description="True if p > pb (Rso reported at pb)"
    )
    in_validity_range: bool = Field(
        ...,
        description=(
            "True if pb, T, gas_sg, and oil_api all fall inside the book's "
            "stated validity envelope (p. 34)"
        ),
    )
