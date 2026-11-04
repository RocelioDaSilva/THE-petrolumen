"""Solver helpers."""
from scipy.optimize import brentq

def solve_scalar(f, lo: float, hi: float, tol: float = 1e-10) -> float:
    return brentq(f, lo, hi, xtol=tol)
