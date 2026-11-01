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

    Raises:
        ValueError: If qi < 0, di < 0, or any t < 0.
    """
    if qi < 0:
        raise ValueError(f"Initial production rate qi must be non-negative, got {qi}")
    if di < 0:
        raise ValueError(f"Decline rate di must be non-negative, got {di}")
    if np.any(np.asarray(t) < 0):
        raise ValueError("Time t cannot be negative.")
    return qi * np.exp(-di * t)


def hyperbolic(t: float | np.ndarray, qi: float, di: float, b: float) -> float | np.ndarray:
    """Hyperbolic decline curve model: q(t) = qi / (1 + b * di * t)^(1 / b).

    Args:
        t: Time array or scalar
        qi: Initial production rate
        di: Initial nominal decline rate
        b: Hyperbolic b-exponent (b >= 0)

    Returns:
        Production rate at time t

    Raises:
        ValueError: If qi < 0, di < 0, b < 0, any t < 0, or if denominator <= 0.
    """
    if qi < 0:
        raise ValueError(f"Initial production rate qi must be non-negative, got {qi}")
    if di < 0:
        raise ValueError(f"Decline rate di must be non-negative, got {di}")
    if b < 0:
        raise ValueError(f"Hyperbolic exponent b must be non-negative, got {b}")
    if np.any(np.asarray(t) < 0):
        raise ValueError("Time t cannot be negative.")

    if b == 0:
        return exponential(t, qi, di)

    base = 1.0 + b * di * t
    if np.any(np.asarray(base) <= 0):
        raise ValueError("Non-positive base (1 + b * di * t) encountered in hyperbolic decline.")

    return qi / (base ** (1.0 / b))


def harmonic(t: float | np.ndarray, qi: float, di: float) -> float | np.ndarray:
    """Harmonic decline curve model: q(t) = qi / (1 + di * t).

    Args:
        t: Time array or scalar
        qi: Initial production rate
        di: Initial nominal decline rate

    Returns:
        Production rate at time t

    Raises:
        ValueError: If qi < 0, di < 0, any t < 0, or denominator <= 0.
    """
    if qi < 0:
        raise ValueError(f"Initial production rate qi must be non-negative, got {qi}")
    if di < 0:
        raise ValueError(f"Decline rate di must be non-negative, got {di}")
    if np.any(np.asarray(t) < 0):
        raise ValueError("Time t cannot be negative.")

    denom = 1.0 + di * t
    if np.any(np.asarray(denom) <= 0):
        raise ValueError("Non-positive denominator (1 + di * t) encountered in harmonic decline.")

    return qi / denom
