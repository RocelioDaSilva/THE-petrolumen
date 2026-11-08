"""Pydantic v2 schemas for the below-Pb oil MB endpoint."""

from pydantic import BaseModel, Field, model_validator


class OilMBBelowPbRequest(BaseModel):
    Np_stb: float = Field(..., ge=0.0)
    Rp: float = Field(..., ge=0.0)
    Rsoi: float = Field(..., ge=0.0)
    Bt: float = Field(..., gt=0.0)
    Bti: float = Field(..., gt=0.0)
    Bg: float = Field(..., gt=0.0)
    Swi: float = Field(..., ge=0.0, lt=1.0)
    cw: float = Field(0.0, ge=0.0)
    cf: float = Field(0.0, ge=0.0)
    delta_p: float = Field(0.0, ge=0.0)
    We: float = Field(0.0, ge=0.0)
    Wp: float = Field(0.0, ge=0.0)
    Bw: float = Field(1.0, gt=0.0)

    @model_validator(mode="after")
    def _checks(self) -> "OilMBBelowPbRequest":
        if self.Bt < self.Bti - 1e-12:
            raise ValueError("Bt < Bti (oil FVF shrank)")
        return self


class OilMBBelowPbResponse(BaseModel):
    n_stb: float = Field(..., gt=0.0)
    rf_fraction: float = Field(..., ge=0.0, le=1.0)
    tp_coef: float = Field(..., gt=0.0)
    denom_bbl_stb: float = Field(..., gt=0.0)
