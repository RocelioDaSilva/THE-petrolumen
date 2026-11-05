"""Reservoir pressure-transient analysis (PTA) endpoints.

Exposes the consolidated well-test engine
:mod:`app.engines.reservoir.well_test_analysis` (Horner buildup, semilog
drawdown, Bourdet derivative, flow-regime detection) over HTTP. The engine
logic was recovered from the legacy prototype and reimplemented with correct
field-unit equations.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.engines.reservoir.well_test_analysis import analyze_buildup, analyze_drawdown

router = APIRouter(prefix="/api/v1/reservoir/well-test", tags=["reservoir-well-test"])


class FlowRegimesResponse(BaseModel):
    radial: tuple[float, float] | None = None
    wellbore_storage: tuple[float, float] | None = None
    boundary: tuple[float, float] | None = None
    radial_slope: float | None = None
    radial_std: float | None = None
    notes: list[str] = Field(default_factory=list)


class DrawdownRequest(BaseModel):
    time: list[float] = Field(..., min_length=3, description="Elapsed time [hours]")
    pressure: list[float] = Field(..., min_length=3, description="Flowing BHP [psia]")
    rate: float = Field(..., gt=0, description="Constant rate [STB/day]")
    viscosity: float = Field(..., gt=0, description="Viscosity [cp]")
    total_compressibility: float = Field(..., gt=0, description="Total compressibility [1/psi]")
    porosity: float = Field(..., gt=0, le=1, description="Porosity [fraction]")
    wellbore_radius: float = Field(..., gt=0, description="Wellbore radius [ft]")
    initial_pressure: float = Field(..., gt=0, description="Initial pressure before drawdown [psia]")
    net_pay: float = Field(..., gt=0, description="Net pay thickness [ft]")
    formation_volume_factor: float = Field(1.0, gt=0, description="FVF [RB/STB]")


class DrawdownResponse(BaseModel):
    permeability_md: float
    skin: float
    slope_psi_per_cycle: float
    intercept_psi: float
    p1hr_psi: float
    radius_of_investigation_ft: float
    regimes: FlowRegimesResponse


class BuildupRequest(BaseModel):
    time: list[float] = Field(..., min_length=3, description="Shut-in time [hours]")
    pressure: list[float] = Field(..., min_length=3, description="Shut-in pressure [psia]")
    rate: float = Field(..., gt=0, description="Rate before shut-in [STB/day]")
    viscosity: float = Field(..., gt=0, description="Viscosity [cp]")
    total_compressibility: float = Field(..., gt=0, description="Total compressibility [1/psi]")
    porosity: float = Field(..., gt=0, le=1, description="Porosity [fraction]")
    wellbore_radius: float = Field(..., gt=0, description="Wellbore radius [ft]")
    producing_time: float = Field(..., gt=0, description="Producing time before shut-in [hours]")
    p_wf_at_shutin: float = Field(..., gt=0, description="Flowing BHP just before shut-in [psia]")
    net_pay: float = Field(..., gt=0, description="Net pay thickness [ft]")
    formation_volume_factor: float = Field(1.0, gt=0, description="FVF [RB/STB]")


class BuildupResponse(BaseModel):
    permeability_md: float
    skin: float
    slope_psi_per_cycle: float
    p_star_psi: float
    p1hr_psi: float
    regimes: FlowRegimesResponse


@router.post("/drawdown", response_model=DrawdownResponse)
def api_analyze_drawdown(req: DrawdownRequest):
    try:
        result = analyze_drawdown(
            time=req.time,
            pressure=req.pressure,
            rate=req.rate,
            viscosity=req.viscosity,
            total_compressibility=req.total_compressibility,
            porosity=req.porosity,
            wellbore_radius=req.wellbore_radius,
            initial_pressure=req.initial_pressure,
            net_pay=req.net_pay,
            formation_volume_factor=req.formation_volume_factor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return DrawdownResponse(
        permeability_md=result.permeability_md,
        skin=result.skin,
        slope_psi_per_cycle=result.slope_psi_per_cycle,
        intercept_psi=result.intercept_psi,
        p1hr_psi=result.p1hr_psi,
        radius_of_investigation_ft=result.radius_of_investigation_ft,
        regimes=FlowRegimesResponse(
            radial=result.regimes.radial,
            wellbore_storage=result.regimes.wellbore_storage,
            boundary=result.regimes.boundary,
            radial_slope=result.regimes.radial_slope,
            radial_std=result.regimes.radial_std,
            notes=result.regimes.notes,
        ),
    )


@router.post("/buildup", response_model=BuildupResponse)
def api_analyze_buildup(req: BuildupRequest):
    try:
        result = analyze_buildup(
            time=req.time,
            pressure=req.pressure,
            rate=req.rate,
            viscosity=req.viscosity,
            total_compressibility=req.total_compressibility,
            porosity=req.porosity,
            wellbore_radius=req.wellbore_radius,
            producing_time=req.producing_time,
            p_wf_at_shutin=req.p_wf_at_shutin,
            net_pay=req.net_pay,
            formation_volume_factor=req.formation_volume_factor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return BuildupResponse(
        permeability_md=result.permeability_md,
        skin=result.skin,
        slope_psi_per_cycle=result.slope_psi_per_cycle,
        p_star_psi=result.p_star_psi,
        p1hr_psi=result.p1hr_psi,
        regimes=FlowRegimesResponse(
            radial=result.regimes.radial,
            wellbore_storage=result.regimes.wellbore_storage,
            boundary=result.regimes.boundary,
            radial_slope=result.regimes.radial_slope,
            radial_std=result.regimes.radial_std,
            notes=result.regimes.notes,
        ),
    )
