"""Pydantic v2 schemas for the above-Pb oil MB endpoint."""

from pydantic import BaseModel, Field, model_validator


class OilMBAbovePbRequest(BaseModel):
    Np_stb: float = Field(..., ge=0.0)
    Bt: float = Field(..., gt=0.0)
    Bti: float = Field(..., gt=0.0)
    Swi: float = Field(..., ge=0.0, lt=1.0)
    cw: float = Field(..., ge=0.0)
    cf: float = Field(..., ge=0.0)
    delta_p: float = Field(..., ge=0.0)
    We: float = Field(0.0, ge=0.0)
    Wp: float = Field(0.0, ge=0.0)
    Bw: float = Field(1.0, gt=0.0)
    co: float | None = Field(default=None, ge=0.0)
    So: float | None = Field(default=None, ge=0.0, lt=1.0)

    @model_validator(mode="after")
    def _checks(self) -> "OilMBAbovePbRequest":
        if self.Bt < self.Bti - 1e-12:
            raise ValueError(
                "Bt < Bti; reservoir is below bubble point"
            )
        if (self.co is None) != (self.So is None):
            raise ValueError("Provide both co and So, or neither")
        if self.co is not None and self.So is not None:
            if self.So + self.Swi > 1.0 + 1e-9:
                raise ValueError("So + Swi exceeds 1.0")
        return self


class OilMBAbovePbResponse(BaseModel):
    n_stb: float = Field(..., gt=0.0)
    ce_psi_inv: float | None = Field(default=None)
    compression_term_bbl_stb: float
    denom_bbl_stb: float
