from pydantic import BaseModel, Field, model_validator


class ThreeStageGERequest(BaseModel):
    Gps_scf: float = Field(..., ge=0.0)
    Gss_scf: float = Field(0.0, ge=0.0)
    Gst_scf: float = Field(..., ge=0.0)
    Np_stb: float = Field(..., ge=0.0)
    gamma_o: float | None = Field(default=None, gt=0.0, lt=1.008)
    M_wo: float | None = Field(default=None, gt=0.0)
    oil_api: float | None = Field(default=None, gt=8.811, lt=100.0)
    two_stage: bool = Field(default=False)

    @model_validator(mode="after")
    def _ident(self):
        if (self.gamma_o is None and self.M_wo is None
                and self.oil_api is None):
            raise ValueError("Provide gamma_o, M_wo, or oil_api")
        return self


class ThreeStageGEResponse(BaseModel):
    Gp_total_scf: float
    GE_scf_per_bbl: float
    Gp_from_condensate_scf: float
    two_stage: bool
