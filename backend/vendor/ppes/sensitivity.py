"""Sensitivity and Monte Carlo."""
from dataclasses import dataclass
from typing import Callable
import numpy as np
import pandas as pd

@dataclass
class Parameter:
    name: str
    nominal: float
    low: float
    high: float
    distribution: str = "uniform"

def one_at_a_time(func, base_params, params, n_points=10):
    rows = []
    for p in params:
        for v in np.linspace(p.low, p.high, n_points):
            a = dict(base_params); a[p.name] = v
            try: r = func(**a)
            except Exception: r = np.nan
            rows.append({"parameter": p.name, "value": v, "result": r})
    return pd.DataFrame(rows)

def monte_carlo(func, params, n_samples=1000, seed=42):
    rng = np.random.default_rng(seed)
    samples = {}
    for p in params:
        if p.distribution == "uniform":
            samples[p.name] = rng.uniform(p.low, p.high, n_samples)
        elif p.distribution == "triangular":
            samples[p.name] = rng.triangular(p.low, p.nominal,
                                             p.high, n_samples)
        elif p.distribution == "normal":
            sigma = (p.high - p.low)/6.0
            samples[p.name] = rng.normal(p.nominal, sigma, n_samples)
    results = np.array([func(**{k: samples[k][i] for k in samples})
                        for i in range(n_samples)])
    return {"results": results,
            "p10": float(np.percentile(results, 10)),
            "p50": float(np.percentile(results, 50)),
            "p90": float(np.percentile(results, 90)),
            "mean": float(results.mean()),
            "std": float(results.std())}
