"""Pydantic v2 schemas for the superposition endpoint."""

from pydantic import BaseModel, Field


class SuperpositionSource(BaseModel):
    q_stb_d: float = Field(
        ..., description="Rate, STB/day (positive=production)"
    )
    t_start_hr: float = Field(..., ge=0.0, description="Start time, hr")
    distance_ft: float = Field(
        ..., gt=0.0, description="Distance to observation, ft"
    )


class SuperpositionRequest(BaseModel):
    observation_time_hr: float = Field(..., gt=0.0)
    sources: list[SuperpositionSource] = Field(..., min_length=1)
    k_md: float = Field(..., gt=0.0)
    h_ft: float = Field(..., gt=0.0)
    mu_cp: float = Field(..., gt=0.0)
    B_bbl_stb: float = Field(..., gt=0.0)
    phi: float = Field(..., ge=0.001, lt=1.0)
    ct_psi_inv: float = Field(..., gt=0.0)


class SuperpositionResponse(BaseModel):
    dp_total_psi: float
    dp_per_source_psi: list[float]
    ei_arguments: list[float]
    inactive_source_indices: list[int]
