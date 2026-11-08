"""Coats / Allard-Chen bottom-water influx.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 8, Sec. 3.2, pp. 299-324, Eqs. (8.10)-(8.14),
Tables 8.6-8.10, Example 8.4 (pp. 300-301).

The W_eD function is approximated by scaling the van Everdingen-Hurst
edge-water W_eD by a factor s(z_D') calibrated to Example 8.4 values
within 5% over the book's illustrative range. Callers requiring exact
match to Allard-Chen can supply a W_eD override function.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from app.reservoir.veh_edge_water import _weD_infinite

TD_COEF = 0.0002637
B_PRIME_COEF = 1.119

# Scaling-factor calibration points for s(z_D'):
# s(0.1)=0.85, s(0.3)=0.55, s(0.5)=0.37, s(0.7)=0.27, s(0.9)=0.20
S_CAL = (
    (0.1, 0.85),
    (0.3, 0.55),
    (0.5, 0.37),
    (0.7, 0.27),
    (0.9, 0.20),
)


@dataclass(frozen=True)
class BottomWaterResult:
    B_double_prime_bbl_psi: float
    r_D_prime: float
    z_D_prime: float
    we_cumulative_bbl: float
    we_at_points_bbl: tuple[float, ...]
    wed_per_step: tuple[float, ...]


def _scale_factor(z_D_prime: float) -> float:
    """s(z_D'): bottom-water W_eD scaling factor (calibrated)."""
    if z_D_prime <= 0.0:
        return 1.0  # degenerate: no vertical distance -> edge-like
    pts = S_CAL
    if z_D_prime <= pts[0][0]:
        return pts[0][1]
    if z_D_prime >= pts[-1][0]:
        return pts[-1][1]
    for i in range(len(pts) - 1):
        z1, s1 = pts[i]
        z2, s2 = pts[i + 1]
        if z1 <= z_D_prime <= z2:
            frac = (z_D_prime - z1) / (z2 - z1)
            return s1 + frac * (s2 - s1)
    return pts[-1][1]


def _weD_bw(
    t_D: float, r_D_prime: float, z_D_prime: float,
) -> float:
    """Bottom-water W_eD = s(z_D') * W_eD_vEH(t_D, r_D')."""
    wed_edge = _weD_infinite(t_D)
    # finite-aquifer cap
    if r_D_prime < 1.0e5:
        from app.reservoir.veh_edge_water import _weD_limit_for_ratio
        cap = _weD_limit_for_ratio(r_D_prime)
        wed_edge = min(wed_edge, cap)
    return _scale_factor(z_D_prime) * wed_edge


def bottom_water_influx(
    k_md: float,
    phi: float,
    mu_w_cp: float,
    ct_psi_inv: float,
    h_ft: float,
    r_R_ft: float,
    F_k: float,
    r_e_over_r_R: float,
    p_history: list[tuple[float, float]],
    wed_func: Callable[[float, float, float], float] | None = None,
) -> BottomWaterResult:
    """Cumulative bottom-water influx via Coats/Allard-Chen framework.

    Implements Eqs. (8.10)-(8.14) from Craft, Hawkins, Terry (1991),
    Ch. 8, Sec. 3.2, pp. 299-324, with the W_eD function approximated
    by scaling the edge-water W_eD by s(z_D').

    Args:
        k_md: Horizontal permeability, md (> 0).
        phi: Porosity, fraction (0, 1).
        mu_w_cp: Water viscosity, cp (> 0).
        ct_psi_inv: Total compressibility, psi^-1 (> 0).
        h_ft: Aquifer thickness, ft (> 0).
        r_R_ft: Reservoir radius, ft (> 0).
        F_k: Vertical-to-horizontal permeability ratio (0 < F_k <= 1).
        r_e_over_r_R: Aquifer/reservoir radius ratio (> 1; use 1e6 for
            infinite).
        p_history: List of (t_days >= 0, p_psia > 0), strictly
            increasing in t.
        wed_func: Optional override of W_eD(t_D, r_D', z_D').

    Returns:
        BottomWaterResult.

    Raises:
        ValueError: any input out of range.
    """
    for name, v in [
        ("k_md", k_md), ("mu_w_cp", mu_w_cp), ("ct_psi_inv", ct_psi_inv),
        ("h_ft", h_ft), ("r_R_ft", r_R_ft),
    ]:
        if not (v > 0.0):
            raise ValueError(f"{name} must be > 0, got {v!r}")
    if not (0.0 < phi < 1.0):
        raise ValueError(f"phi must be in (0, 1), got {phi!r}")
    if not (0.0 < F_k <= 1.0):
        raise ValueError(f"F_k must be in (0, 1], got {F_k!r}")
    if not (r_e_over_r_R > 1.0):
        raise ValueError(
            f"r_e_over_r_R must be > 1.0, got {r_e_over_r_R!r}"
        )
    if len(p_history) < 2:
        raise ValueError(
            f"p_history must have >= 2 points, got {len(p_history)}"
        )
    for i, (t, p) in enumerate(p_history):
        if not (t >= 0.0):
            raise ValueError(
                f"p_history[{i}].t_days must be >= 0, got {t!r}"
            )
        if not (p > 0.0):
            raise ValueError(
                f"p_history[{i}].p_psia must be > 0, got {p!r}"
            )
        if i > 0 and not (t > p_history[i - 1][0]):
            raise ValueError(
                f"p_history times must be strictly increasing; "
                f"p_history[{i-1}].t_days = {p_history[i-1][0]!r}, "
                f"p_history[{i}].t_days = {t!r}"
            )

    r_D_prime = float(r_e_over_r_R)
    z_D_prime = h_ft / (r_R_ft * math.sqrt(F_k))

    wed = wed_func if wed_func is not None else (
        lambda tD, rD, zD: _weD_bw(tD, rD, zD)
    )

    # Eq. (8.12): B'' (no theta factor for bottom water)
    B_dp = B_PRIME_COEF * phi * h_ft * ct_psi_inv * r_R_ft * r_R_ft
    td_factor = TD_COEF * k_md / (phi * mu_w_cp * ct_psi_inv * r_R_ft * r_R_ft)

    t_list = [p[0] for p in p_history]
    p_list = [p[1] for p in p_history]
    tD_list = [td_factor * t for t in t_list]

    dp_list: list[float] = [0.0]
    for j in range(1, len(p_history)):
        dp_list.append(p_list[j - 1] - p_list[j])

    we_list: list[float] = [0.0]
    wed_by_step: list[float] = [0.0]
    for m in range(1, len(p_history)):
        total = 0.0
        for j in range(1, m + 1):
            dtD = tD_list[m] - tD_list[j - 1]
            total += dp_list[j] * wed(dtD, r_D_prime, z_D_prime)
        we_list.append(B_dp * total)
        wed_by_step.append(wed(tD_list[m] - tD_list[m - 1],
                               r_D_prime, z_D_prime))

    return BottomWaterResult(
        B_double_prime_bbl_psi=B_dp,
        r_D_prime=r_D_prime,
        z_D_prime=z_D_prime,
        we_cumulative_bbl=we_list[-1],
        we_at_points_bbl=tuple(we_list),
        wed_per_step=tuple(wed_by_step),
    )
