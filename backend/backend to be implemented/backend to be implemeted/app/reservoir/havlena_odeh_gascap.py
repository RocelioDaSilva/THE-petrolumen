"""Havlena-Odeh straight-line with gas cap.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 6, Sec. 3, pp. 191-193, Eqs. (6.3)-(6.5),
Table 6.2 / Fig. 6.4 (Conroe Field worked example).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

SLOPE_TOL = 0.05        # 5% deviation from 1.0 triggers the flag
MIN_POINTS = 2


@dataclass(frozen=True)
class HOGC_Point:
    Np: float
    Rp: float
    Wp: float
    We: float
    Bw: float
    Bt: float
    Bg: float


@dataclass(frozen=True)
class HOGC_Result:
    n_hat: float
    free_slope: float
    free_intercept: float
    r_squared: float
    slope_diagnostic_ok: bool
    per_point_n: tuple[float, ...]
    residuals: tuple[float, ...]
    f_prime: tuple[float, ...]
    x_values: tuple[float, ...]


def _r_squared(y: np.ndarray, pred: np.ndarray) -> float:
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - float(np.mean(y))) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0.0 else 1.0


def havelna_odeh_gascap(
    points: list[HOGC_Point],
    Bti: float,
    Bgi: float,
    Rsoi: float,
    m: float,
) -> HOGC_Result:
    """Fit F' / X through origin (Craft Eqs. 6.4-6.5).

    Args:
        points: List of HOGC_Point, >= 2.
        Bti: Initial two-phase FVF, bbl/STB (> 0).
        Bgi: Initial gas FVF, bbl/SCF (> 0).
        Rsoi: Initial solution GOR, SCF/STB (>= 0).
        m: Gas cap / oil zone ratio (>= 0).

    Returns:
        HOGC_Result.

    Raises:
        ValueError: invalid input or rank-deficient X.
    """
    for name, v in [("Bti", Bti), ("Bgi", Bgi)]:
        if not (v > 0.0):
            raise ValueError(f"{name} must be > 0, got {v!r}")
    if not (Rsoi >= 0.0):
        raise ValueError(f"Rsoi must be >= 0, got {Rsoi!r}")
    if not (m >= 0.0):
        raise ValueError(f"m must be >= 0, got {m!r}")
    if len(points) < MIN_POINTS:
        raise ValueError(
            f"At least {MIN_POINTS} points required, got {len(points)}"
        )
    for i, pt in enumerate(points):
        for name in ("Np", "Rp", "Wp", "We", "Bw"):
            v = getattr(pt, name)
            if not (v >= 0.0 if name != "Bw" else v > 0.0):
                raise ValueError(
                    f"points[{i}].{name} out of range: {v!r}"
                )
        for name in ("Bt", "Bg"):
            v = getattr(pt, name)
            if not (v > 0.0):
                raise ValueError(
                    f"points[{i}].{name} must be > 0, got {v!r}"
                )

    gascap_coef = m * Bti / Bgi
    F: list[float] = []
    X: list[float] = []
    for pt in points:
        f_prime = (
            pt.Np * (pt.Bt + (pt.Rp - Rsoi) * pt.Bg)
            + pt.Bw * pt.Wp - pt.We
        )
        eo = pt.Bt - Bti
        eg = pt.Bg - Bgi
        x = eo + gascap_coef * eg
        F.append(f_prime)
        X.append(x)

    F_arr = np.asarray(F, dtype=float)
    X_arr = np.asarray(X, dtype=float)

    xx = float(np.dot(X_arr, X_arr))
    if xx <= 0.0:
        raise ValueError(
            "Design matrix rank-deficient: all X_i = 0. "
            "Cannot fit slope."
        )

    n_hat = float(np.dot(X_arr, F_arr) / xx)

    A = np.column_stack([X_arr, np.ones_like(X_arr)])
    sol, *_ = np.linalg.lstsq(A, F_arr, rcond=None)
    free_slope = float(sol[0])
    free_intercept = float(sol[1])

    pred = n_hat * X_arr
    resid = F_arr - pred
    r2 = _r_squared(F_arr, pred)

    per_point_n = tuple(
        float(F_arr[i] / X_arr[i]) if X_arr[i] != 0.0 else float("nan")
        for i in range(len(points))
    )

    slope_ok = abs(free_slope - 1.0) < SLOPE_TOL

    return HOGC_Result(
        n_hat=n_hat,
        free_slope=free_slope,
        free_intercept=free_intercept,
        r_squared=r2,
        slope_diagnostic_ok=slope_ok,
        per_point_n=per_point_n,
        residuals=tuple(float(r) for r in resid),
        f_prime=tuple(float(f) for f in F_arr),
        x_values=tuple(float(x) for x in X_arr),
    )
