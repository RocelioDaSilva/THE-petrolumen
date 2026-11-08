"""Fetkovich pseudosteady-state water influx.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 8, Sec. 4, pp. 325-328, Eqs. (8.15)-(8.21),
Table 8.11 (p. 327), Example 8.5 (pp. 326-328).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

J_COEF = 0.00708         # Table 8.11, p. 327
PSS_OFFSET = 0.75        # Table 8.11, p. 327
FULL_ANGLE_DEG = 360.0

Boundary = Literal["no_flow", "constant_pressure"]


@dataclass(frozen=True)
class FetkovichResult:
    J_bpd_psi: float | None
    we_cumulative_bbl: float
    we_at_points_bbl: tuple[float, ...]
    delta_we_per_step_bbl: tuple[float, ...]
    pbar_per_step_psia: tuple[float, ...]


def fetkovich_productivity_index(
    k_md: float,
    h_ft: float,
    mu_cp: float,
    r_e_ft: float,
    r_R_ft: float,
    theta_deg: float,
    outer_boundary: Boundary,
) -> float:
    """Aquifer productivity index J for radial flow (Table 8.11, p. 327).

    Args:
        k_md: Aquifer permeability, md (> 0).
        h_ft: Thickness, ft (> 0).
        mu_cp: Water viscosity, cp (> 0).
        r_e_ft: Aquifer outer radius, ft (> 0; must exceed r_R).
        r_R_ft: Reservoir radius, ft (> 0).
        theta_deg: Angle subtended by reservoir boundary, deg
            (0 < theta <= 360).
        outer_boundary: 'no_flow' or 'constant_pressure'.

    Returns:
        J (bbl/day/psi).

    Raises:
        ValueError: any input out of range, or invalid boundary name.
    """
    if not (k_md > 0.0):
        raise ValueError(f"k_md must be > 0, got {k_md!r}")
    if not (h_ft > 0.0):
        raise ValueError(f"h_ft must be > 0, got {h_ft!r}")
    if not (mu_cp > 0.0):
        raise ValueError(f"mu_cp must be > 0, got {mu_cp!r}")
    if not (r_e_ft > 0.0):
        raise ValueError(f"r_e_ft must be > 0, got {r_e_ft!r}")
    if not (r_R_ft > 0.0):
        raise ValueError(f"r_R_ft must be > 0, got {r_R_ft!r}")
    if not (r_e_ft > r_R_ft):
        raise ValueError(
            f"r_e_ft ({r_e_ft!r}) must exceed r_R_ft ({r_R_ft!r})"
        )
    if not (0.0 < theta_deg <= FULL_ANGLE_DEG):
        raise ValueError(
            f"theta_deg must be in (0, {FULL_ANGLE_DEG}], got {theta_deg!r}"
        )
    if outer_boundary == "no_flow":
        log_arg = math.log(r_e_ft / r_R_ft) - PSS_OFFSET
        if not (log_arg > 0.0):
            raise ValueError(
                f"ln(r_e/r_R) - 0.75 = {log_arg!r} <= 0; r_e/r_R "
                "must be large enough (>= e^0.75 ~= 2.12)"
            )
    elif outer_boundary == "constant_pressure":
        log_arg = math.log(r_e_ft / r_R_ft)
        if not (log_arg > 0.0):
            raise ValueError(
                f"ln(r_e/r_R) = {log_arg!r} <= 0; r_e must exceed r_R"
            )
    else:
        raise ValueError(
            f"outer_boundary must be 'no_flow' or 'constant_pressure', "
            f"got {outer_boundary!r}"
        )
    theta_frac = theta_deg / FULL_ANGLE_DEG
    J = J_COEF * k_md * h_ft * theta_frac / (mu_cp * log_arg)
    return J


def fetkovich_water_influx(
    W_ei_bbl: float,
    p_i_psia: float,
    J_bpd_psi: float,
    p_history: list[tuple[float, float]],
) -> FetkovichResult:
    """Cumulative Fetkovich influx over a boundary-pressure history.

    Implements Eqs. (8.18)-(8.21) from Craft, Hawkins, Terry (1991),
    Ch. 8, Sec. 4, pp. 325-328, Example 8.5.

    Args:
        W_ei_bbl: Initial encroachable water, bbl (> 0).
        p_i_psia: Initial aquifer pressure, psia (> 0).
        J_bpd_psi: Aquifer productivity index, bbl/day/psi (> 0).
        p_history: List of (t_days >= 0, p_R_psia > 0) strictly
            increasing in t. The boundary pressure p_R is the pressure
            at the reservoir-aquifer boundary at each measurement time.

    Returns:
        FetkovichResult with cumulative W_e per step.

    Raises:
        ValueError: invalid input or physical geometry violations.
    """
    if not (W_ei_bbl > 0.0):
        raise ValueError(f"W_ei_bbl must be > 0, got {W_ei_bbl!r}")
    if not (p_i_psia > 0.0):
        raise ValueError(f"p_i_psia must be > 0, got {p_i_psia!r}")
    if not (J_bpd_psi > 0.0):
        raise ValueError(f"J_bpd_psi must be > 0, got {J_bpd_psi!r}")
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
                f"p_history[{i}].p_R_psia must be > 0, got {p!r}"
            )
        if p > p_i_psia:
            raise ValueError(
                f"p_history[{i}].p_R_psia = {p!r} exceeds p_i_psia = "
                f"{p_i_psia!r}; cannot represent an aquifer discharging "
                "into a reservoir above its initial pressure."
            )
        if i > 0 and not (t > p_history[i - 1][0]):
            raise ValueError(
                f"p_history times must be strictly increasing; "
                f"p_history[{i-1}].t_days = {p_history[i-1][0]!r}, "
                f"p_history[{i}].t_days = {t!r}"
            )

    We_list: list[float] = [0.0]
    dWe_list: list[float] = [0.0]
    pbar_list: list[float] = [p_i_psia]
    W_e = 0.0
    pbar_prev = p_i_psia    # Eq. (8.19) at n=0: pbar_0 = p_i
    p_R_prev = p_i_psia     # boundary starts at p_i

    for i in range(1, len(p_history)):
        t_n, p_Rn = p_history[i]
        t_prev = p_history[i - 1][0]
        dt_n = t_n - t_prev
        # Eq. (8.20): average boundary pressure during interval n
        pbarR_n = 0.5 * (p_R_prev + p_Rn)
        # Eq. (8.18): per-interval influx
        factor = 1.0 - math.exp(-J_bpd_psi * p_i_psia * dt_n / W_ei_bbl)
        dW_en = (W_ei_bbl / p_i_psia) * (pbar_prev - pbarR_n) * factor
        # Eq. (8.21): cumulative sum
        W_e += dW_en
        We_list.append(W_e)
        dWe_list.append(dW_en)
        # Eq. (8.19): update aquifer average pressure for next step
        pbar_prev = p_i_psia * (1.0 - W_e / W_ei_bbl)
        pbar_list.append(pbar_prev)
        p_R_prev = p_Rn

    return FetkovichResult(
        J_bpd_psi=J_bpd_psi,
        we_cumulative_bbl=W_e,
        we_at_points_bbl=tuple(We_list),
        delta_we_per_step_bbl=tuple(dWe_list),
        pbar_per_step_psia=tuple(pbar_list),
    )
