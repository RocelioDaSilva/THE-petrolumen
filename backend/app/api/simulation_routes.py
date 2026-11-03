from typing import Literal, NoReturn

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, PositiveFloat, model_validator

from ..engines.reservoir.simulation import (
    BlackOilSimulator,
    CompositionalSimulator,
    ThermalSimulator,
)
from ..engines.reservoir.simulation.grid import Grid3D

router = APIRouter()
MAX_BLACK_OIL_CELLS = 512


class BlackOilResponse(BaseModel):
    pressure: list[float]
    saturations: dict[str, list[float]]
    wells: list[dict[str, object]]


class GridInput(BaseModel):
    nx: int = Field(gt=0)
    ny: int = Field(gt=0)
    nz: int = Field(gt=0)
    dx: PositiveFloat
    dy: PositiveFloat
    dz: PositiveFloat

    @property
    def cell_count(self) -> int:
        return self.nx * self.ny * self.nz


class WellInput(BaseModel):
    name: str
    i: int = Field(ge=0)
    j: int = Field(ge=0)
    perforation_layers: list[int]
    well_type: Literal["producer", "injector"]
    controls: dict[str, float]


class BlackOilInput(BaseModel):
    grid: GridInput
    porosity: list[float]
    permeability: list[float]
    rock_compressibility: float = Field(ge=0)
    fluid_properties: dict[str, PositiveFloat]
    initial_pressure: PositiveFloat
    initial_water_saturation: list[float]
    initial_gas_saturation: list[float]
    wells: list[WellInput] = Field(default_factory=list)
    timesteps: list[PositiveFloat] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_grid_data(self) -> "BlackOilInput":
        cell_count = self.grid.cell_count
        if cell_count > MAX_BLACK_OIL_CELLS:
            raise ValueError(
                f"Black-oil simulations are limited to {MAX_BLACK_OIL_CELLS} "
                "grid cells because this solver allocates dense matrices."
            )
        for name, values in (
            ("porosity", self.porosity),
            ("permeability", self.permeability),
            ("initial_water_saturation", self.initial_water_saturation),
            ("initial_gas_saturation", self.initial_gas_saturation),
        ):
            if len(values) != cell_count:
                raise ValueError(f"{name} must contain exactly {cell_count} values.")

        if any(value <= 0 or value > 1 for value in self.porosity):
            raise ValueError("Porosity values must be greater than 0 and at most 1.")
        if any(value < 0 or value > 1 for value in self.initial_water_saturation):
            raise ValueError("Water saturation values must be between 0 and 1.")
        if any(value < 0 or value > 1 for value in self.initial_gas_saturation):
            raise ValueError("Gas saturation values must be between 0 and 1.")
        if any(
            water + gas > 1
            for water, gas in zip(
                self.initial_water_saturation, self.initial_gas_saturation
            )
        ):
            raise ValueError("Water and gas saturations cannot sum to more than 1.")

        required_viscosities = {
            "water_viscosity",
            "oil_viscosity",
            "gas_viscosity",
        }
        missing = required_viscosities - self.fluid_properties.keys()
        if missing:
            raise ValueError(
                f"fluid_properties is missing required viscosities: {sorted(missing)}."
            )

        for well in self.wells:
            if well.i >= self.grid.nx or well.j >= self.grid.ny:
                raise ValueError(f"Well {well.name!r} is outside the grid.")
            if not well.perforation_layers or any(
                layer < 0 or layer >= self.grid.nz
                for layer in well.perforation_layers
            ):
                raise ValueError(
                    f"Well {well.name!r} must have valid perforation layers."
                )
        return self


class ComponentInput(BaseModel):
    name: str
    mw: PositiveFloat
    tc: PositiveFloat
    pc: PositiveFloat
    omega: float


class CompositionalInput(BaseModel):
    grid: GridInput
    components: list[ComponentInput] = Field(min_length=1)
    rock_properties: dict[str, float]
    wells: list[dict[str, object]] = Field(default_factory=list)
    initial_composition: dict[str, float]
    timesteps: list[PositiveFloat] = Field(min_length=1)


