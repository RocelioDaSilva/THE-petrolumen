"""Craze-Buckley / Arps residual-oil saturation correlation.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 5, Sec. 2, p. 151, Table 5.2.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Base table: (mu_o_cp, Sor_pct) -- log-log monotone
BASE = (
    (0.2, 30.0), (0.5, 32.0), (1.0, 34.5), (2.0, 37.0),
    (5.0, 40.5), (10.0, 43.5), (20.0, 64.5),
)
# Permeability adjustment: (k_md, delta_Sor_pct) -- log-log monotone
ADJ = (
    (50.0, 12.0), (100.0, 9.0), (200.0, 6.0), (500.0, 2.0),
    (1000.0, -1.0), (2000.0, -4.5), (5000.0, -8.5),
)


@dataclass(frozen=True)
class CrazeBuckleyResult:
    Sor: float             # fraction of pore space
    Sor_pct: float         # percent of pore space
    base_pct: float
    adj_pct: float
    out_of_table_range: bool


def _loglog_interp(x: float, table: tuple[tuple[float, float], ...]) -> float:
    """Log-log linear interpolation, clamped at endpoints."""
    if x <= table[0][0]:
        return table[0][1]
    if x >= table[-1][0]:
        return table[-1][1]
    lx = math.log10(x)
    for i in range(len(table) - 1):
        x1, y1 = table[i]
        x2, y2 = table[i + 1]
        if x1 <= x <= x2:
            lx1, lx2 = math.log10(x1), math.log10(x2)
            # Interpolate y on log(y) because y is monotone-positive
            ly1, ly2 = math.log10(y1 if y1 > 0 else 1e-6), \
                       math.log10(y2 if y2 > 0 else 1e-6)
            # Handle sign for ADJ which has negative values
            if y1 <= 0.0 or y2 <= 0.0:
                # Linear interpolation in x, log-x on y
                frac = (lx - lx1) / (lx2 - lx1)
                return y1 + frac * (y2 - y1)
            frac = (lx - lx1) / (lx2 - lx1)
            return math.pow(10.0, ly1 + frac * (ly2 - ly1))
    return table[-1][1]


def craze_buckley_sor(
    mu_o_cp: float, k_md: float,
) -> CrazeBuckleyResult:
    """Residual oil saturation from Craze-Buckley (Craft Table 5.2).

    Args:
        mu_o_cp: Reservoir oil viscosity, cp (> 0).
        k_md: Average permeability, md (> 0).

    Returns:
        CrazeBuckleyResult with Sor (fraction) and Sor_pct (percent).

    Raises:
        ValueError: any input out of physical range.
    """
    if not (mu_o_cp > 0.0):
        raise ValueError(f"mu_o_cp must be > 0, got {mu_o_cp!r}")
    if not (k_md > 0.0):
        raise ValueError(f"k_md must be > 0, got {k_md!r}")

    base = _loglog_interp(mu_o_cp, BASE)
    adj = _loglog_interp(k_md, ADJ)
    sor_pct = base + adj
    out_of_range = not (0.0 <= sor_pct <= 100.0)
    return CrazeBuckleyResult(
        Sor=sor_pct / 100.0,
        Sor_pct=sor_pct,
        base_pct=base,
        adj_pct=adj,
        out_of_table_range=out_of_range,
    )
