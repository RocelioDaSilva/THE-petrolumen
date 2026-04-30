import numpy as np
import scipy.optimize as opt
from typing import Dict, List, Tuple, Callable


def arps_exponential(t: np.ndarray, qi: float, di: float) -> np.ndarray:
    return qi * np.exp(-di * t)


def arps_hyperbolic(t: np.ndarray, qi: float, di: float, b: float) -> np.ndarray:
    return qi / (1 + b * di * t) ** (1 / b)


def arps_harmonic(t: np.ndarray, qi: float, di: float) -> np.ndarray:
    return qi / (1 + di * t)


def duong_model(t: np.ndarray, q1: float, a: float, m: float) -> np.ndarray:
    # t must be > 0. Usually t starting at 1.
    return q1 * t**-m * np.exp(a / (1 - m) * (t ** (1 - m) - 1))


def ple_model(
    t: np.ndarray, qi: float, di: float, d_inf: float, n: float
) -> np.ndarray:
    return qi * np.exp(-d_inf * t - di * t**n)


def sepd_model(t: np.ndarray, qi: float, tau: float, n: float) -> np.ndarray:
    return qi * np.exp(-((t / tau) ** n))


def lgm_model(t: np.ndarray, K: float, a: float, b: float) -> np.ndarray:
    return (K * a * b * np.exp(-a * t)) / (1 + b * np.exp(-a * t)) ** 2


def perform_arps_fit(time: np.ndarray, rate: np.ndarray) -> Dict:
    # Try hyperbolic, which generalizes to exp (b=0) and harmonic (b=1)
    try:
        popt, _ = opt.curve_fit(
            arps_hyperbolic,
            time,
            rate,
            p0=[rate[0], 0.1, 0.5],
            bounds=(0, [np.inf, np.inf, 2.0]),
        )
        qi, di, b = popt
        forecast = arps_hyperbolic(time, qi, di, b)
        r2 = 1 - np.sum((rate - forecast) ** 2) / np.sum((rate - np.mean(rate)) ** 2)
        return {
            "parameters": {"qi": qi, "di": di, "b": b},
            "r_squared": r2,
            "model": "hyperbolic",
        }
    except:
        return {"error": "Fitting failed"}


def perform_duong_fit(time: np.ndarray, rate: np.ndarray) -> Dict:
    # time should be 1-based or shifted
    t = time + 1 if time[0] == 0 else time
    try:
        popt, _ = opt.curve_fit(duong_model, t, rate, p0=[rate[0], 1.0, 1.1])
        q1, a, m = popt
        forecast = duong_model(t, q1, a, m)
        r2 = 1 - np.sum((rate - forecast) ** 2) / np.sum((rate - np.mean(rate)) ** 2)
        return {
            "parameters": {"q1": q1, "a": a, "m": m},
            "r_squared": r2,
            "model": "Duong",
        }
    except:
        return {"error": "Fitting failed"}
