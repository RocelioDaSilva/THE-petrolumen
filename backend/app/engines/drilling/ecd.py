"""Drilling fluids and Equivalent Circulating Density (ECD) calculations."""

from __future__ import annotations

# Standard acceleration due to gravity (m/s^2)
G: float = 9.80665


def pressure_from_density(rho: float, depth: float) -> float:
    """Calculate hydrostatic pressure in Pascals (Pa) from density and depth.

    Args:
        rho: Fluid density in kg/m^3
        depth: True vertical depth in meters (m)

    Returns:
        Hydrostatic pressure in Pa
    """
    if rho < 0 or depth < 0:
        raise ValueError("Density and depth must be non-negative.")
    return rho * G * depth


def hydrostatic_pressure_bar(rho: float, depth: float) -> float:
    """Calculate hydrostatic pressure in bar.

    Args:
        rho: Fluid density in kg/m^3
        depth: True vertical depth in meters (m)

    Returns:
        Hydrostatic pressure in bar (1 bar = 10^5 Pa)
    """
    return pressure_from_density(rho, depth) / 1e5
