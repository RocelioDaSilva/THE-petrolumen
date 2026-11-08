"""Abnormally pressured gas p/z correction (Bernard, Eq. 3.26).

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 3, Sec. 8, pp. 97-99, Eq. (3.26) and Fig. 3.13.
"""

from __future__ import annotations

from dataclasses import dataclass

# Numerical guard for the covariance denominator
SINGULAR_REL_TOL = 1.0e-12

# Diagnostic threshold: C' below this is treated as "likely normal"
C_PRIME_SIGNIFICANCE = 1.0e-7  # psi^-1


@dataclass(frozen=True)
class GeopressuredPZPoint:
    p_psia: float
    Gp_scf: float
    z: float


@dataclass(frozen=True)
class GeopressuredPZResult:
    g_initial_scf: float
    c_prime_psi_inv: float
    a_primes: tuple[float, ...]
    b_primes: tuple[float, ...]
    residuals: tuple[float, ...]
    likely_normal: bool
    late_time_diverge: bool


def geopressured_pz(
    points: list[GeopressuredPZPoint],
    pi_psia: float | None = None,
    zi: float | None = None,
) -> GeopressuredPZResult:
    """Fit Bernard Eq. (3.26) for geopressured gas reservoirs.

    Implements the A'/B' fitting procedure from Craft, Hawkins, Terry
    (1991), Ch. 3, Sec. 8, pp. 97-99 (Eq. 3.26 and the auxiliary
    quantities on p. 98). Requires at least 3 points.

    Args:
        points: List of GeopressuredPZPoint, at least 3.
        pi_psia: Optional initial pressure; defaults to the first
            point's p_psia.
        zi: Optional initial z; defaults to the first point's z.

    Returns:
        GeopressuredPZResult with G, C', A'/B' arrays, residuals, and
        diagnostic flags.

    Raises:
        ValueError: fewer than 3 points, invalid input, singular fit,
            or non-positive G.
    """
    n = len(points)
    if n < 3:
        raise ValueError(
            f"At least 3 points required for Bernard fit, got {n}"
        )

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

    if pi_psia is None:
        pi = points[0].p_psia
    else:
        if not (pi_psia > 0.0):
            raise ValueError(f"pi_psia must be > 0, got {pi_psia!r}")
        pi = float(pi_psia)
    if zi is None:
        z_init = points[0].z
    else:
        if not (zi > 0.0):
            raise ValueError(f"zi must be > 0, got {zi!r}")
        z_init = float(zi)

    pi_over_zi = pi / z_init

    # Build A' and B' arrays
    a_primes: list[float] = []
    b_primes: list[float] = []
    pz: list[float] = []
    gp: list[float] = []
    for i, pt in enumerate(points):
        dp = pi - pt.p_psia
        if dp <= 0.0:
            raise ValueError(
                f"points[{i}]: pi - p = {dp!r} <= 0; geopressure "
                "correction requires a positive pressure drop."
            )
        pz_i = pt.p_psia / pt.z
        a_p = (pz_i - pi_over_zi) / (dp * pz_i)
        b_p = pi_over_zi / (dp * pz_i) * pt.Gp_scf
        a_primes.append(a_p)
        b_primes.append(b_p)
        pz.append(pz_i)
        gp.append(pt.Gp_scf)

    sum_A = sum(a_primes)
    sum_B = sum(b_primes)
    sum_AB = sum(a * b for a, b in zip(a_primes, b_primes))
    sum_BB = sum(b * b for b in b_primes)

    denom = sum_AB - sum_A * (sum_B / n)
    scale = max(abs(sum_AB), 1.0)
    if abs(denom) <= SINGULAR_REL_TOL * scale:
        raise ValueError(
            f"Bernard fit denominator |{denom:.3e}| <= tol*"
            f"{scale:.3e}; data cannot separate G from C'. "
            "Supply more points spanning a wider pressure range."
        )

    numerator = sum_B * (sum_B / n) - sum_BB
    g_initial = numerator / denom
    if not (g_initial > 0.0):
        raise ValueError(
            f"Bernard fit produced G = {g_initial!r} <= 0; "
            "inputs or data inconsistent with Eq. (3.26)."
        )

    c_prime = sum_A / n + (1.0 / g_initial) * (sum_B / n)

    # Residuals: r_k = p/z - [pi/zi - (pi/zi)*Gp/G] / (1 - C'*dp)
    residuals: list[float] = []
    late_time_diverge = False
    for i, pt in enumerate(points):
        dp = pi - pt.p_psia
        denom_k = 1.0 - c_prime * dp
        if abs(denom_k) < 1.0e-12:
            late_time_diverge = True
            residuals.append(float("nan"))
            continue
        pred = (pi_over_zi - pi_over_zi * gp[i] / g_initial) / denom_k
        residuals.append(pz[i] - pred)

    likely_normal = abs(c_prime) < C_PRIME_SIGNIFICANCE

    return GeopressuredPZResult(
        g_initial_scf=g_initial,
        c_prime_psi_inv=c_prime,
        a_primes=tuple(a_primes),
        b_primes=tuple(b_primes),
        residuals=tuple(residuals),
        likely_normal=likely_normal,
        late_time_diverge=late_time_diverge,
    )
