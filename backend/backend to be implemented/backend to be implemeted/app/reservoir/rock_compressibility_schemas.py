"""Pydantic v2 schemas for the formation-compressibility endpoint."""

from typing import Literal
from pydantic import BaseModel, Field, field_validator

RockType = Literal["sandstone", "limestone"]


class FormationCompressibilityRequest(BaseModel):
    phi: float = Field(
        ...,
        gt=0.0,
        lt=1.0,
        description="Porosity, fraction (dimensionless), 0 < phi < 1",
    )
    rock_type: RockType = Field(
        ...,
        description="Either 'sandstone' or 'limestone'",
    )
    strict: bool = Field(
        default=False,
        description="If True, enforce the book's stated validity range",
    )

    @field_validator("rock_type")
    @classmethod
    def _type_ok(cls, v: str) -> str:
        if v not in ("sandstone", "limestone"):
            raise ValueError("rock_type must be 'sandstone' or 'limestone'")
        return v


class FormationCompressibilityResponse(BaseModel):
    cf_psi_inv: float = Field(..., gt=0.0, description="cf in psi^-1")
    rock_type: RockType
    in_validity_range: bool = Field(
        ..., description="True if phi is within the book's stated range"
    )
