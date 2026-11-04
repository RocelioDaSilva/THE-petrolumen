"""Chapter 8 â€” Production Decline Analysis (pp. 8/97 â€“ 8/104)."""
from __future__ import annotations
import math


def exponential_rate(qi: float, b: float, t: float) -> float:
    """Eq. 8.16 (p. 8/98)."""
    return qi * math.exp(-b*t)


def exponential_cum(qi: float, b: float, t: float) -> float:
    """Eq. 8.18 (p. 8/99)."""
    return (qi / b) * (1 - math.exp(-b*t))


def exponential_b_from_ln(q1, q2, t1, t2) -> float:
    """Eq. 8.23 (p. 8/99)."""
    return math.log(q1/q2) / (t2 - t1)


def exponential_b_from_np(q1, q2, np1, np2) -> float:
    """Eq. 8.27 (p. 8/99)."""
    return (q1 - q2) / (np2 - np1)


def harmonic_rate(q0: float, b: float, t: float) -> float:
    """Eq. 8.32 (p. 8/100)."""
    return q0 / (1 + b*t)


def harmonic_cum(q0: float, b: float, t: float) -> float:
    """Eq. 8.33 (p. 8/100)."""
    return (q0 / b) * math.log(1 + b*t)


def hyperbolic_rate(q0: float, a: float, b: float, t: float) -> float:
    """Eq. 8.37 (p. 8/100), a = 1/d."""
    return q0 / (1 + (b/a)*t)**a


def hyperbolic_cum(q0: float, a: float, b: float, t: float) -> float:
    """Eq. 8.38 (p. 8/100)."""
    return (a*q0 / (b*(a-1))) * (1 - (1 + (b/a)*t)**(1-a))