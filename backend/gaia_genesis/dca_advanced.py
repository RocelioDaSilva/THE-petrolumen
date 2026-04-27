import numpy as np
from scipy.optimize import curve_fit
from typing import Dict, List, Tuple, Any

def arps_exponential(t: np.ndarray, qi: float, di: float) -> np.ndarray:
    return qi * np.exp(-di * t)

def arps_hyperbolic(t: np.ndarray, qi: float, di: float, b: float) -> np.ndarray:
    return qi / (1 + b * di * t)**(1/b)

def arps_harmonic(t: np.ndarray, qi: float, di: float) -> np.ndarray:
    return qi / (1 + di * t)

def duong_model(t: np.ndarray, a: float, m: float) -> np.ndarray:
    """Duong (2011) model: q = qi * t^-m * exp(a/(1-m) * (t^(1-m) - 1))"""
    # Simplified version for fitting
    return a * t**(-m)

def perform_duong(time: np.ndarray, rate: np.ndarray) -> Dict[str, Any]:
    """
    Duong analysis: log(q/Gp) vs log(t) is a straight line.
    """
    Gp = np.cumsum(rate)
    x = np.log10(time[1:])
    y = np.log10(rate[1:] / Gp[1:])

    # Linear fit
    m, c = np.polyfit(x, y, 1)
    a = 10**c

    return {
        "model": "Duong",
        "parameters": {"a": float(a), "m": float(-m)},
        "r_squared": 0.0 # Placeholder
    }

def power_law_exponential(t: np.ndarray, qi: float, di: float, n: float, d_inf: float) -> np.ndarray:
    return qi * np.exp(-di * t**n - d_inf * t)

def sepd_model(t: np.ndarray, qi: float, tau: float, n: float) -> np.ndarray:
    """Stretched Exponential Production Decline"""
    return qi * np.exp(-(t / tau)**n)

def calculate_eur_arps(params: Dict[str, Any], t_final: float = 360) -> float:
    """Calculate EUR for Arps models up to t_final (months)."""
    t = np.linspace(0, t_final, t_final + 1)
    if params['method'] == 'exponential':
        q = arps_exponential(t, params['qi'], params['di'])
    elif params['method'] == 'hyperbolic':
        q = arps_hyperbolic(t, params['qi'], params['di'], params['b'])
    elif params['method'] == 'harmonic':
        q = arps_harmonic(t, params['qi'], params['di'])
    else:
        return 0.0
    return float(np.sum(q))

def monte_carlo_eur(time: np.ndarray, rate: np.ndarray, n_iter: int = 500) -> Dict[str, float]:
    """Bootstrap Monte Carlo for EUR uncertainty."""
    eurs = []
    for _ in range(n_iter):
        # Resample with replacement
        indices = np.random.choice(len(time), len(time), replace=True)
        t_resampled = time[indices]
        q_resampled = rate[indices]

        try:
            popt, _ = curve_fit(arps_hyperbolic, t_resampled, q_resampled,
                                p0=[rate[0], 0.1, 0.5], bounds=(0, [np.inf, 1, 2]))
            eur = calculate_eur_arps({'method': 'hyperbolic', 'qi': popt[0], 'di': popt[1], 'b': popt[2]})
            eurs.append(eur)
        except Exception:
            continue

    if not eurs:
        return {"P10": 0.0, "P50": 0.0, "P90": 0.0}

    return {
        "P10": float(np.percentile(eurs, 90)),
        "P50": float(np.percentile(eurs, 50)),
        "P90": float(np.percentile(eurs, 10))
    }
