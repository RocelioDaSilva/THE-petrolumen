"""Pydantic v2 schemas for the pseudopressure endpoint."""
from pydantic import BaseModel, Field, model_validator


class MuZPointIn(BaseModel):
    p_psia: float = Field(..., gt=0.0)
    mu_cp: float = Field(..., gt=0.0)
    z: float = Field(..., gt=0.0)


class PseudopressureRequest(BaseModel):
    p_psia: float = Field(..., gt=0.0)
    mu_z_table: list[MuZPointIn] = Field(..., min_length=2)
    p_ref_psia: float = Field(14.7, gt=0.0)
    n_grid: int = Field(1000, ge=10)

    @model_validator(mode="after")
    def _monotone(self) -> "PseudopressureRequest":
        for i in range(1, len(self.mu_z_table)):
            if self.mu_z_table[i].p_psia <= self.mu_z_table[i-1].p_psia:
                raise ValueError(
                    f"mu_z_table pressures must increase at {i}"
                )
        return self


class PseudopressureResponse(BaseModel):
    p_psia: float
    m_p_psia2_cp: float
    p_ref_psia: float
    n_grid: int
    p_outside_table: bool
