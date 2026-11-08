"""Pydantic v2 schemas for the oil-material-balance endpoint."""

from pydantic import BaseModel, Field, model_validator


class OilMaterialBalanceRequest(BaseModel):
    Np: float = Field(..., ge=0.0, description="Cumulative oil, STB")
    Rp: float = Field(..., ge=0.0, description="Cumulative GOR, SCF/STB")
    Wp: float = Field(..., ge=0.0, description="Cumulative water, STB")
    Bt: float = Field(..., gt=0.0, description="Two-phase FVF at p, bbl/STB")
    Bti: float = Field(..., gt=0.0, description="Two-phase FVF at pi, bbl/STB")
    Bg: float = Field(..., gt=0.0, description="Gas FVF at p, bbl/SCF")
    Rsoi: float = Field(..., ge=0.0, description="Initial GOR, SCF/STB")
    m: float = Field(0.0, ge=0.0, description="Gas cap / oil zone ratio")
    Bgi: float | None = Field(
        default=None, gt=0.0,
        description="Initial gas FVF, bbl/SCF (required iff m>0)"
    )
    We: float = Field(0.0, ge=0.0, description="Water influx, bbl")
    Bw: float = Field(1.0, gt=0.0, description="Water FVF, bbl/STB")
    Swi: float = Field(0.0, ge=0.0, lt=1.0, description="Connate water frac")
    cw: float = Field(0.0, ge=0.0, description="Water compressibility, psi^-1")
    cf: float = Field(0.0, ge=0.0, description="Formation compressibility, psi^-1")
    delta_p: float = Field(0.0, ge=0.0, description="Pressure drop pi-p, psi")

    @model_validator(mode="after")
    def _bgi_required(self) -> "OilMaterialBalanceRequest":
        if self.m > 0.0 and (self.Bgi is None or self.Bgi <= 0.0):
            raise ValueError("Bgi must be provided and > 0 when m > 0")
        return self


class OilMaterialBalanceResponse(BaseModel):
    n_estimated: float = Field(..., description="N, STB")
    ddi: float = Field(..., description="Depletion drive index")
    sdi: float = Field(..., description="Segregation (gas-cap) index")
    wdi: float = Field(..., description="Water-drive index")
    index_sum: float = Field(
        ..., description="DDI + SDI + WDI (should be ~1 for comp-term=0)"
    )
    rhs_hc_bbl: float = Field(..., description="Hydrocarbon production term, bbl")
    net_water_influx_bbl: float = Field(
        ..., description="We - Bw*Wp, bbl"
    )
    expansion_oil_bbl: float = Field(..., description="Bt - Bti")
    expansion_gas_bbl: float = Field(..., description="m*Bti/Bgi*(Bg - Bgi)")
    expansion_water_bbl: float = Field(
        ..., description="(1+m)*Bti*[(cw*Swi+cf)/(1-Swi)]*delta_p"
    )
    denom_bbl_stb: float = Field(..., description="Sum of expansion terms")
