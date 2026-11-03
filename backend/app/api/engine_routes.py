"""HTTP endpoints for the organized petroleum-engineering engines."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, PositiveFloat, model_validator

from ..engines.drilling.trajectory import (
    compute_trajectory_minimum_curvature,
)
from ..engines.geology.mesh import Grid3D
from ..engines.pvt.eos_solver import EosSolver
from ..engines.reservoir.nodal import find_operating_point

router = APIRouter()


class EosResponse(BaseModel):
    z_factor: float


class TrajectoryResponse(BaseModel):
    survey: list[dict[str, float]]


class GridResponse(BaseModel):
    shape: list[int]
    total_cells: int
    bulk_volume: float


class NodalResponse(BaseModel):
    operating_rate: float


class EosComponentInput(BaseModel):
    name: str
    critical_pressure: PositiveFloat = Field(
        description="Critical pressure in Pa; consistent with request pressure."
    )
    critical_temperature: PositiveFloat = Field(
        description="Critical temperature in K; consistent with request temperature."
    )
    acentric_factor: float
    molecular_weight: PositiveFloat | None = None


class EosRequest(BaseModel):
    pressure: PositiveFloat = Field(description="Pressure in Pa.")
    temperature: PositiveFloat = Field(description="Temperature in K.")
    components: list[EosComponentInput] = Field(min_length=1)
    composition: dict[str, float]
    eos_type: Literal["PR"] = "PR"
    binary_interactions: list[list[float]] | None = None

    @model_validator(mode="after")
    def validate_mixture(self) -> "EosRequest":
        names = [component.name for component in self.components]
        if len(set(names)) != len(names):
            raise ValueError("Component names must be unique.")
        if not math.isfinite(self.pressure) or not math.isfinite(self.temperature):
            raise ValueError("Pressure and temperature must be finite.")
        for component in self.components:
            values = (
                component.critical_pressure,
                component.critical_temperature,
                component.acentric_factor,
            )
            if not all(math.isfinite(value) for value in values):
                raise ValueError(
                    f"Critical properties for {component.name!r} must be finite."
                )
            if (
                component.molecular_weight is not None
                and not math.isfinite(component.molecular_weight)
            ):
                raise ValueError(
                    f"Molecular weight for {component.name!r} must be finite."
                )
        if set(self.composition) != set(names):
            raise ValueError("Composition keys must exactly match component names.")
        fractions = list(self.composition.values())
        if any(not math.isfinite(value) or value < 0 for value in fractions):
            raise ValueError("Mole fractions must be finite and non-negative.")
        if not math.isclose(sum(fractions), 1.0, rel_tol=1e-6, abs_tol=1e-8):
            raise ValueError("Mole fractions must sum to 1.")

        if self.binary_interactions is not None:
            count = len(names)
            matrix = np.asarray(self.binary_interactions, dtype=float)
            if matrix.shape != (count, count) or not np.all(np.isfinite(matrix)):
                raise ValueError(
                    "binary_interactions must be a finite square matrix matching "
                    "the number of components."
                )
        return self


class SurveyInput(BaseModel):
    survey: list[dict[str, float]] = Field(min_length=1)
    md_col: str = "md"
    inc_col: str = "inc"
    azi_col: str = "azi"

    @model_validator(mode="after")
    def validate_survey_columns(self) -> "SurveyInput":
        required = {self.md_col, self.inc_col, self.azi_col}
        for index, station in enumerate(self.survey):
            missing = required - station.keys()
            if missing:
                raise ValueError(
                    f"Survey station {index} is missing columns: {sorted(missing)}."
                )
            if any(not math.isfinite(station[column]) for column in required):
                raise ValueError(f"Survey station {index} contains non-finite values.")
        return self


class GridRequest(BaseModel):
    nx: int = Field(gt=0)
    ny: int = Field(gt=0)
    nz: int = Field(gt=0)
    dx: PositiveFloat | list[PositiveFloat]
    dy: PositiveFloat | list[PositiveFloat]
    dz: PositiveFloat | list[PositiveFloat]

    @model_validator(mode="after")
    def validate_spacing_lengths(self) -> "GridRequest":
        for name, spacing, count in (
            ("dx", self.dx, self.nx),
            ("dy", self.dy, self.ny),
            ("dz", self.dz, self.nz),
        ):
            widths = spacing if isinstance(spacing, list) else [spacing]
            if isinstance(spacing, list) and len(spacing) != count:
                raise ValueError(f"{name} must contain exactly {count} cell widths.")
            if any(not math.isfinite(width) for width in widths):
                raise ValueError(f"{name} cell widths must be finite.")
        return self


class NodalRequest(BaseModel):
    qi: PositiveFloat
    pr: PositiveFloat
    p_surf: float = Field(default=1000.0, ge=0)
    a: float = Field(default=0.002, ge=0)
    b: float = Field(default=10.0, ge=0)

    @model_validator(mode="after")
    def validate_finite_values(self) -> "NodalRequest":
        if not all(
            math.isfinite(value)
            for value in (self.qi, self.pr, self.p_surf, self.a, self.b)
        ):
            raise ValueError("Nodal-analysis inputs must be finite.")
        return self


@router.post("/engine/pvt/eos", tags=["PVT"], response_model=EosResponse)
def calculate_eos(payload: EosRequest) -> EosResponse:
    """Calculate mixture compressibility with the Peng-Robinson equation."""
    solver = EosSolver(eos_type=payload.eos_type)
    for component in payload.components:
        properties = component.model_dump(
            exclude={"name", "molecular_weight"}, exclude_none=True
        )
        if component.molecular_weight is not None:
            properties["molecular_weight"] = component.molecular_weight
        solver.add_component(component.name, properties)

    count = len(payload.components)
    interactions = payload.binary_interactions
    solver.set_binary_interactions(
        np.zeros((count, count), dtype=float)
        if interactions is None
        else np.asarray(interactions, dtype=float)
    )
    try:
        z_factor = solver.calculate_z_factor(
            payload.pressure, payload.temperature, payload.composition
        )
    except (ValueError, KeyError, FloatingPointError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if not math.isfinite(z_factor) or z_factor <= 0:
        raise HTTPException(
            status_code=500,
            detail="The equation-of-state solver produced a non-physical Z-factor.",
        )
    return EosResponse(z_factor=float(z_factor))


@router.post("/engine/drilling/trajectory", tags=["Drilling"], response_model=TrajectoryResponse)
def calculate_trajectory(payload: SurveyInput) -> TrajectoryResponse:
    """Compute survey coordinates using minimum curvature."""
    dataframe = pd.DataFrame(payload.survey)
    try:
        result = compute_trajectory_minimum_curvature(
            dataframe,
            md_col=payload.md_col,
            inc_col=payload.inc_col,
            azi_col=payload.azi_col,
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return TrajectoryResponse(survey=result.to_dict(orient="records"))


@router.post("/engine/geology/grid", tags=["Geology"], response_model=GridResponse)
def calculate_grid(payload: GridRequest) -> GridResponse:
    """Create a Cartesian 3D grid and report its dimensions and bulk volume."""
    grid = Grid3D(
        payload.nx,
        payload.ny,
        payload.nz,
        payload.dx,
        payload.dy,
        payload.dz,
    )
    return GridResponse(
        shape=list(grid.shape),
        total_cells=grid.total_cells,
        bulk_volume=float(np.sum(grid.volumes)),
    )


@router.post("/engine/reservoir/nodal", tags=["Reservoir"], response_model=NodalResponse)
def calculate_nodal(payload: NodalRequest) -> NodalResponse:
    """Calculate the operating flow rate at the IPR/TPR intersection."""
    try:
        operating_rate = find_operating_point(
            qi=payload.qi,
            pr=payload.pr,
            p_surf=payload.p_surf,
            a=payload.a,
            b=payload.b,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return NodalResponse(operating_rate=float(operating_rate))
