"""Pydantic v2 schemas for the PVT-combine endpoint."""

from typing import Literal
from pydantic import BaseModel, Field, model_validator


class PVTCombineRequest(BaseModel):
    p_psia: float = Field(..., gt=0.0)
    pb_psia: float = Field(..., gt=0.0)
    Bob: float = Field(..., gt=0.0)
    Bodb: float = Field(..., gt=0.0)
    Rsob: float = Field(..., ge=0.0)
    Rsodb: float = Field(..., ge=0.0)
    RV: float | None = Field(default=None, gt=0.0)
    Bod_current: float | None = Field(default=None, gt=0.0)
    Rsod_current: float | None = Field(default=None, ge=0.0)

    @model_validator(mode="after")
    def _regime_args(self) -> "PVTCombineRequest":
        if self.p_psia >= self.pb_psia:
            if self.RV is None:
                raise ValueError(
                    "RV required above bubble point"
                )
        else:
            if self.Bod_current is None or self.Rsod_current is None:
                raise ValueError(
                    "Bod_current and Rsod_current required below "
                    "bubble point"
                )
        return self


class PVTCombineResponse(BaseModel):
    bo_bbl_stb: float = Field(..., gt=0.0)
    rso_scf_stb: float = Field(..., ge=0.0)
    regime: Literal["above_pb", "below_pb"]
