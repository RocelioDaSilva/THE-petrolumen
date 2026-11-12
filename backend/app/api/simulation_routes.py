from typing import Literal, NoReturn

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import Field, PositiveFloat, model_validator

from .base import APIModel as BaseModel
from ..engines.reservoir.simulation import BlackOilSimulator
from ..engines.reservoir.simulation.black_oil_simulator import WellControlError
from ..engines.reservoir.simulation.grid import Grid3D

router = APIRouter()
MAX_SIMULATION_CELLS = 512


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

    @model_validator(mode="after")
    def validate_resource_bounds(self) -> "GridInput":
        if self.cell_count > MAX_SIMULATION_CELLS:
            raise ValueError(
                f"Simulation grids are limited to {MAX_SIMULATION_CELLS} cells."
            )
        return self


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
            supported_controls = {"bhp", "water_rate", "gas_rate"}
            unsupported_controls = set(well.controls) - supported_controls
            if unsupported_controls:
                raise ValueError(
                    f"Well {well.name!r} has unsupported controls: "
                    f"{sorted(unsupported_controls)}."
                )
            if not well.controls:
                raise ValueError(
                    f"Well {well.name!r} must specify at least one supported control."
                )
            for control, value in well.controls.items():
                if not np.isfinite(value) or (
                    value <= 0 if control == "bhp" else value < 0
                ):
                    constraint = "positive" if control == "bhp" else "non-negative"
                    raise ValueError(
                        f"Well {well.name!r} {control} must be finite and "
                        f"{constraint}."
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


class UnimplementedResponse(BaseModel):
    detail: str
    tracking: str


def _not_implemented(detail: str, tracking: str) -> NoReturn:
    raise HTTPException(
        status_code=501,
        detail={"detail": detail, "tracking": tracking},
    )


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
        try:
            simulator.run_timestep(timestep)
        except WellControlError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except (ArithmeticError, np.linalg.LinAlgError) as error:
            raise HTTPException(
                status_code=422,
                detail=f"Black-oil solver failed numerically: {error}",
            ) from error

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


@router.post(
    "/simulate/compositional",
    responses={501: {"model": UnimplementedResponse, "description": "The compositional flow solver is not implemented."}},
    tags=["Simulation"],
)
def simulate_compositional(payload: CompositionalInput) -> None:
    _not_implemented(
        "The compositional flow solver is not implemented; no simulation results were produced.",
        "app.engines.reservoir.simulation.compositional_simulator.CompositionalSimulator",
    )


@router.post(
    "/simulate/thermal",
    responses={501: {"model": UnimplementedResponse, "description": "The thermal flow and heat-transfer solver is not implemented."}},
    tags=["Simulation"],
)
def simulate_thermal(payload: ThermalInput) -> None:
    _not_implemented(
        "The thermal flow and heat-transfer solver is not implemented; no simulation results were produced.",
        "app.engines.reservoir.simulation.thermal_simulator.ThermalSimulator",
    )


def grid_from_input(grid: GridInput) -> Grid3D:
    return Grid3D(grid.nx, grid.ny, grid.nz, grid.dx, grid.dy, grid.dz)
