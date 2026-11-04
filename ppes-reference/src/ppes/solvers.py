"""Solver helpers for the book's implicit equations.

The book requires Newtonâ€“Raphson on several equations (z-factor,
bottomhole pressure, nodal analysis, gas-lift valve spacing). Where the
book can bracket the root, we use scipy.optimize.brentq for robustness.
"""
from __future__ import annotations
from scipy.optimize import brentq


def solve_scalar(f, lo: float, hi: float, tol: float = 1e-10) -> float:
    """Robust bracketed scalar solve (brentq)."""
    return brentq(f, lo, hi, xtol=tol)