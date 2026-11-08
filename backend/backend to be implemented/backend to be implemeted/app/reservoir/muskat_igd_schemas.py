from pydantic import BaseModel, Field, model_validator


class MuskatPVTIn(BaseModel):
    p_psia: float = Field(..., gt=0.0)
    Bo: float = Field(..., gt=0.0)
    Bg: float = Field(..., gt=0.0)
    Rso: float = Field(..., ge=0.0)
    mu_o: float = Field(..., gt=0.0)
    mu_g: float = Field(..., gt=0.0)


class RelPermIn(BaseModel):
    SL: float = Field(..., ge=0.0, le=1.0)
    kg_ko: float = Field(..., ge=0.0)


class MuskatRequest(BaseModel):
    N_stb: float = Field(..., gt=0.0)
    Swi: float = Field(..., ge=0.0, lt=1.0)
    pvt: list[MuskatPVTIn] = Field(..., min_length=2)
    rel_perm: list[RelPermIn] = Field(..., min_length=2)

    @model_validator(mode="after")
    def _checks(self):
        for i in range(1, len(self.pvt)):
            if self.pvt[i].p_psia >= self.pvt[i-1].p_psia:
                raise ValueError("pvt pressures must decrease")
        return self


class MuskatRowOut(BaseModel):
    p_psia: float
    So: float
    Np_stb: float
    dSo_dp: float


class MuskatResponse(BaseModel):
    N_stb: float
    rows: list[MuskatRowOut]
