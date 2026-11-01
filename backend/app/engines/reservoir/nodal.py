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
    if pr <= 0:
        raise ValueError("Reservoir pressure pr must be strictly positive.")
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
    """

    def residual(q: float) -> float:
        pwf = pr - tpr(q, a=a, b=b)
        return float(ipr_vogel(q, qi, pr, pwf) - q)

    return float(brentq(residual, 1.0, qi))
