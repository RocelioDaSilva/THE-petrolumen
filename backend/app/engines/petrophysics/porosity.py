"""Petrophysical log property calculations (porosity, saturation, etc.)."""

from __future__ import annotations

import pandas as pd


def calculate_density_porosity(
    rho_bulk: float | pd.Series,
    rho_matrix: float = 2.65,
    rho_fluid: float = 1.0,
) -> float | pd.Series:
    """Calculate formation porosity from bulk density log.

    phi = (rho_matrix - rho_bulk) / (rho_matrix - rho_fluid)

    Args:
        rho_bulk: Bulk density from log (g/cm^3)
        rho_matrix: Matrix rock density (g/cm^3, default 2.65 for quartz sandstone)
        rho_fluid: Pore fluid density (g/cm^3, default 1.0 for fresh water)

    Returns:
        Porosity as fraction (0.0 to 1.0)
    """
    if rho_matrix <= 0 or rho_fluid <= 0:
        raise ValueError("Matrix and fluid densities must be strictly positive.")
    if rho_matrix == rho_fluid:
        raise ValueError("rho_matrix and rho_fluid cannot be identical.")
    if isinstance(rho_bulk, (int, float)) and rho_bulk <= 0:
        raise ValueError(f"Bulk density must be positive, got {rho_bulk}")
    return (rho_matrix - rho_bulk) / (rho_matrix - rho_fluid)
