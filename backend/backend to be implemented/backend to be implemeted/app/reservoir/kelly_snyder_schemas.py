from pydantic import BaseModel, Field, model_validator


class KSPointIn(BaseModel):
    p_psia: float = Field(..., gt=0.0)
    Bo_bbl_stb: float = Field(..., gt=0.0)
    Bt_bbl_stb: float = Field(..., gt=0.0)
    Bg_bbl_scf: float = Field(..., gt=0.0)
    Rso_scf_stb: float = Field(..., ge=0.0)


class KSRequest(BaseModel):
    N_stb: float = Field(..., gt=0.0)
    Swi: float = Field(..., ge=0.0, lt=1.0)
    Sgc: float = Field(..., gt=0.0, lt=1.0)
    pvt: list[KSPointIn] = Field(..., min_length=2)

    @model_validator(mode="after")
    def _monotone(self):
        for i in range(1, len(self.pvt)):
            if self.pvt[i].p_psia >= self.pvt[i-1].p_psia:
                raise ValueError("pvt pressures must strictly decrease")
        return self


class KSRowOut(BaseModel):
    p_psia: float
    Np_stb: float
    Sg: float
    Np_over_N: float


class KSResponse(BaseModel):
    N_stb: float
    rows: list[KSRowOut]
    stopped_at_critical: bool