class ThermalPropertiesInput(BaseModel):
    rock_heat_capacity: PositiveFloat
    thermal_conductivity: PositiveFloat
    fluid_heat_capacity: PositiveFloat


class ThermalInput(CompositionalInput):
    thermal_properties: ThermalPropertiesInput
    initial_temperature: PositiveFloat


def _not_implemented(detail: str) -> NoReturn:
    raise HTTPException(status_code=501, detail=detail)


@router.post("/simulate/black-oil", tags=["Simulation"], response_model=BlackOilResponse)
def simulate_black_oil(payload: BlackOilInput) -> BlackOilResponse:
    simulator = BlackOilSimulator()
    simulator.setup_grid(
        payload.grid.nx,
        payload.grid.ny,
        payload.grid.nz,
        payload.grid.dx,
        payload.grid.dy,
        payload.grid.dz,
    )
    simulator.set_rock_properties(
        np.asarray(payload.porosity, dtype=float),
        np.asarray(payload.permeability, dtype=float),
        payload.rock_compressibility,
    )
    simulator.set_fluid_properties(payload.fluid_properties)

    for well in payload.wells:
        simulator.add_well(
            name=well.name,
            i=well.i,
            j=well.j,
            perforation_layers=well.perforation_layers,
            well_type=well.well_type,
            controls=well.controls,
        )

    simulator.initialize(
        payload.initial_pressure,
        {
            "water": np.asarray(payload.initial_water_saturation, dtype=float),
            "gas": np.asarray(payload.initial_gas_saturation, dtype=float),
        },
    )
    for timestep in payload.timesteps:
        simulator.run_timestep(timestep)

    pressure = np.asarray(simulator.pressure)
    water_saturation = np.asarray(simulator.saturations["water"])
    gas_saturation = np.asarray(simulator.saturations["gas"])
    if (
        not np.all(np.isfinite(pressure))
        or np.any(pressure <= 0)
        or not np.all(np.isfinite(water_saturation))
        or not np.all(np.isfinite(gas_saturation))
        or np.any(water_saturation < 0)
        or np.any(gas_saturation < 0)
        or np.any(water_saturation + gas_saturation > 1)
    ):
        raise HTTPException(
            status_code=500,
            detail=(
                "The black-oil solver produced a non-physical reservoir state; "
                "results were not returned."
            ),
        )

    results = simulator.get_results()
    return BlackOilResponse(
        pressure=results["pressure"].tolist(),
        saturations={
            phase: values.tolist() for phase, values in results["saturations"].items()
        },
        wells=results["wells"],
    )


@router.post("/simulate/compositional", tags=["Simulation"])
def simulate_compositional(payload: CompositionalInput) -> None:
    simulator = CompositionalSimulator()
    simulator.setup_components(
        [component.model_dump() for component in payload.components]
    )
    simulator.set_grid_and_rock(
        grid_from_input(payload.grid),
        payload.rock_properties,
    )
    for well in payload.wells:
        simulator.add_well(well)
    simulator.initialize_composition(payload.initial_composition)
    simulator.run_simulation(payload.timesteps)
    _not_implemented(
        "The compositional flow solver is not implemented; no simulation results "
        "were produced."
    )


@router.post("/simulate/thermal", tags=["Simulation"])
def simulate_thermal(payload: ThermalInput) -> None:
    simulator = ThermalSimulator()
    simulator.setup_components(
        [component.model_dump() for component in payload.components]
    )
    simulator.set_grid_and_rock(
        grid_from_input(payload.grid),
        payload.rock_properties,
    )
    simulator.set_thermal_properties(
        payload.thermal_properties.model_dump()
    )
    simulator.initialize_temperature(payload.initial_temperature)
    for timestep in payload.timesteps:
        simulator.run_thermal_timestep(timestep)
    _not_implemented(
        "The thermal flow and heat-transfer solver is not implemented; "
        "no simulation results were produced."
    )


def grid_from_input(grid: GridInput) -> Grid3D:
    return Grid3D(grid.nx, grid.ny, grid.nz, grid.dx, grid.dy, grid.dz)
