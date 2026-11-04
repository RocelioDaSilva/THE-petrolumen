"""Chapter 18 â€” Production Optimization (pp. 18/267 â€“ 18/280)."""
from __future__ import annotations
import math


def series_capacity_ratio(L, D1, L1, D2) -> float:
    """Series pipeline capacity â€” Eq. 18.31 (p. 18/272)."""
    return math.sqrt(
        (L / D1**(16/3))
        / (L1/D1**(16/3) + (L - L1)/D2**(16/3)))


def parallel_capacity_ratio(D1, D2) -> float:
    """Parallel pipeline capacity â€” Eq. 18.36 (p. 18/272)."""
    return ((math.sqrt(D1**(16/3)) + math.sqrt(D2**(16/3)))
            / math.sqrt(D1**(16/3)))


def looped_capacity_ratio(L, D1, L1, D2) -> float:
    """Looped pipeline capacity â€” Eq. 18.43 (p. 18/273)."""
    denom = (L1 / (math.sqrt(D1**(16/3)) + math.sqrt(D2**(16/3)))**2
             + (L - L1) / D1**(16/3))
    return math.sqrt((L / D1**(16/3)) / denom)


def npv(cashflows, i) -> float:
    """Net present value â€” Eq. 18.48 (p. 18/279)."""
    return sum(cf / (1 + i)**n for n, cf in enumerate(cashflows))