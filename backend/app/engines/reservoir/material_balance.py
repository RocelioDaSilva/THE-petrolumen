"""Gas reservoir material balance engine and Rate Transient Analysis (RTA).

Provides Flowing Material Balance (FMB) calculations for original gas in place (OGIP)
estimation based on P/Z straight-line methods.
"""

from __future__ import annotations

import math
from typing import TypedDict

from .pvt import calculate_z_factor_hall_yarborough


def _hydrocarbon_pore_volume_ac_ft(
    area_acres: float,
    net_pay_ft: float,
    porosity: float,
    water_saturation: float,
) -> float:
    for name, value in (
        ("area_acres", area_acres),
        ("net_pay_ft", net_pay_ft),
        ("porosity", porosity),
        ("water_saturation", water_saturation),
    ):
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite.")
    if area_acres <= 0 or net_pay_ft <= 0:
        raise ValueError("Area and net pay must be positive.")
    if not 0 < porosity <= 1:
        raise ValueError("Porosity must be greater than zero and at most one.")
    if not 0 <= water_saturation < 1:
        raise ValueError("Water saturation must be at least zero and less than one.")

    pore_volume = area_acres * net_pay_ft * porosity * (1 - water_saturation)
    if not math.isfinite(pore_volume):
        raise ValueError("Calculated hydrocarbon pore volume must be finite.")
    return pore_volume


def calculate_volumetric_ogip(
    area_acres: float,
    net_pay_ft: float,
    porosity: float,
    water_saturation: float,
    gas_fvf_ft3_scf: float,
) -> float:
    """Calculate volumetric OGIP in MMscf from field-unit reservoir inputs.

    Converts hydrocarbon pore volume from acre-feet to cubic feet, divides by
    gas FVF in ft^3/scf, then converts scf to MMscf.
    """
    pore_volume_ac_ft = _hydrocarbon_pore_volume_ac_ft(
        area_acres, net_pay_ft, porosity, water_saturation
    )
    if not math.isfinite(gas_fvf_ft3_scf) or gas_fvf_ft3_scf <= 0:
        raise ValueError("Gas FVF must be finite and positive in ft^3/scf.")

    ogip_mmscf = pore_volume_ac_ft * 43_560.0 / gas_fvf_ft3_scf / 1_000_000.0
    if not math.isfinite(ogip_mmscf):
        raise ValueError("Calculated OGIP must be finite.")
    return float(ogip_mmscf)


def calculate_volumetric_stoiip(
    area_acres: float,
    net_pay_ft: float,
    porosity: float,
    water_saturation: float,
    oil_fvf_rb_stb: float,
) -> float:
    """Calculate volumetric STOIIP in MMstb from field-unit reservoir inputs.

    Converts hydrocarbon pore volume from acre-feet to reservoir barrels,
    divides by oil FVF in rb/STB, then converts STB to MMstb.
    """
    pore_volume_ac_ft = _hydrocarbon_pore_volume_ac_ft(
        area_acres, net_pay_ft, porosity, water_saturation
    )
    if not math.isfinite(oil_fvf_rb_stb) or oil_fvf_rb_stb <= 0:
        raise ValueError("Oil FVF must be finite and positive in rb/STB.")

    reservoir_volume_rb = pore_volume_ac_ft * 7_758.367
    stoiip_mmstb = reservoir_volume_rb / oil_fvf_rb_stb / 1_000_000.0
    if not math.isfinite(stoiip_mmstb):
        raise ValueError("Calculated STOIIP must be finite.")
    return float(stoiip_mmstb)


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
        raise ValueError(f"Unphysical Z-factor calculated: {zi}")

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

    if any(x < 0 for x in gp) or any(y <= 0 for y in pz):
        raise ValueError("Cumulative production Gp must be non-negative and P/Z must be strictly positive.")

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
