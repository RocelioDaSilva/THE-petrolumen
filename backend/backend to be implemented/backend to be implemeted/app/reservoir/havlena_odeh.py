"""Havlena-Odeh straight-line material balance.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 2, Sec. 4, pp. 66-67, Eqs. (2.12)-(2.14);
Ch. 6, Sec. 3, pp. 191-193.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class HavlenaOdehPoint:
    Np: float
    Rp: float
    Wp: float
    We: float
    Bw: float
    Bt: float
    Bg: float
    delta_p: float


@dataclass(frozen=True)
class HavlenaOdehResult:
    n_hat: float
    intercept: float
    r_squared: float
    per_point_n: tuple[float, ...]
    residuals: tuple[float, ...]
    f_values: tuple[float, ...]
    x_values: tuple[float, ...]


def havelna_odeh(
    points: list[HavlenaOdehPoint],
    Bti: float,
    Bgi: float,
    Rsoi: float,
    Swi: float,
    cw: float,
    cf: float,
    m: float = 0.0,
) -> HavlenaOdehResult:
    """Through-origin Havlena-Odeh fit (Craft Eqs. 2.13-2.14).

    Builds F_i and X_i = Eo_i + (m*Bti/Bgi)*Eg_i
    + (1+m)*Bti*Ef_i for each observation, then fits F = N*X through
    the origin (matching the book's Eq. 2.14 statement that the
    intercept is zero). A free-intercept regression is also run for
    diagnostic value.

    Args:
        points: list of HavlenaOdehPoint (>= 2).
        Bti: Initial oil two-phase FVF, bbl/STB (> 0).
        Bgi: Initial gas FVF, bbl/SCF (> 0).
        Rsoi: Initial solution GOR, SCF/STB (>= 0).
        Swi: Connate water saturation, fraction ([0, 1)).
        cw: Water isothermal compressibility, psi^-1 (>= 0).
        cf: Formation compressibility, psi^-1 (>= 0).
        m: Initial gas-cap / oil-zone ratio (>= 0; default 0).

    Returns:
        HavlenaOdehResult.

    Raises:
        ValueError: invalid input, fewer than 2 points, or rank-
            deficient design matrix (all X_i == 0).
    """
    if not (Bti > 0.0):
        raise ValueError(f"Bti must be > 0, got {Bti!r}")
    if not (Bgi > 0.0):
        raise ValueError(f"Bgi must be > 0, got {Bgi!r}")
    if not (Rsoi >= 0.0):
        raise ValueError(f"Rsoi must be >= 0, got {Rsoi!r}")
    if not (0.0 <= Swi < 1.0):
        raise ValueError(f"Swi must be in [0, 1), got {Swi!r}")
    if not (cw >= 0.0):
        raise ValueError(f"cw must be >= 0, got {cw!r}")
    if not (cf >= 0.0):
        raise ValueError(f"cf must be >= 0, got {cf!r}")
    if not (m >= 0.0):
        raise ValueError(f"m must be >= 0, got {m!r}")
    if len(points) < 2:
        raise ValueError(
            f"At least 2 points required for regression, got {len(points)}"
        )

    for i, pt in enumerate(points):
        if not (pt.Np >= 0.0):
            raise ValueError(f"points[{i}].Np must be >= 0, got {pt.Np!r}")
        if not (pt.Rp >= 0.0):
            raise ValueError(f"points[{i}].Rp must be >= 0, got {pt.Rp!r}")
        if not (pt.Wp >= 0.0):
            raise ValueError(f"points[{i}].Wp must be >= 0, got {pt.Wp!r}")
        if not (pt.We >= 0.0):
            raise ValueError(f"points[{i}].We must be >= 0, got {pt.We!r}")
        if not (pt.Bw > 0.0):
            raise ValueError(f"points[{i}].Bw must be > 0, got {pt.Bw!r}")
        if not (pt.Bt > 0.0):
            raise ValueError(f"points[{i}].Bt must be > 0, got {pt.Bt!r}")
        if not (pt.Bg > 0.0):
            raise ValueError(f"points[{i}].Bg must be > 0, got {pt.Bg!r}")
        if not (pt.delta_p >= 0.0):
            raise ValueError(
                f"points[{i}].delta_p must be >= 0, got {pt.delta_p!r}"
            )

    ef_coef = (cw * Swi + cf) / (1.0 - Swi) if Swi < 1.0 else 0.0

    F: list[float] = []
    X: list[float] = []
    for pt in points:
        f_i = (
            pt.Np * (pt.Bt + (pt.Rp - Rsoi) * pt.Bg)
            + pt.Bw * pt.Wp
            - pt.We
        )
        eo_i = pt.Bt - Bti
        eg_i = pt.Bg - Bgi
        ef_i = ef_coef * pt.delta_p
        x_i = eo_i + (m * Bti / Bgi) * eg_i + (1.0 + m) * Bti * ef_i
        F.append(f_i)
        X.append(x_i)

    F_arr = np.asarray(F, dtype=float)
    X_arr = np.asarray(X, dtype=float)

    xx = float(np.dot(X_arr, X_arr))
    if xx <= 0.0:
        raise ValueError(
            "Design matrix rank-deficient: all X_i = 0. "
            "Cannot fit slope; check that at least one point has Bt != Bti."
        )

    n_hat = float(np.dot(X_arr, F_arr) / xx)

    A = np.column_stack([X_arr, np.ones_like(X_arr)])
    sol, *_ = np.linalg.lstsq(A, F_arr, rcond=None)
    intercept = float(sol[1])

    pred = n_hat * X_arr
    resid = F_arr - pred
    ss_res = float(np.sum(resid * resid))
    ss_tot = float(np.sum((F_arr - float(np.mean(F_arr))) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0.0 else 1.0

    per_point_n = tuple(
        float(F_arr[i] / X_arr[i]) if X_arr[i] != 0.0 else float("nan")
        for i in range(len(points))
    )

    return HavlenaOdehResult(
        n_hat=n_hat,
        intercept=intercept,
        r_squared=r_squared,
        per_point_n=per_point_n,
        residuals=tuple(float(r) for r in resid),
        f_values=tuple(float(f) for f in F_arr),
        x_values=tuple(float(x) for x in X_arr),
    )
