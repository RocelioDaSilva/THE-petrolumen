"""Pydantic v2 schemas for the wellbore-storage endpoint."""
from pydantic import BaseModel, Field


class WSPoint(BaseModel):
    dt_hr: float = Field(..., gt=0.0)
    pwf_psia: float = Field(..., gt=0.0)


class WellboreStorageRequest(BaseModel):
    early_points: list[WSPoint] = Field(..., min_length=3)
    Q_stb_d: float = Field(..., gt=0.0)
    late_points: list[WSPoint] | None = Field(default=None)


class WellboreStorageResponse(BaseModel):
    F_bbl_per_psi: float = Field(..., gt=0.0)
    F_ft5_per_lbf: float = Field(..., gt=0.0)
    r_squared_early: float
    r_squared_late: float | None = None
    late_data_usable: bool
    early_fit_slope_psi_per_hr: float
