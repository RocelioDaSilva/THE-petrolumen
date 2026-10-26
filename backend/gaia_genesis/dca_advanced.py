import numpy as np
import scipy.optimize as opt
from typing import Dict


def arps_exponential(t: np.ndarray, qi: float, di: float) -> np.ndarray:
    return qi * np.exp(-di * t)


def arps_hyperbolic(t: np.ndarray, qi: float, di: float, b: float) -> np.ndarray:
    if abs(b) < 1e-6:
        return arps_exponential(t, qi, di)
    denom = 1 + b * di * t
    denom = np.where(denom <= 0, 1e-12, denom)
    return qi / (denom ** (1 / b))


def arps_harmonic(t: np.ndarray, qi: float, di: float) -> np.ndarray:
    denom = 1 + di * t
    denom = np.where(denom <= 0, 1e-12, denom)
    return qi / denom


def duong_model(t: np.ndarray, q1: float, a: float, m: float) -> np.ndarray:
    if abs(1 - m) < 1e-6:
        m = 1.0 - 1e-6
    t_safe = np.where(t <= 0, 1e-12, t)
    return q1 * (t_safe ** -m) * np.exp((a / (1 - m)) * (t_safe ** (1 - m) - 1))


def ple_model(
    t: np.ndarray, qi: float, di: float, d_inf: float, n: float
) -> np.ndarray:
    return qi * np.exp(-d_inf * t - di * t**n)


def sepd_model(t: np.ndarray, qi: float, tau: float, n: float) -> np.ndarray:
    return qi * np.exp(-((t / tau) ** n))


def lgm_model(t: np.ndarray, K: float, a: float, b: float) -> np.ndarray:
    return (K * a * b * np.exp(-a * t)) / (1 + b * np.exp(-a * t)) ** 2


def _calc_r2(rate: np.ndarray, forecast: np.ndarray) -> float:
    ss_tot = float(np.sum((rate - np.mean(rate)) ** 2))
    if ss_tot < 1e-12:
        return 1.0 if np.allclose(rate, forecast, atol=1e-6) else 0.0
    return float(1.0 - np.sum((rate - forecast) ** 2) / ss_tot)


def perform_arps_fit(time: np.ndarray, rate: np.ndarray) -> Dict:
    if len(rate) == 0:
        return {"error": "Fitting failed"}
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
        r2 = _calc_r2(rate, forecast)
        return {
            "parameters": {"qi": qi, "di": di, "b": b},
            "r_squared": r2,
            "model": "hyperbolic",
        }
    except Exception:
        return {"error": "Fitting failed"}


def perform_ple_fit(time: np.ndarray, rate: np.ndarray) -> Dict:
    if len(rate) == 0:
        return {"error": "Fitting failed"}
    try:
        popt, _ = opt.curve_fit(
            ple_model, time, rate, p0=[rate[0], 0.1, 0.01, 0.5], bounds=(0, np.inf)
        )
        qi, di, d_inf, n = popt
        forecast = ple_model(time, qi, di, d_inf, n)
        r2 = _calc_r2(rate, forecast)
        return {
            "parameters": {"qi": qi, "di": di, "d_inf": d_inf, "n": n},
            "r_squared": r2,
            "model": "PLE",
        }
    except Exception:
        return {"error": "Fitting failed"}


def perform_sepd_fit(time: np.ndarray, rate: np.ndarray) -> Dict:
    if len(rate) == 0:
        return {"error": "Fitting failed"}
    try:
        popt, _ = opt.curve_fit(
            sepd_model, time, rate, p0=[rate[0], 100, 0.5], bounds=(0, np.inf)
        )
        qi, tau, n = popt
        forecast = sepd_model(time, qi, tau, n)
        r2 = _calc_r2(rate, forecast)
        return {
            "parameters": {"qi": qi, "tau": tau, "n": n},
            "r_squared": r2,
            "model": "SEPD",
        }
    except Exception:
        return {"error": "Fitting failed"}


def perform_duong_fit(time: np.ndarray, rate: np.ndarray) -> Dict:
    if len(rate) == 0 or len(time) == 0:
        return {"error": "Fitting failed"}
    # time should be 1-based or shifted
    t = time + 1 if time[0] == 0 else time
    try:
        popt, _ = opt.curve_fit(duong_model, t, rate, p0=[rate[0], 1.0, 1.1])
        q1, a, m = popt
        forecast = duong_model(t, q1, a, m)
        r2 = _calc_r2(rate, forecast)
        return {
            "parameters": {"q1": q1, "a": a, "m": m},
            "r_squared": r2,
            "model": "Duong",
        }
    except Exception:
        return {"error": "Fitting failed"}
