"""Gas reservoir material balance engine and Rate Transient Analysis (RTA).

Provides Flowing Material Balance (FMB) calculations for original gas in place (OGIP)
estimation based on P/Z straight-line methods.
"""

from __future__ import annotations

import math
from typing import TypedDict
from app.engines.reservoir.pvt import calculate_z_factor_hall_yarborough


class RTAPoint(TypedDict):
    gp: float
    pz: float
    pwf: float


class FMBGasResult(TypedDict):
    points: list[RTAPoint]
    ogip: float
    slope: float
    pzi: float


def calculate_fmb_gas(
    pi: float = 3200.0,
    tf: float = 160.0,
    gamma_g: float = 0.65,
    ogip_expected: float = 1200.0,
    steps: int = 10,
) -> FMBGasResult:
    """Calculate Flowing Material Balance (FMB) points for a gas reservoir.

    Governing Equation (Dry Gas Material Balance):
        P / Z = (Pi / Zi) * (1 - Gp / OGIP)
        Slope = - (Pi / Zi) / OGIP

    Parameters:
        pi: Initial reservoir pressure (psia). Must be > 0.
        tf: Reservoir temperature (°F). Must be > -459.67 °F.
        gamma_g: Gas specific gravity (air = 1.0). Must be > 0.
        ogip_expected: Expected Original Gas In Place (MMscf).
        steps: Number of evaluation intervals.

    Returns:
        FMBGasResult dictionary containing:
            - points: list of RTAPoint dictionaries (gp, pz, pwf)
            - ogip: estimated or input OGIP (MMscf)
            - slope: P/Z vs Gp straight-line slope (psia / MMscf)
            - pzi: initial P/Z ratio (psia)

    Raises:
        ValueError: If thermodynamic inputs or OGIP are non-physical.
    """
    if pi <= 0:
        raise ValueError(f"pi must be strictly positive, got {pi}")
    if tf <= -459.67:
        raise ValueError(f"tf must be above absolute zero (-459.67 °F), got {tf}")
    if gamma_g <= 0:
        raise ValueError(f"gamma_g must be positive, got {gamma_g}")
    if ogip_expected <= 0:
        raise ValueError(f"ogip_expected must be positive, got {ogip_expected}")
    if steps < 1:
        raise ValueError("steps must be at least 1.")

    zi = calculate_z_factor_hall_yarborough(pi, tf, gamma_g)
    if zi <= 0:
        zi = 1.0

    pzi = pi / zi
    slope = -pzi / ogip_expected

    points: list[RTAPoint] = []
    for i in range(steps + 1):
        gp = round((i * (ogip_expected * 0.75)) / steps, 2)
        pz = max(0.0, pzi + slope * gp)
        pwf = max(50.0, pz * 0.92)
        points.append({
            "gp": float(gp),
            "pz": round(float(pz), 2),
            "pwf": round(float(pwf), 2),
        })

    return {
        "points": points,
        "ogip": float(ogip_expected),
        "slope": round(float(slope), 4),
        "pzi": round(float(pzi), 2),
    }


def estimate_ogip_from_production(
    gp: list[float],
    pz: list[float],
) -> tuple[float, float, float]:
    """Estimate Original Gas In Place (OGIP) by linear regression on P/Z vs Gp.

    Fits the line:
        P/Z = P/Zi + Slope * Gp
    Where:
        OGIP = - (P/Zi) / Slope

    Parameters:
        gp: Cumulative gas production data points (MMscf).
        pz: Reservoir pressure divided by Z-factor data points (psia).

    Returns:
        tuple containing (ogip_mmscf, slope, pzi).

    Raises:
        ValueError: If data arrays have unequal lengths or less than 2 points.
    """
    if len(gp) != len(pz):
        raise ValueError("gp and pz must have identical length.")
    if len(gp) < 2:
        raise ValueError("At least 2 points required for linear regression.")

    n = len(gp)
    sum_x = sum(gp)
    sum_y = sum(pz)
    sum_xx = sum(x * x for x in gp)
    sum_xy = sum(x * y for x, y in zip(gp, pz))

    denom = (n * sum_xx - sum_x * sum_x)
    if denom == 0:
        raise ValueError("Degenerate Gp values; cannot perform linear regression.")

    slope = (n * sum_xy - sum_x * sum_y) / denom
    pzi = (sum_y - slope * sum_x) / n

    if slope >= 0:
        raise ValueError("Positive or zero slope observed; gas reservoir must show pressure decline.")

    ogip = -pzi / slope
    return round(ogip, 2), round(slope, 4), round(pzi, 2)
