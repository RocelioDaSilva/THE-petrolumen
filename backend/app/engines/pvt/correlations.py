"""Validated PVT property correlations used by production workflows."""

from __future__ import annotations

import math
from typing import Optional

from app.engines.reservoir.pvt import (
    calculate_oil_fvf_standing,
    calculate_z_factor_hall_yarborough,
)

__all__ = ["PVTProperties"]


class PVTProperties:
    """Oil and gas PVT correlations with field-unit inputs."""

    @staticmethod
    def _require_finite(name: str, value: float) -> None:
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite.")

    def calculate_solution_gas_ratio(
        self,
        pressure: float,
        temperature: float,
        api_gravity: float,
        gas_specific_gravity: float,
    ) -> float:
        """Calculate solution GOR (scf/STB) from Standing's bubble-point fit."""
        for name, value in (
            ("pressure", pressure),
            ("temperature", temperature),
            ("API gravity", api_gravity),
            ("gas specific gravity", gas_specific_gravity),
        ):
            self._require_finite(name, value)
        if pressure <= 0 or api_gravity <= 0 or gas_specific_gravity <= 0:
            raise ValueError("Pressure, API gravity, and gas specific gravity must be positive.")
        if temperature <= -459.67:
            raise ValueError("Temperature must be above absolute zero (-459.67 °F).")

        exponent = 0.0125 * api_gravity - 0.00091 * temperature
        term = (pressure / 18.2 + 1.4) * 10.0**exponent
        return float(gas_specific_gravity * term**1.2048)

    def calculate_formation_volume_factor(
        self,
        pressure: float,
        temperature: float,
        fluid_type: str,
        api_gravity: Optional[float] = None,
        gas_specific_gravity: Optional[float] = None,
    ) -> float:
        """Calculate oil Bo (rb/STB) or gas Bg (ft³/scf)."""
        self._require_finite("pressure", pressure)
        self._require_finite("temperature", temperature)
        if pressure <= 0:
            raise ValueError("Pressure must be positive.")
        fluid = fluid_type.casefold()

        if fluid == "oil":
            if api_gravity is None or gas_specific_gravity is None:
                raise ValueError("Oil FVF requires API and gas specific gravities.")
            if not math.isfinite(api_gravity) or api_gravity <= 0:
                raise ValueError("API gravity must be finite and positive.")
            if not math.isfinite(gas_specific_gravity) or gas_specific_gravity <= 0:
                raise ValueError("Gas specific gravity must be finite and positive.")
            rs = self.calculate_solution_gas_ratio(
                pressure, temperature, api_gravity, gas_specific_gravity
            )
            oil_specific_gravity = 141.5 / (api_gravity + 131.5)
            return calculate_oil_fvf_standing(
                rs, gas_specific_gravity, oil_specific_gravity, temperature
            )

        if fluid == "gas":
            if gas_specific_gravity is None:
                raise ValueError("Gas FVF requires gas specific gravity.")
            z_factor = self.calculate_z_factor(
                pressure, temperature, gas_specific_gravity
            )
            temperature_rankine = temperature + 459.67
            return 0.02827 * z_factor * temperature_rankine / pressure

        raise ValueError(f"Unsupported fluid type: {fluid_type}")

    def calculate_viscosity(
        self,
        pressure: float,
        temperature: float,
        fluid_type: str,
        api_gravity: Optional[float] = None,
        gas_specific_gravity: Optional[float] = None,
    ) -> float:
        """Calculate oil viscosity (Beggs-Robinson) or gas viscosity (Lee et al.)."""
        for name, value in (("pressure", pressure), ("temperature", temperature)):
            self._require_finite(name, value)
        if pressure <= 0:
            raise ValueError("Pressure must be positive.")
        if temperature <= -459.67:
            raise ValueError("Temperature must be above absolute zero (-459.67 °F).")
        fluid = fluid_type.casefold()

        if fluid == "oil":
            if api_gravity is None or gas_specific_gravity is None:
                raise ValueError("Oil viscosity requires API and gas specific gravities.")
            if not math.isfinite(api_gravity) or api_gravity <= 0:
                raise ValueError("API gravity must be finite and positive.")
            if not math.isfinite(gas_specific_gravity) or gas_specific_gravity <= 0:
                raise ValueError("Gas specific gravity must be finite and positive.")
            if temperature <= -200:
                raise ValueError("Beggs-Robinson dead-oil viscosity requires temperature above -200 °F.")

            exponent = 10.0 ** (0.43 + 8.33 / api_gravity)
            dead_oil = (
                0.32 + 1.8e7 / api_gravity**4.53
            ) * (360.0 / (temperature + 200.0)) ** exponent
            rs = self.calculate_solution_gas_ratio(
                pressure, temperature, api_gravity, gas_specific_gravity
            )
            a = 10.715 * (rs + 100.0) ** -0.515
            b = 5.44 * (rs + 150.0) ** -0.338
            viscosity = a * dead_oil**b
        elif fluid == "gas":
            if gas_specific_gravity is None or not math.isfinite(gas_specific_gravity):
                raise ValueError("Gas viscosity requires finite gas specific gravity.")
            if gas_specific_gravity <= 0:
                raise ValueError("Gas specific gravity must be positive.")
            temperature_rankine = temperature + 459.67
            molecular_weight = gas_specific_gravity * 28.97
            z_factor = self.calculate_z_factor(
                pressure, temperature, gas_specific_gravity
            )
            density = pressure * molecular_weight / (10.73 * temperature_rankine * z_factor)
            k = (
                (9.4 + 0.02 * molecular_weight)
                * temperature_rankine**1.5
                / (209.0 + 19.0 * molecular_weight + temperature_rankine)
            )
            x = 3.5 + 986.0 / temperature_rankine + 0.01 * molecular_weight
            y = 2.4 - 0.2 * x
            viscosity = 1e-4 * k * math.exp(x * density**y)
        else:
            raise ValueError(f"Unsupported fluid type: {fluid_type}")

        if not math.isfinite(viscosity) or viscosity <= 0:
            raise ValueError(f"Unphysical viscosity calculated: {viscosity}")
        return float(viscosity)

    def calculate_z_factor(
        self,
        pressure: float,
        temperature: float,
        gas_specific_gravity: float,
    ) -> float:
        """Calculate gas compressibility using the canonical Hall-Yarborough solver."""
        return calculate_z_factor_hall_yarborough(
            pressure, temperature, gas_specific_gravity
        )