"""Gas isothermal compressibility.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 1, Sec. 5.5, pp. 24-26, Eq. (1.19) and Example 1.4.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

# Derivative step-size policy: h = max(REL_STEP * p, ABS_STEP_PSI)
REL_STEP = 1.0e-3        # dimensionless
ABS_STEP_PSI = 0.5       # psi
MIN_T_F = -459.67        # deg F, absolute zero


@dataclass(frozen=True)
class GasCompressibilityResult:
    cg_psi_inv: float
    z_at_p: float
    dz_dp_psi_inv: float


def gas_compressibility_from_z_curve(
    p_psia: float,
    z_func: Callable[[float], float],
    z_at_p: float | None = None,
    h_psi: float | None = None,
) -> GasCompressibilityResult:
    """Return gas isothermal compressibility via Eq. (1.19).

    Implements cg = 1/p - (1/z)(dz/dp) at fixed T (Craft, Hawkins, Terry
    1991, Ch. 1, Sec. 5.5, p. 24). The isothermal derivative dz/dp is
    computed by central finite difference of the caller-supplied z(p)
    callable; near p = 0 the routine falls back to forward difference.

    Args:
        p_psia: Pressure in psia. Must be > 0.
        z_func: Callable p -> z, gas deviation factor.
        z_at_p: Optional precomputed z(p); if None, z_func(p) is called.
        h_psi: Optional derivative step in psi; if None, uses
            max(REL_STEP*p, ABS_STEP_PSI).

    Returns:
        GasCompressibilityResult(cg_psi_inv, z_at_p, dz_dp_psi_inv).

    Raises:
        ValueError: if p_psia <= 0, h_psi <= 0, or z at p is non-positive.
    """
    if not (p_psia > 0.0):
        raise ValueError(f"p_psia must be > 0, got {p_psia!r}")

    z = float(z_at_p) if z_at_p is not None else float(z_func(p_psia))
    if not (z > 0.0):
        raise ValueError(f"z at p must be > 0, got {z!r}")

    if h_psi is None:
        h = max(REL_STEP * p_psia, ABS_STEP_PSI)
    else:
        h = float(h_psi)
        if not (h > 0.0):
            raise ValueError(f"h_psi must be > 0, got {h_psi!r}")

    # Eq. (1.19): cg = 1/p - (1/z)(dz/dp) at constant T.
    # Central difference when both neighbours are physically valid,
    # forward difference otherwise (near zero pressure).
    if p_psia - h > 0.0:
        z_plus = float(z_func(p_psia + h))
        z_minus = float(z_func(p_psia - h))
        dz_dp = (z_plus - z_minus) / (2.0 * h)
    else:
        z_plus = float(z_func(p_psia + h))
        dz_dp = (z_plus - z) / h

    cg = 1.0 / p_psia - (1.0 / z) * dz_dp
    return GasCompressibilityResult(
        cg_psi_inv=cg, z_at_p=z, dz_dp_psi_inv=dz_dp,
    )


def gas_compressibility(
    p_psia: float,
    T_F: float,
    gas_sg: float,
    z_at_p: float | None = None,
) -> GasCompressibilityResult:
    """High-level wrapper using the project's z-factor correlation.

    Args:
        p_psia: Pressure in psia. Must be > 0.
        T_F: Temperature in degrees Fahrenheit. Must be > -459.67.
        gas_sg: Gas specific gravity (air = 1). Must be in (0, 2).
        z_at_p: Optional precomputed z(p).

    Returns:
        GasCompressibilityResult.

    Raises:
        ValueError: any of p_psia, T_F, gas_sg out of range.
    """
    if not (p_psia > 0.0):
        raise ValueError(f"p_psia must be > 0, got {p_psia!r}")
    if not (T_F > MIN_T_F):
        raise ValueError(f"T_F must be above {MIN_T_F} deg F, got {T_F!r}")
    if not (0.0 < gas_sg < 2.0):
        raise ValueError(f"gas_sg must be in (0, 2), got {gas_sg!r}")

    # Lazy import: keeps the low-level routine testable without the
    # project z-factor module. Replace the module path if the existing
    # project z-factor helper lives elsewhere.
    from app.reservoir.gas_z_factor import z_factor

    return gas_compressibility_from_z_curve(
        p_psia=p_psia,
        z_func=lambda p: z_factor(p, T_F, gas_sg),
        z_at_p=z_at_p,
    )
