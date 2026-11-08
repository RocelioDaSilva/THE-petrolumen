"""Horner pressure buildup analysis.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 7, Sec. 10.2, pp. 259-262, Eqs. (7.68)-(7.71),
Example 7.3 (pp. 261-262).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

K_COEF = 162.6          # Eq. (7.70)
S_COEF = 1.151          # Eq. (7.71)
S_LOG_CONST = 3.23      # Eq. (7.71)

MIN_HORNER_SPAN = 0.30  # log10 decades
MIN_POINTS = 2


@dataclass(frozen=True)
class HornerResult:
    m_psi_per_cycle: float
    p1hr_psia: float
    k_md: float
    skin: float
    p_star_psia: float
    r_squared: float


def _r_squared(y: np.ndarray, pred: np.ndarray) -> float:
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - float(np.mean(y))) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0.0 else 1.0


def horner_buildup(
    q_stb_d: float,
    mu_cp: float,
    B_bbl_stb: float,
    h_ft: float,
    phi: float,
    ct_psi_inv: float,
    rw_ft: float,
    tp_hr: float,
    pwf_at_shutin_psia: float,
    horner_points: list[tuple[float, float]],
) -> HornerResult:
    """Horner buildup interpretation (Craft Eqs. 7.68-7.71).

    Fits p_ws vs log10((tp + dt)/dt) on the Horner straight-line
    region and returns k, S, and p* (pi-equivalent extrapolation).

    The caller is responsible for supplying points on the transient
    straight-line region (book p. 262 notes the earliest points are
    often wellbore-storage-dominated). tp must be computed from
    cumulative production per Eq. (7.68).

    Args:
        q_stb_d: Flow rate before shut-in, STB/day (> 0).
        mu_cp: Viscosity, cp (> 0).
        B_bbl_stb: FVF, bbl/STB (> 0).
        h_ft: Net pay thickness, ft (> 0).
        phi: Porosity, fraction (0, 1).
        ct_psi_inv: Total compressibility, psi^-1 (> 0).
        rw_ft: Wellbore radius, ft (> 0).
        tp_hr: Producing time before shut-in, hr (> 0; Eq. 7.68).
        pwf_at_shutin_psia: Flowing BHP at the instant of shut-in,
            psia (> 0).
        horner_points: List of (dt_hr > 0, pws_psia > 0).

    Returns:
        HornerResult.

    Raises:
        ValueError: invalid input, fewer than 2 points, insufficient
            Horner-time span, or non-physical slope.
    """
    if not (q_stb_d > 0.0):
        raise ValueError(f"q_stb_d must be > 0, got {q_stb_d!r}")
    if not (mu_cp > 0.0):
        raise ValueError(f"mu_cp must be > 0, got {mu_cp!r}")
    if not (B_bbl_stb > 0.0):
        raise ValueError(f"B_bbl_stb must be > 0, got {B_bbl_stb!r}")
    if not (h_ft > 0.0):
        raise ValueError(f"h_ft must be > 0, got {h_ft!r}")
    if not (0.0 < phi < 1.0):
        raise ValueError(f"phi must be in (0, 1), got {phi!r}")
    if not (ct_psi_inv > 0.0):
        raise ValueError(f"ct_psi_inv must be > 0, got {ct_psi_inv!r}")
    if not (rw_ft > 0.0):
        raise ValueError(f"rw_ft must be > 0, got {rw_ft!r}")
    if not (tp_hr > 0.0):
        raise ValueError(f"tp_hr must be > 0, got {tp_hr!r}")
    if not (pwf_at_shutin_psia > 0.0):
        raise ValueError(
            f"pwf_at_shutin_psia must be > 0, got {pwf_at_shutin_psia!r}"
        )

    if len(horner_points) < MIN_POINTS:
        raise ValueError(
            f"At least {MIN_POINTS} Horner points required, got "
            f"{len(horner_points)}"
        )

    dt_arr = np.empty(len(horner_points), dtype=float)
    pws_arr = np.empty(len(horner_points), dtype=float)
    for i, (dt, pws) in enumerate(horner_points):
        if not (dt > 0.0):
            raise ValueError(
                f"horner_points[{i}] dt must be > 0, got {dt!r}"
            )
        if not (pws > 0.0):
            raise ValueError(
                f"horner_points[{i}] pws must be > 0, got {pws!r}"
            )
        dt_arr[i] = dt
        pws_arr[i] = pws

    # Eq. (7.69): x = log10((tp + dt)/dt)
    x = np.log10((tp_hr + dt_arr) / dt_arr)
    span = float(np.max(x) - np.min(x))
    if span < MIN_HORNER_SPAN:
        raise ValueError(
            f"Horner time span {span:.3f} decades < "
            f"{MIN_HORNER_SPAN}; slope will be poorly conditioned."
        )

    # Fit pws = b + m*x -> [m, b]
    m, b = np.polyfit(x, pws_arr, 1)
    m = float(m)
    b = float(b)
    if not (m < 0.0):
        raise ValueError(
            f"Fitted Horner slope m = {m!r} >= 0; buildup pressure "
            "must rise with Horner time (i.e., decline with x-axis)."
        )
    r2 = _r_squared(pws_arr, m * x + b)

    # p1hr = value at dt = 1 hr: x1 = log10((tp + 1)/1)
    p1hr = b + m * math.log10(tp_hr + 1.0)
    # p* = b (extrapolation at x = 0)
    p_star = b

    # Eq. (7.70): k
    k = -K_COEF * q_stb_d * mu_cp * B_bbl_stb / (m * h_ft)
    if not (k > 0.0):
        raise ValueError(
            f"Computed k = {k!r} md <= 0; check inputs."
        )

    # Eq. (7.71): S
    log_arg = k / (phi * mu_cp * ct_psi_inv * rw_ft * rw_ft)
    if not (log_arg > 0.0):
        raise ValueError(
            "log(k/(phi*mu*ct*rw^2)) argument <= 0; check inputs."
        )
    skin = S_COEF * (
        (pwf_at_shutin_psia - p1hr) / m
        - math.log10(log_arg) + S_LOG_CONST
    )

    return HornerResult(
        m_psi_per_cycle=m,
        p1hr_psia=p1hr,
        k_md=k,
        skin=skin,
        p_star_psia=p_star,
        r_squared=r2,
    )
