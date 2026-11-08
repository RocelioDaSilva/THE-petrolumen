"""Pydantic v2 schemas for the gas-viscosity endpoint."""

from pydantic import BaseModel, Field, model_validator


class GasViscosityRequest(BaseModel):
    p_psia: float = Field(..., gt=0.0, description="Pressure, psia (>0)")
    T_F: float = Field(
        ..., gt=-459.67, description="Temperature, deg F (above abs zero)"
    )
    z: float = Field(..., gt=0.0, description="Gas z-factor (>0)")
    Mw_g_mol: float | None = Field(
        default=None, gt=0.0,
        description="Gas molecular weight, g/mol (or provide gas_sg)"
    )
    gas_sg: float | None = Field(
        default=None, gt=0.0, lt=2.0,
        description="Gas specific gravity, air=1 (or provide Mw_g_mol)"
    )

    @model_validator(mode="after")
    def _exactly_one(self) -> "GasViscosityRequest":
        provided = [self.Mw_g_mol is not None, self.gas_sg is not None]
        if sum(provided) != 1:
            raise ValueError(
                "Provide exactly one of Mw_g_mol or gas_sg"
            )
        return self


class GasViscosityResponse(BaseModel):
    mu_cp: float = Field(..., gt=0.0, description="Gas viscosity, cp")
    rho_gcc: float = Field(..., ge=0.0, description="Gas density, g/cc")
    K: float = Field(..., gt=0.0, description="Eq. 1.25b K factor")
    X: float = Field(..., description="Eq. 1.25c X factor")
    Y: float = Field(..., description="Eq. 1.25d Y factor")
    in_validity_range: bool = Field(
        ...,
        description="True if p in [100,8000] psia and T in [100,340] deg F",
    )
