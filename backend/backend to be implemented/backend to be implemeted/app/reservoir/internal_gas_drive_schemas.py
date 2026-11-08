"""Pydantic v2 schemas for the internal-gas-drive endpoint."""

from pydantic import BaseModel, Field, model_validator


class PVTPointIn(BaseModel):
    p_psia: float = Field(..., gt=0.0)
    Bo_bbl_stb: float = Field(..., gt=0.0)
    Bg_bbl_scf: float = Field(..., gt=0.0)
    Rso_scf_stb: float = Field(..., ge=0.0)
    mu_o_cp: float = Field(..., gt=0.0)
    mu_g_cp: float = Field(..., gt=0.0)


class RelPermPointIn(BaseModel):
    SL: float = Field(..., ge=0.0, le=1.0)
    kg_ko: float = Field(..., ge=0.0)


class InternalGasDriveRequest(BaseModel):
    N_stb: float = Field(..., gt=0.0)
    Swi: float = Field(..., ge=0.0, lt=1.0)
    pvt: list[PVTPointIn] = Field(..., min_length=2)
    rel_perm: list[RelPermPointIn] = Field(..., min_length=2)
    m: float = Field(0.0, ge=0.0)

    @model_validator(mode="after")
    def _checks(self) -> "InternalGasDriveRequest":
        for i in range(1, len(self.pvt)):
            if self.pvt[i].p_psia >= self.pvt[i-1].p_psia:
                raise ValueError(
                    f"pvt pressures must strictly decrease at index {i}"
                )
        for i in range(1, len(self.rel_perm)):
            if self.rel_perm[i].SL <= self.rel_perm[i-1].SL:
                raise ValueError(
                    f"rel_perm SL must strictly increase at index {i}"
                )
        return self


class TarnerRowOut(BaseModel):
    p_psia: float
    Np_stb: float
    Gp_scf: float
    R_scf_stb: float
    SL: float
    kg_over_ko: float
    n_iter: int
    converged: bool


class InternalGasDriveResponse(BaseModel):
    N_stb: float
    rows: list[TarnerRowOut]
    converged_all: bool
