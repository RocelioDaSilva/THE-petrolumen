"""Pressure-transient calculations migrated from the legacy well-testing engine."""

from __future__ import annotations

import math


def calculate_radius_of_investigation(
    time_hours: float,
    permeability_md: float,
    porosity: float,
    total_compressibility_per_psi: float,
    viscosity_cp: float,
) -> float:
    """Estimate investigation radius in feet for a slightly compressible fluid.

    Uses the field-unit approximation ``r_i = sqrt(0.00105 k t / (phi mu c_t))``.
    """
    values = {
        "time_hours": time_hours,
        "permeability_md": permeability_md,
        "porosity": porosity,
        "total_compressibility_per_psi": total_compressibility_per_psi,
        "viscosity_cp": viscosity_cp,
    }
    for name, value in values.items():
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive.")

    return math.sqrt(
        0.00105
        * permeability_md
        * time_hours
        / (porosity * total_compressibility_per_psi * viscosity_cp)
    )
