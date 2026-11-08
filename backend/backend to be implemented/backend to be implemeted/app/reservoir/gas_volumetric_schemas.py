"""Pydantic v2 schemas for the gas-volumetric endpoint."""

from typing import Literal
from pydantic import BaseModel, Field, model_validator

Mechanism = Literal[
    "depletion", "partial_water_drive", "complete_water_drive"
]


class GasVolumetricRequest(BaseModel):
    phi_frac: float = Field(..., gt=0.0, lt=1.0, description="Porosity, frac")
    Swi: float = Field(..., ge=0.0, lt=1.0, description="Connate water, frac")
    Bgi: float = Field(..., gt=0.0, description="Initial Bg, cu ft/SCF")
    Bga: float = Field(
        ..., gt=0.0, description="Bg at abandonment, cu ft/SCF"
    )
    mechanism: Mechanism = Field(..., description="Recovery mechanism")
    Sgr: float | None = Field(
        default=None, ge=0.0, lt=1.0,
        description="Residual gas saturation (required for water drive)"
    )
    Vb_ac_ft: float | None = Field(
        default=None, gt=0.0, description="Bulk volume, ac-ft (optional)"
    )
    A_acres: float | None = Field(
        default=None, gt=0.0, description="Areal extent, acres (optional)"
    )
    h_ft: float | None = Field(
        default=None, gt=0.0, description="Net thickness, ft (optional)"
    )

    @model_validator(mode="after")
    def _cross_checks(self) -> "GasVolumetricRequest":
        if self.Bga <= self.Bgi:
            raise ValueError("Bga must exceed Bgi")
        if self.mechanism != "depletion":
            if self.Sgr is None:
                raise ValueError(
                    f"Sgr required for mechanism={self.mechanism!r}"
                )
            if self.Swi + self.Sgr >= 1.0:
                raise ValueError("Swi + Sgr must be < 1")
        if (self.Vb_ac_ft is None
                and (self.A_acres is None) != (self.h_ft is None)):
            raise ValueError(
                "Provide either Vb_ac_ft alone, or both A_acres and h_ft, "
                "or neither."
            )
        return self


class GasVolumetricResponse(BaseModel):
    g_unit_scf_per_acft: float = Field(..., gt=0.0)
    dg_unit_scf_per_acft: float = Field(..., ge=0.0)
    recovery_factor_pct: float = Field(..., ge=0.0, le=100.0)
    g_total_scf: float | None = Field(default=None)
    reserve_total_scf: float | None = Field(default=None)
    mechanism: Mechanism
