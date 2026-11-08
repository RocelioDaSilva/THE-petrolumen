from pydantic import BaseModel, Field, model_validator


class GCWaterDriveRequest(BaseModel):
    Swi: float = Field(..., ge=0.0, lt=1.0)
    Sgr: float = Field(..., ge=0.0, lt=1.0)
    F_invaded: float = Field(..., ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _check(self):
        if self.Swi + self.Sgr >= 1.0:
            raise ValueError("Swi + Sgr must be < 1")
        return self


class GCWaterDriveResponse(BaseModel):
    recovery: float
    out_of_physical_range: bool
