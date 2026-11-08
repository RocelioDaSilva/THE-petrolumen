from pydantic import BaseModel, Field, model_validator


class TwoStageRequest(BaseModel):
    phi_frac: float = Field(..., gt=0.0, lt=1.0)
    Swi: float = Field(..., ge=0.0, lt=1.0)
    Sgr: float = Field(..., ge=0.0, lt=1.0)
    Bgi: float = Field(..., gt=0.0)
    Bg_ps: float = Field(..., gt=0.0)
    Bga_500: float = Field(..., gt=0.0)
    Vb_ac_ft: float = Field(..., gt=0.0)

    @model_validator(mode="after")
    def _chk(self):
        if self.Swi + self.Sgr >= 1.0:
            raise ValueError("Swi + Sgr must be < 1")
        return self


class TwoStageResponse(BaseModel):
    g_init_scf: float
    gp_stage1_scf: float
    gp_stage2_scf: float
    gp_total_scf: float
    rf_total_pct: float
