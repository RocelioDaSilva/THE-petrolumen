"""Pydantic v2 schemas for the oil-compressibility endpoint."""

from typing import Literal
from pydantic import BaseModel, Field, field_validator


class OilCompressibilityRequest(BaseModel):
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


class OilCompressibilityResponse(BaseModel):
    co_psi_inv: float = Field(..., gt=0.0, description="co, psi^-1")
    formulation: Literal["villena_lanzi", "vasquez_beggs"] = Field(
        ..., description="Which correlation was used"
    )
    rsob_scf_stb: float = Field(..., gt=0.0, description="Rso at pb")
    in_validity_range: bool = Field(
        ...,
        description=(
            "True if p, pb, T, Rsob, API, gas_sg all inside the "
            "book's stated envelope for the active formulation (p. 39)"
        ),
    )
