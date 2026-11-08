from pydantic import BaseModel, Field, model_validator


class SchilthuisPVTIn(BaseModel):
    p_psia: float = Field(..., gt=0.0)
    Bo: float = Field(..., gt=0.0)
    Bg: float = Field(..., gt=0.0)
    Rso: float = Field(..., ge=0.0)
    mu_o: float = Field(..., gt=0.0)
    mu_g: float = Field(..., gt=0.0)


class RelPermIn2(BaseModel):
    SL: float = Field(..., ge=0.0, le=1.0)
    kg_ko: float = Field(..., ge=0.0)


class SchilthuisRequest(BaseModel):
    N_stb: float = Field(..., gt=0.0)
    Swi: float = Field(..., ge=0.0, lt=1.0)
    pvt: list[SchilthuisPVTIn] = Field(..., min_length=2)
    rel_perm: list[RelPermIn2] = Field(..., min_length=2)

    @model_validator(mode="after")
    def _mono(self):
        for i in range(1, len(self.pvt)):
            if self.pvt[i].p_psia >= self.pvt[i-1].p_psia:
                raise ValueError("pvt pressures must decrease")
        return self


class SchilthuisRowOut(BaseModel):
    p_psia: float
    Np_stb: float
    S_L: float
    R_scf_stb: float
    n_iter: int


class SchilthuisResponse(BaseModel):
    N_stb: float
    rows: list[SchilthuisRowOut]
