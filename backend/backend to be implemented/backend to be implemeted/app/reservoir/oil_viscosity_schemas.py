"""Pydantic v2 schemas for the oil-viscosity endpoint."""

from typing import Literal
from pydantic import BaseModel, Field, field_validator


class OilViscosityRequest(BaseModel):
    p_psia: float = Field(..., gt=0.0, description="Pressure, psia (>0)")
    pb_psia: float = Field(
        ..., gt=0.0, description="Bubble-point pressure, psia (>0)"
    )
    T_F: float = Field(
        ..., gt=0.0,
        description="Temperature, deg F (>0 to keep log10(T) defined)",
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
        if v <= 0.0:
            raise ValueError(
                "T_F must be > 0 deg F for log10(T) in Eq. 1.34"
            )
        return v


class OilViscosityResponse(BaseModel):
    mu_cp: float = Field(..., gt=0.0, description="Live-oil viscosity, cp")
    mu_od_cp: float = Field(..., gt=0.0, description="Dead-oil viscosity, cp")
    mu_ob_cp: float = Field(
        ..., gt=0.0, description="Live-oil viscosity at pb, cp"
    )
    A: float = Field(..., gt=0.0, description="Eq. 1.35 A factor")
    B: float = Field(..., description="Eq. 1.35 B exponent")
    m: float | None = Field(
        default=None, description="Eq. 1.36 m exponent (None if p <= pb)"
    )
    formulation: Literal["beggs_robinson", "vasquez_beggs"] = Field(
        ..., description="Which live-oil form was used"
    )
    in_validity_range: bool = Field(
        ...,
        description=(
            "True if all inputs inside the active formulation's envelope "
            "(book pp. 41-42)"
        ),
    )
