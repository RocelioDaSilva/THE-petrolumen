"""Gas material balance (p/z vs Gp) with least-squares fit.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 3, Sec. 5, pp. 83-90, Eq. (3.18) and Example 3.5.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Diagnostic thresholds (documented in the write-up)
R2_LINEARITY_WARN = 0.90
INTERCEPT_REL_WARN = 0.05  # 5% deviation vs pi/zi


@dataclass(frozen=True)
class GasPZPoint:
    p_psia: float
    Gp_scf: float
    z: float


@dataclass(frozen=True)
class GasPZResult:
    g_initial_scf: float
    slope: float
    intercept: float
    r_squared: float
    gp_at_abandonment_scf: float | None
    linearity_suspect: bool
    intercept_suspect: bool
    predicted_pz: tuple[float, ...]
    predicted_gp: tuple[float, ...]


def gas_pz_analysis(
    points: list[GasPZPoint],
    abandon_pz: float | None = None,
) -> GasPZResult:
    """Fit p/z = m*Gp + b and return G = -b/m (Craft Eq. 3.18).

    Implements the linear-regression method of Craft, Hawkins, Terry
    (1991), Ch. 3, Sec. 5, pp. 83-90, Eq. (3.18). Requires a volumetric
    reservoir for validity (book p. 84-85); the diagnostic flags on
    low R^2 warn that a water drive may be present.

    Args:
        points: List of GasPZPoint, at least 2. Each has p_psia (>0),
            Gp_scf (>=0), z (>0).
        abandon_pz: Optional abandonment p/z (psia). If provided, the
            engine predicts Gp at that p/z.

    Returns:
        GasPZResult with G, slope, intercept, R^2, abandonment Gp
        (if requested), diagnostic flags, and the fitted (Gp, p/z)
        pairs.

    Raises:
        ValueError: fewer than 2 points, any input out of physical
            range, rank-deficient design, or non-physical slope
            (m >= 0).
    """
    if len(points) < 2:
        raise ValueError(
            f"At least 2 survey points required, got {len(points)}"
        )

    gp = np.empty(len(points), dtype=float)
    pz = np.empty(len(points), dtype=float)
    for i, pt in enumerate(points):
        if not (pt.p_psia > 0.0):
            raise ValueError(
                f"points[{i}].p_psia must be > 0, got {pt.p_psia!r}"
            )
        if not (pt.Gp_scf >= 0.0):
            raise ValueError(
                f"points[{i}].Gp_scf must be >= 0, got {pt.Gp_scf!r}"
            )
        if not (pt.z > 0.0):
            raise ValueError(f"points[{i}].z must be > 0, got {pt.z!r}")
        gp[i] = pt.Gp_scf
        pz[i] = pt.p_psia / pt.z

    A = np.column_stack([gp, np.ones_like(gp)])
    sol, _resid, rank, _sv = np.linalg.lstsq(A, pz, rcond=None)
    if rank < 2:
        raise ValueError(
            "Design matrix rank-deficient (Gp values are all identical); "
            "cannot fit slope and intercept."
        )
    slope = float(sol[0])
    intercept = float(sol[1])

    if not (slope < 0.0):
        raise ValueError(
            f"Fitted slope m = {slope!r} >= 0; Eq. (3.18) requires m < 0 "
            "for physical (production-driven) depletion. Data may not "
            "follow the p/z model."
        )
    if not (intercept > 0.0):
        raise ValueError(
            f"Fitted intercept b = {intercept!r} <= 0; cannot be a "
            "positive pi/zi."
        )

    g_initial = -intercept / slope

    pred = slope * gp + intercept
    resid = pz - pred
    ss_res = float(np.sum(resid * resid))
    ss_tot = float(np.sum((pz - float(np.mean(pz))) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0.0 else 1.0

    gp_ab: float | None = None
    if abandon_pz is not None:
        if not (abandon_pz > 0.0):
            raise ValueError(
                f"abandon_pz must be > 0, got {abandon_pz!r}"
            )
        if abandon_pz >= intercept:
            raise ValueError(
                f"abandon_pz = {abandon_pz!r} must be less than the "
                f"fitted intercept (pi/zi) = {intercept!r}."
            )
        gp_ab = (abandon_pz - intercept) / slope

    linearity_suspect = r2 < R2_LINEARITY_WARN
    intercept_suspect = False
    if len(points) >= 1:
        pi_over_zi = points[0].p_psia / points[0].z
        if pi_over_zi > 0.0:
            rel_err = abs(intercept - pi_over_zi) / pi_over_zi
            intercept_suspect = rel_err > INTERCEPT_REL_WARN

    return GasPZResult(
        g_initial_scf=g_initial,
        slope=slope,
        intercept=intercept,
        r_squared=r2,
        gp_at_abandonment_scf=gp_ab,
        linearity_suspect=linearity_suspect,
        intercept_suspect=intercept_suspect,
        predicted_pz=tuple(float(x) for x in pred),
        predicted_gp=tuple(float(x) for x in gp),
    )
