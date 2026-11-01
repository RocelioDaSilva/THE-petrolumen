"""Thermodynamic PVT correlations for black oil and natural gas."""

from __future__ import annotations

import math


def pseudocritical_properties(gamma_g: float) -> tuple[float, float]:
    """Calculate pseudocritical pressure (Ppc) and temperature (Tpc) using Sutton correlations.

    Equations:
        Ppc = 756.8 - 131.0 * gamma_g - 3.6 * gamma_g^2  (psia)
        Tpc = 169.2 + 349.5 * gamma_g - 74.0 * gamma_g^2  (°R)

    Parameters:
        gamma_g: Gas specific gravity relative to air (air = 1.0).

    Returns:
        tuple containing (ppc_psia, tpc_rankine).

    Raises:
        ValueError: If gas gravity is non-positive.
    """
    if gamma_g <= 0:
        raise ValueError(f"Gas specific gravity must be positive, got {gamma_g}")

    ppc = 756.8 - 131.0 * gamma_g - 3.6 * (gamma_g ** 2)
    tpc = 169.2 + 349.5 * gamma_g - 74.0 * (gamma_g ** 2)
    return round(ppc, 2), round(tpc, 2)


def calculate_z_factor_hall_yarborough(
    pressure_psia: float,
    temperature_f: float,
    gamma_g: float,
) -> float:
    """Calculate natural gas compressibility factor Z using Hall-Yarborough EOS.

    Parameters:
        pressure_psia: Pressure in psia.
        temperature_f: Temperature in °F.
        gamma_g: Gas specific gravity.

    Returns:
        Gas compressibility factor Z (dimensionless).

    Raises:
        ValueError: On unphysical pressure, temperature, or gas gravity.
    """
    if pressure_psia <= 0:
        raise ValueError(f"Pressure must be strictly positive (psia), got {pressure_psia}")
    if temperature_f <= -459.67:
        raise ValueError(f"Temperature must be above absolute zero (-459.67 °F), got {temperature_f}")
    if gamma_g <= 0:
        raise ValueError(f"Gas gravity must be positive, got {gamma_g}")

    ppc, tpc = pseudocritical_properties(gamma_g)
    temp_r = temperature_f + 459.67

    pr = pressure_psia / ppc
    tr = temp_r / tpc

    t = 1.0 / tr
    a = 0.06125 * t * math.exp(-1.2 * (1.0 - t) ** 2)
    b = t * (14.76 - 9.76 * t + 4.58 * (t ** 2))
    c = t * (90.7 - 242.2 * t + 42.4 * (t ** 2))
    d = 2.18 + 2.82 * t

    # Newton-Raphson to solve for reduced density Y
    y = 0.001
    for _ in range(100):
        y2 = y * y
        y3 = y2 * y
        y4 = y3 * y
        denom = (1.0 - y) ** 3
        denom2 = (1.0 - y) ** 4

        f = -a * pr + (y + y2 + y3 - y4) / denom - b * y2 + c * (y ** d)
        df = ((1.0 + 4.0 * y + 4.0 * y2 - 4.0 * y3 + y4) / denom2) - 2.0 * b * y + c * d * (y ** (d - 1.0))

        if abs(df) < 1e-12:
            break
        y_next = y - f / df
        if abs(y_next - y) < 1e-6:
            y = y_next
            break
        y = max(1e-6, min(0.99, y_next))

    z = (a * pr) / max(y, 1e-6)
    return round(float(z), 4)


def calculate_bubble_point_standing(
    rs_scf_stb: float,
    gamma_g: float,
    api: float,
    temperature_f: float,
) -> float:
    """Calculate bubble point pressure Pb (psia) using Standing's correlation.

    Equation:
        Pb = 18.2 * ((Rs / gamma_g)^0.83 * 10^(0.00091 * T - 0.0125 * API) - 1.4)

    Parameters:
        rs_scf_stb: Solution gas-oil ratio at bubble point (scf/STB).
        gamma_g: Gas specific gravity (air=1.0).
        api: Oil API gravity.
        temperature_f: Reservoir temperature (°F).

    Returns:
        Bubble point pressure Pb in psia.

    Raises:
        ValueError: If Rs, gamma_g, or API are non-physical.
    """
    if rs_scf_stb < 0:
        raise ValueError(f"Solution GOR must be non-negative, got {rs_scf_stb}")
    if gamma_g <= 0:
        raise ValueError(f"Gas gravity must be positive, got {gamma_g}")
    if api <= 0:
        raise ValueError(f"API gravity must be positive, got {api}")
    if temperature_f <= -459.67:
        raise ValueError(f"Temperature must be above absolute zero, got {temperature_f}")

    term = ((rs_scf_stb / gamma_g) ** 0.83) * (10.0 ** (0.00091 * temperature_f - 0.0125 * api))
    pb = 18.2 * (term - 1.4)
    return round(max(14.7, float(pb)), 2)


def calculate_oil_fvf_standing(
    rs_scf_stb: float,
    gamma_g: float,
    gamma_o: float,
    temperature_f: float,
) -> float:
    """Calculate oil formation volume factor Bo (rb/STB) using Standing's correlation.

    Equation:
        Bo = 0.9759 + 0.000120 * [Rs * (gamma_g / gamma_o)^0.5 + 1.25 * T]^1.2

    Parameters:
        rs_scf_stb: Solution gas-oil ratio (scf/STB).
        gamma_g: Gas specific gravity.
        gamma_o: Oil specific gravity (water=1.0).
        temperature_f: Reservoir temperature (°F).

    Returns:
        Oil formation volume factor Bo (bbl/STB).
    """
    if rs_scf_stb < 0 or gamma_g <= 0 or gamma_o <= 0:
        raise ValueError("Invalid negative or zero fluid properties.")

    inside = rs_scf_stb * ((gamma_g / gamma_o) ** 0.5) + 1.25 * temperature_f
    bo = 0.9759 + 0.000120 * (max(0.0, inside) ** 1.2)
    return round(float(bo), 4)
