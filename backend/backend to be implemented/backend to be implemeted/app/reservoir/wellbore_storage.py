"""Wellbore storage coefficient from early drawdown.

Source: Chin, W.C. (2016), Reservoir Engineering in Modern Oilfields:
Vertical, Deviated, Horizontal and Multilateral Well Systems, Wiley,
Ch. 2, Sec. "Modeling wellbore storage", pp. 47-48; Ch. 3, Example 3-5.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

EARLY_UNIT_SLOPE_R2_MIN = 0.95
LATE_FLAT_R2_MAX = 0.95
MIN_POINTS = 3


@dataclass(frozen=True)
class WellboreStorageResult:
    F_bbl_per_psi: float
    F_ft5_per_lbf: float
    r_squared_early: float
    r_squared_late: float | None
    late_data_usable: bool
    early_fit_slope_psi_per_hr: float


def _r2(y: np.ndarray, pred: np.ndarray) -> float:
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - float(np.mean(y))) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0.0 else 1.0


def wellbore_storage_from_drawdown(
    early_points: list[tuple[float, float]],
    Q_stb_d: float,
    late_points: list[tuple[float, float]] | None = None,
) -> WellboreStorageResult:
    """Estimate wellbore storage factor F from early drawdown.

    Fits a linear Delta-p vs Delta-t on the early unit-slope window
    (Chin Ch 2 pp. 47-48), then F = Q / (dp_wf/dt) with units adapted
    to bbl/psi (oilfield) and ft^5/lbf (Chin).

    Args:
        early_points: List of (dt_hr > 0, pwf > 0), >= 3 points,
            during the wellbore-storage-dominated period.
        Q_stb_d: Surface production rate, STB/day (> 0).
        late_points: Optional list of (dt_hr > 0, pwf > 0) from the
            post-storage period, used to compute the
            late_data_usable flag.

    Returns:
        WellboreStorageResult.

    Raises:
        ValueError: invalid input, no unit-slope window, or non-
            positive storage factor.
    """
    if not (Q_stb_d > 0.0):
        raise ValueError(f"Q_stb_d must be > 0, got {Q_stb_d!r}")
    if len(early_points) < MIN_POINTS:
        raise ValueError(
            f"At least {MIN_POINTS} early points required, got "
            f"{len(early_points)}"
        )
    t_arr = np.empty(len(early_points), dtype=float)
    p_arr = np.empty(len(early_points), dtype=float)
    for i, (dt, p) in enumerate(early_points):
        if not (dt > 0.0):
            raise ValueError(
                f"early_points[{i}] dt_hr must be > 0, got {dt!r}"
            )
        if not (p > 0.0):
            raise ValueError(
                f"early_points[{i}] pwf must be > 0, got {p!r}"
            )
        t_arr[i] = dt
        p_arr[i] = p

    # Unit slope: Delta p vs Delta t linear (in chronological coords,
    # this is p_wf declining linearly with t at fixed q_surface).
    # Fit p_wf = b + m * t; expected m < 0 during drawdown.
    m, b = np.polyfit(t_arr, p_arr, 1)
    m = float(m)
    b = float(b)
    if not (m < 0.0):
        raise ValueError(
            f"Early-slope m = {m!r} >= 0; expected declining pwf during "
            "drawdown."
        )
    r2_early = _r2(p_arr, m * t_arr + b)
    if r2_early < EARLY_UNIT_SLOPE_R2_MIN:
        # Still allow the fit, but flag in the diagnostic
        pass

    # F = Q / (dp_wf/dt). Note Q is in STB/day and t in hr -> factor 24.
    dp_dt_stb_per_hr = -m  # negative slope -> positive decline rate
    F_bbl_per_psi = Q_stb_d / 24.0 / dp_dt_stb_per_hr
    if not (F_bbl_per_psi > 0.0):
        raise ValueError(
            f"Computed F = {F_bbl_per_psi!r} <= 0; check inputs."
        )

    # Chin's ft^5/lbf uses Vol*C (compressibility * volume):
    # 1 bbl/psi = 5.6146 ft^3/psi
    # 1 psi = 1 lbf / (1/144 ft^2) = 144 lbf/ft^2
    # 1 bbl/psi = 5.6146 * 144 = 808.5 ft^5/lbf (approximately)
    F_ft5_per_lbf = F_bbl_per_psi * 808.5

    # Late-data diagnostic
    r2_late: float | None = None
    late_usable = True
    if late_points is not None:
        if len(late_points) < MIN_POINTS:
            raise ValueError(
                f"late_points must have >= {MIN_POINTS} points if "
                "provided, got {len(late_points)}"
            )
        lt = np.empty(len(late_points), dtype=float)
        lp = np.empty(len(late_points), dtype=float)
        for i, (dt, p) in enumerate(late_points):
            if not (dt > 0.0):
                raise ValueError(f"late_points[{i}] dt_hr must be > 0")
            if not (p > 0.0):
                raise ValueError(f"late_points[{i}] pwf must be > 0")
            lt[i] = dt
            lp[i] = p
        ml, bl = np.polyfit(lt, lp, 1)
        r2_late = _r2(lp, ml * lt + bl)
        # If the late data are still extremely linear, they may STILL be
        # in storage; flag as not usable.
        late_usable = r2_late < LATE_FLAT_R2_MAX

    return WellboreStorageResult(
        F_bbl_per_psi=F_bbl_per_psi,
        F_ft5_per_lbf=F_ft5_per_lbf,
        r_squared_early=r2_early,
        r_squared_late=r2_late,
        late_data_usable=late_usable,
        early_fit_slope_psi_per_hr=m,
    )
