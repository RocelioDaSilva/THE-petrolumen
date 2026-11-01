"""Nodal analysis calculations for inflow performance (IPR) and tubing performance (TPR)."""

from __future__ import annotations

import numpy as np
from scipy.optimize import brentq


def ipr_vogel(q: float | np.ndarray, qi: float, pr: float, pwf: float | np.ndarray) -> float | np.ndarray:
    """Vogel Inflow Performance Relationship (IPR) for saturated oil reservoirs.

    q / q_max = 1 - 0.2 * (pwf / pr) - 0.8 * (pwf / pr)^2

    Args:
        q: Current rate placeholder or ignored if calculating direct rate
        qi: Maximum open-flow rate (q_max) at pwf = 0
        pr: Average reservoir static pressure
        pwf: Flowing bottom-hole pressure

    Returns:
        Flow rate q calculated from pwf
    """
    if qi < 0:
        raise ValueError(f"Open-flow rate qi must be non-negative, got {qi}")
    if pr <= 0:
        raise ValueError("Reservoir pressure pr must be strictly positive.")
    if np.any(np.asarray(pwf) < 0):
        raise ValueError("Flowing bottom-hole pressure pwf cannot be negative.")
    ratio = pwf / pr
    return qi * (1.0 - 0.2 * ratio - 0.8 * (ratio**2))


def tpr(q: float | np.ndarray, a: float = 0.002, b: float = 10.0) -> float | np.ndarray:
    """Tubing Performance Relationship (TPR) quadratic pressure loss approximation.

    P_drop = a * q^2 + b * q

    Args:
        q: Flow rate
        a: Quadratic loss coefficient
        b: Linear loss coefficient

    Returns:
        Pressure drop across the tubing
    """
    if a < 0 or b < 0:
        raise ValueError(f"Tubing loss coefficients must be non-negative, got a={a}, b={b}")
    return a * (q**2) + b * q


def find_operating_point(
    qi: float,
    pr: float,
    p_surf: float = 1000.0,
    a: float = 0.002,
    b: float = 10.0,
) -> float:
    """Find equilibrium operating flow rate q_op where IPR equals TPR.

    Args:
        qi: Maximum open-hole flow rate (q_max)
        pr: Average reservoir pressure
        p_surf: Surface backpressure
        a: Quadratic tubing loss coefficient
        b: Linear tubing loss coefficient

    Returns:
        Equilibrium flow rate (q_op)

    Raises:
        ValueError: If parameters are unphysical or if no intersection exists.
    """
    if qi <= 0:
        raise ValueError(f"Maximum flow rate qi must be strictly positive, got {qi}")
    if pr <= 0:
        raise ValueError(f"Reservoir static pressure pr must be strictly positive, got {pr}")
    if p_surf < 0:
        raise ValueError(f"Surface backpressure p_surf cannot be negative, got {p_surf}")
    if a < 0 or b < 0:
        raise ValueError(f"Loss coefficients a and b must be non-negative, got a={a}, b={b}")
    if p_surf >= pr:
        raise ValueError(
            f"Surface backpressure ({p_surf}) is greater than or equal to reservoir pressure ({pr}); well cannot naturally flow."
        )

    def residual(q: float) -> float:
        # Tubing requires pwf = p_surf + delta_p_tubing
        pwf = p_surf + float(tpr(q, a=a, b=b))
        if pwf >= pr:
            # Well does not produce if required pwf exceeds reservoir pressure
            return -q
        return float(ipr_vogel(q, qi, pr, pwf) - q)

    f_low = residual(1e-5)
    f_high = residual(qi)

    if f_low * f_high > 0:
        raise ValueError(
            "No operating point intersection found between IPR and TPR curves within physical rate boundaries."
        )

    return float(brentq(residual, 1e-5, qi))
