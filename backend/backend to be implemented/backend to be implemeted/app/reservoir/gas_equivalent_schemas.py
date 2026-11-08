"""Pydantic v2 schemas for the gas-equivalent endpoint."""

from pydantic import BaseModel, Field, model_validator


class GasEquivalentRequest(BaseModel):
    Np_stb: float = Field(..., ge=0.0, description="Condensate, STB")
    gamma_o: float | None = Field(
        default=None, gt=0.0, lt=1.008,
        description="Stock-tank oil specific gravity (water=1)",
    )
    M_wo: float | None = Field(
        default=None, gt=0.0,
        description="Stock-tank oil molecular weight, lbm/lbmol",
    )
    oil_api: float | None = Field(
        default=None, gt=8.811, lt=100.0,
        description="Stock-tank oil gravity, deg API",
    )
    Wp_water_bbl: float = Field(
        0.0, ge=0.0, description="Produced water, bbl"
    )
    Gp_surf_scf: float = Field(
        0.0, ge=0.0, description="Separator + stock-tank gas, SCF"
    )

    @model_validator(mode="after")
    def _at_least_one_identity(self) -> "GasEquivalentRequest":
        if (self.gamma_o is None
                and self.M_wo is None
                and self.oil_api is None):
            raise ValueError(
                "Provide at least one of gamma_o, M_wo, oil_api"
            )
        return self


class GasEquivalentResponse(BaseModel):
    ge_scf_per_bbl: float = Field(..., gt=0.0, description="GE, SCF/bbl")
    ge_water_scf_per_bbl: float = Field(
        ..., gt=0.0, description="GE_w, SCF/bbl (7390 per book)"
    )
    gp_total_scf: float = Field(..., ge=0.0, description="Total Gp, SCF")
    gw_total_scf: float = Field(
        ..., ge=0.0, description="Water gas-equivalent total, SCF"
    )
    gamma_o: float = Field(..., gt=0.0, lt=1.008)
    mw_o: float = Field(..., gt=0.0)
    in_validity: bool = Field(
        ..., description="True if oil_api within 30-70 deg API (typical)"
    )
