"""Arps Decline Curve Analysis (DCA) models."""

from __future__ import annotations

import numpy as np


def exponential(t: float | np.ndarray, qi: float, di: float) -> float | np.ndarray:
    """Exponential decline curve model: q(t) = qi * exp(-di * t).

    Args:
        t: Time array or scalar
        qi: Initial production rate
        di: Nominal decline rate

    Returns:
        Production rate at time t
    """
    return qi * np.exp(-di * t)


def hyperbolic(t: float | np.ndarray, qi: float, di: float, b: float) -> float | np.ndarray:
    """Hyperbolic decline curve model: q(t) = qi / (1 + b * di * t)^(1 / b).

    Args:
        t: Time array or scalar
        qi: Initial production rate
        di: Initial nominal decline rate
        b: Hyperbolic b-exponent (0 < b < 1)

    Returns:
        Production rate at time t
    """
    if b == 0:
        return exponential(t, qi, di)
    return qi / ((1.0 + b * di * t) ** (1.0 / b))


def harmonic(t: float | np.ndarray, qi: float, di: float) -> float | np.ndarray:
    """Harmonic decline curve model: q(t) = qi / (1 + di * t).

    Args:
        t: Time array or scalar
        qi: Initial production rate
        di: Initial nominal decline rate

    Returns:
        Production rate at time t
    """
    return qi / (1.0 + di * t)
