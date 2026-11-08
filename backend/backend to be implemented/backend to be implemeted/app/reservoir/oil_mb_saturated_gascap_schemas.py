"""Pydantic v2 schemas for the saturated-oil MB endpoint."""

from pydantic import BaseModel, Field, model_validator


class SaturatedOilMBRequest(BaseModel):
    Np_stb: float = Field(..., ge=0.0)
    Rp: float = Field(..., ge=0.0)
    Bt: float = Field(..., gt=0.0, description="Two-phase FVF, bbl/STB")
    Bti: float = Field(..., gt=0.0, description="Initial Bt, bbl/STB")
    Bg: float = Field(..., gt=0.0, description="Gas FVF, bbl/SCF")
    Rsoi: float = Field(..., ge=0.0)
    m: float = Field(0.0, ge=0.0, description="Gas cap / oil zone ratio")
    Bgi: float | None = Field(default=None, gt=0.0, description="Initial Bg, bbl/SCF")
    We: float = Field(0.0, ge=0.0)
    Wp: float = Field(0.0, ge=0.0)
    Bw: float = Field(1.0, gt=0.0)
    Swi: float | None = Field(default=None, ge=0.0, lt=1.0)
    cw: float = Field(0.0, ge=0.0)
    cf: float = Field(0.0, ge=0.0)
    delta_p: float = Field(0.0, ge=0.0)

    @model_validator(mode="after")
    def _bg_required(self) -> "SaturatedOilMBRequest":
        if self.m > 0.0 and (self.Bgi is None or self.Bgi <= 0.0):
            raise ValueError("Bgi must be provided and > 0 when m > 0")
        return self


class SaturatedOilMBResponse(BaseModel):
    n_stb: float = Field(..., gt=0.0)
    expansion_oil: float
    expansion_gas: float
    expansion_comp: float
    rhs_hc_bbl: float
    net_water_bbl: float
    denom_bbl_stb: float
