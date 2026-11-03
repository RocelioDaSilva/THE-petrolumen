"""Arps Decline Curve Analysis (DCA) models."""

from __future__ import annotations

import numpy as np
from scipy.optimize import curve_fit


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


def fit_arps(
    time: np.ndarray,
    rate: np.ndarray,
    method: str = "hyperbolic",
) -> dict[str, float | str]:
    """Fit an Arps decline model and return its parameters."""
    time = np.asarray(time, dtype=float)
    rate = np.asarray(rate, dtype=float)
    if time.ndim != 1 or rate.ndim != 1 or time.shape != rate.shape or time.size < 2:
        raise ValueError("time and rate must be equal-length one-dimensional arrays with at least two samples.")
    if not np.all(np.isfinite(time)) or not np.all(np.isfinite(rate)):
        raise ValueError("time and rate must contain only finite values.")
    if np.any(time < 0) or np.any(rate < 0):
        raise ValueError("time and rate values must be non-negative.")
    if method not in {"exponential", "harmonic", "hyperbolic"}:
        raise ValueError(f"Unsupported Arps decline method: {method}")

    qi = float(np.max(rate))
    if method == "exponential":
        parameters, _ = curve_fit(
            exponential, time, rate, p0=[qi, 0.1], bounds=([0.0, 0.0], [np.inf, np.inf])
        )
        fitted_qi, di = parameters
        b = 0.0
    elif method == "harmonic":
        parameters, _ = curve_fit(
            harmonic, time, rate, p0=[qi, 0.1], bounds=([0.0, 0.0], [np.inf, np.inf])
        )
        fitted_qi, di = parameters
        b = 1.0
    else:
        def hyperbolic_fit(t, initial_rate, decline_rate, exponent):
            if exponent <= 1e-8:
                return exponential(t, initial_rate, decline_rate)
            return hyperbolic(t, initial_rate, decline_rate, exponent)

        parameters, _ = curve_fit(
            hyperbolic_fit,
            time,
            rate,
            p0=[qi, 0.1, 0.5],
            bounds=([0.0, 0.0, 0.0], [np.inf, np.inf, 2.0]),
            maxfev=10000,
        )
        fitted_qi, di, b = parameters

    return {
        "qi": float(fitted_qi),
        "di": float(di),
        "b": float(b),
        "method": method,
    }


def forecast_production(
    params: dict[str, float | str],
    time: float | np.ndarray,
) -> float | np.ndarray:
    """Evaluate an Arps model from fitted parameters."""
    method = params.get("method")
    qi = float(params["qi"])
    di = float(params["di"])
    if method == "exponential":
        return exponential(time, qi, di)
    if method == "harmonic":
        return harmonic(time, qi, di)
    if method == "hyperbolic":
        return hyperbolic(time, qi, di, float(params["b"]))
    raise ValueError(f"Unsupported Arps decline method: {method}")


def calculate_eur(
    params: dict[str, float | str],
    economic_limit: float,
) -> float:
    """Integrate the Arps decline curve to its economic production limit."""
    qi = float(params["qi"])
    di = float(params["di"])
    method = params.get("method")
    if not np.isfinite(qi) or qi < 0 or economic_limit <= 0 or not np.isfinite(economic_limit):
        raise ValueError("Initial rate must be non-negative and economic_limit must be finite and positive.")
    if di <= 0 or not np.isfinite(di):
        raise ValueError("Decline rate must be finite and positive to calculate finite EUR.")
    if economic_limit >= qi:
        return 0.0

    ratio = economic_limit / qi
    if method == "exponential":
        return float(qi / di * (1.0 - ratio))
    if method == "harmonic":
        return float(qi / di * np.log(qi / economic_limit))
    if method == "hyperbolic":
        b = float(params["b"])
        if b < 0 or not np.isfinite(b):
            raise ValueError("Hyperbolic exponent must be finite and non-negative.")
        if b <= 1e-8:
            return float(qi / di * (1.0 - ratio))
        if abs(b - 1.0) <= 1e-8:
            return float(qi / di * np.log(qi / economic_limit))
        return float(qi / (di * (1.0 - b)) * (1.0 - ratio ** (1.0 - b)))
    raise ValueError(f"Unsupported Arps decline method: {method}")


def calculate_remaining_life(
    params: dict[str, float | str],
    current_rate: float,
    economic_limit: float,
) -> float:
    """Calculate time until the modeled rate reaches the economic limit."""
    di = float(params["di"])
    qi = float(params["qi"])
    if (
        not np.isfinite(qi)
        or qi <= 0
        or current_rate <= 0
        or economic_limit <= 0
        or not np.isfinite(current_rate + economic_limit)
    ):
        raise ValueError("Current rate and economic_limit must be finite and positive.")
    if current_rate > qi:
        raise ValueError("Current rate cannot exceed the fitted initial rate.")
    if di <= 0 or not np.isfinite(di):
        raise ValueError("Decline rate must be finite and positive to calculate remaining life.")
    if current_rate <= economic_limit:
        return 0.0

    method = params.get("method")
    ratio = current_rate / economic_limit
    if method == "exponential":
        return float(np.log(ratio) / di)
    if method == "harmonic":
        return float(qi / di * (1.0 / economic_limit - 1.0 / current_rate))
    if method == "hyperbolic":
        b = float(params["b"])
        if b < 0 or not np.isfinite(b):
            raise ValueError("Hyperbolic exponent must be finite and non-negative.")
        if b <= 1e-8:
            return float(np.log(ratio) / di)
        return float(
            ((qi / economic_limit) ** b - (qi / current_rate) ** b)
            / (b * di)
        )
    raise ValueError(f"Unsupported Arps decline method: {method}")
