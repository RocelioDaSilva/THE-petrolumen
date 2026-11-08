from pydantic import BaseModel, Field, model_validator

class AbandonmentRequest(BaseModel):
    G_scf: float = Field(..., gt=0.0)
    pi_over_zi: float = Field(..., gt=0.0)
    pa_over_za: float = Field(..., gt=0.0)
    water_drive_Gpa_scf: float | None = Field(default=None, ge=0.0)

    @model_validator(mode="after")
    def _chk(self):
        if self.pa_over_za >= self.pi_over_zi:
            raise ValueError("pa_over_za must be < pi_over_zi")
        return self

class AbandonmentResponse(BaseModel):
    G_scf: float
    Gp_at_abandonment_scf: float
    RF_at_abandonment: float
    pz_ratio: float
    method: str
