"""Thermodynamic PVT correlations for black oil and natural gas.

Kept local (do NOT delegate without accepting a numerical change):
  * ``pseudocritical_properties`` — ppes.ch02 uses different Sutton-style
    constants. At gamma_g=0.65: local (670.13, 365.11) vs ppes
    (671.44, 370.26).
  * ``calculate_z_factor_hall_yarborough`` — consequence of the above:
    at P=5000 psia, T=180F, gamma_g=0.65 local Z=0.9965 vs ppes Z=0.9918.
  * ``calculate_bubble_point_standing`` — exact analytic inverse of
    Standing's Rs; numerically inverting ppes.rs_standing would be worse
    (round-trip error 0.04% via the current closed form).

Delegated to ppes_bridge:
  * ``calculate_oil_fvf_standing`` -> ``bo_standing`` (identical to 4 dp
    at parity inputs: 1.2672 vs 1.2672383...).
"""
from __future__ import annotations

import math

from app.engines.reservoir.ppes_bridge import bo_standing as _bo_ppes


def pseudocritical_properties(gamma_g: float) -> tuple[float, float]:
    """Sutton pseudocritical P/T. Kept local — see module docstring."""
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
    """Hall-Yarborough Z rounded to four decimals for backward compatibility."""
    return round(
        calculate_z_factor_hall_yarborough_unrounded(
            pressure_psia, temperature_f, gamma_g
        ),
        4,
    )


def calculate_z_factor_hall_yarborough_unrounded(
    pressure_psia: float,
    temperature_f: float,
    gamma_g: float,
) -> float:
    """Return full-precision Hall-Yarborough Z for derivative calculations."""
    if not math.isfinite(pressure_psia) or pressure_psia <= 0:
        raise ValueError(
            f"Pressure must be a positive finite value (psia), got {pressure_psia}"
        )
    if not math.isfinite(temperature_f) or temperature_f <= -459.67:
        raise ValueError(
            f"Temperature must be finite and above absolute zero (-459.67 F), "
            f"got {temperature_f}"
        )
    if not math.isfinite(gamma_g) or gamma_g <= 0:
        raise ValueError(
            f"Gas gravity must be a positive finite value, got {gamma_g}"
        )

    ppc, tpc = pseudocritical_properties(gamma_g)
    temp_r = temperature_f + 459.67
    pr = pressure_psia / ppc
    tr = temp_r / tpc

    t = 1.0 / tr
    a = 0.06125 * t * math.exp(-1.2 * (1.0 - t) ** 2)
    b = t * (14.76 - 9.76 * t + 4.58 * (t ** 2))
    c = t * (90.7 - 242.2 * t + 42.4 * (t ** 2))
    d = 2.18 + 2.82 * t

    y = 0.001
    converged = False
    f = 0.0
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
            converged = True
            break
        y = max(1e-6, min(0.99, y_next))

    if not converged and abs(f) > 1e-4:
        raise RuntimeError(
            f"Hall-Yarborough Z-factor iteration failed to converge for "
            f"P={pressure_psia} psia, T={temperature_f} F, gamma_g={gamma_g}"
        )

    z = (a * pr) / max(y, 1e-6)
    if z <= 0.0 or not math.isfinite(z):
        raise RuntimeError(f"Unphysical Z-factor calculated: {z}")
    return float(z)


def calculate_bubble_point_standing(
    rs_scf_stb: float,
    gamma_g: float,
    api: float,
    temperature_f: float,
) -> float:
    """Standing Pb — exact analytic inverse of Standing's Rs. Kept local."""
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
    """Standing Bo, delegated to ppes_bridge.bo_standing (single source of truth)."""
    if rs_scf_stb < 0:
        raise ValueError(f"Solution GOR must be non-negative, got {rs_scf_stb}")
    if gamma_g <= 0:
        raise ValueError(f"Gas gravity must be positive, got {gamma_g}")
    if gamma_o <= 0:
        raise ValueError(f"Oil gravity must be positive, got {gamma_o}")
    if temperature_f <= -459.67:
        raise ValueError(f"Temperature must be above absolute zero, got {temperature_f}")

    api = 141.5 / gamma_o - 131.5
    return round(float(_bo_ppes(temperature_f, api, rs_scf_stb, gamma_g)), 4)