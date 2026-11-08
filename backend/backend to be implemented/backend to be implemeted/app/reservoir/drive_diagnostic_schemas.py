from typing import Literal
from pydantic import BaseModel, Field, model_validator


class DiagnosticSnapshotIn(BaseModel):
    t_days: float = Field(..., ge=0.0)
    Np_stb: float = Field(..., ge=0.0)
    Rp_scf_stb: float = Field(..., ge=0.0)
    Wp_stb: float = Field(..., ge=0.0)
    Bt: float = Field(..., gt=0.0)
    Bti: float = Field(..., gt=0.0)
    Bg: float = Field(..., gt=0.0)
    Rsoi: float = Field(..., ge=0.0)
    m: float = Field(..., ge=0.0)
    Bgi: float | None = Field(default=None, gt=0.0)
    Swi: float = Field(..., ge=0.0, lt=1.0)
    cw_psi_inv: float = Field(0.0, ge=0.0)
    cf_psi_inv: float = Field(0.0, ge=0.0)
    delta_p_psi: float = Field(0.0, ge=0.0)


class DriveDiagRequest(BaseModel):
    snapshots: list[DiagnosticSnapshotIn] = Field(..., min_length=3)

    @model_validator(mode="after")
    def _mono(self):
        for i in range(1, len(self.snapshots)):
            if self.snapshots[i].t_days <= self.snapshots[i-1].t_days:
                raise ValueError("times must strictly increase")
        return self


class DriveDiagResponse(BaseModel):
    classification: Literal[
        "volumetric", "water_drive", "decreasing", "insufficient_data"
    ]
    trend_fraction: float
    N_per_point_stb: list[float]
    ddi_per_point: list[float]
    sdi_per_point: list[float]
    r_squared: float
