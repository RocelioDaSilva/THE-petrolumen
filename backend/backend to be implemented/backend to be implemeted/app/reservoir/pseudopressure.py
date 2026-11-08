"""Real-gas pseudopressure m(p).

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 7, Sec. 6.2, pp. 240-242, Eq. (7.39), (7.45)-(7.46).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import simpson

DEFAULT_P_REF = 14.7
DEFAULT_N_GRID = 1000


@dataclass(frozen=True)
class PseudopressureResult:
    p_psia: float
    m_p_psia2_cp: float
    p_ref_psia: float
    n_grid: int
    p_outside_table: bool


def _interp_mu_z(
    p: float, table: list[tuple[float, float, float]],
) -> tuple[float, float]:
    """Piecewise-linear interpolation on (p, mu, z)."""
    ps = [pt[0] for pt in table]
    if p <= ps[0]:
        return table[0][1], table[0][2]
    if p >= ps[-1]:
        return table[-1][1], table[-1][2]
    for i in range(len(ps) - 1):
        if ps[i] <= p <= ps[i + 1]:
            frac = (p - ps[i]) / (ps[i + 1] - ps[i])
            mu1, z1 = table[i][1], table[i][2]
            mu2, z2 = table[i + 1][1], table[i + 1][2]
            return mu1 + frac * (mu2 - mu1), z1 + frac * (z2 - z1)
    return table[-1][1], table[-1][2]


def pseudopressure(
    p_psia: float,
    mu_z_table: list[tuple[float, float, float]],
    p_ref_psia: float = DEFAULT_P_REF,
    n_grid: int = DEFAULT_N_GRID,
) -> PseudopressureResult:
    """Real-gas pseudopressure m(p), Eq. (7.39).

    Args:
        p_psia: Target pressure, psia (> 0).
        mu_z_table: List of (p_psia, mu_cp, z) tuples, sorted by p,
            at least 2 points, mu > 0, z > 0.
        p_ref_psia: Reference pressure, psia (default 14.7).
        n_grid: Number of integration points (default 1000).

    Returns:
        PseudopressureResult.

    Raises:
        ValueError: any input out of physical range, or table
            malformed.
    """
    if not (p_psia > 0.0):
        raise ValueError(f"p_psia must be > 0, got {p_psia!r}")
    if not (p_ref_psia > 0.0):
        raise ValueError(
            f"p_ref_psia must be > 0, got {p_ref_psia!r}"
        )
    if n_grid < 10:
        raise ValueError(f"n_grid must be >= 10, got {n_grid!r}")
    if len(mu_z_table) < 2:
        raise ValueError(
            f"mu_z_table must have >= 2 points, got {len(mu_z_table)}"
        )
    for i, (pp, mu, z) in enumerate(mu_z_table):
        if not (pp > 0.0):
            raise ValueError(f"table[{i}].p must be > 0")
        if not (mu > 0.0):
            raise ValueError(f"table[{i}].mu must be > 0")
        if not (z > 0.0):
            raise ValueError(f"table[{i}].z must be > 0")
        if i > 0 and pp <= mu_z_table[i - 1][0]:
            raise ValueError(
                f"table pressures must be strictly increasing at {i}"
            )
    p_lo = mu_z_table[0][0]
    p_hi = mu_z_table[-1][0]
    outside = not (p_lo <= p_psia <= p_hi and p_lo <= p_ref_psia <= p_hi)

    grid = np.linspace(p_ref_psia, p_psia, n_grid)
    mu_arr = np.array([_interp_mu_z(float(g), mu_z_table)[0] for g in grid])
    z_arr = np.array([_interp_mu_z(float(g), mu_z_table)[1] for g in grid])
    integrand = 2.0 * grid / (mu_arr * z_arr)
    m_p = float(simpson(integrand, x=grid))
    return PseudopressureResult(
        p_psia=float(p_psia),
        m_p_psia2_cp=m_p,
        p_ref_psia=float(p_ref_psia),
        n_grid=int(n_grid),
        p_outside_table=outside,
    )
