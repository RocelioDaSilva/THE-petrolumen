"""Transient drawdown analysis with skin.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 7, Sec. 6.1 pp. 234-241, Sec. 10.1 pp. 253-258,
Eqs. (7.37), (7.58)-(7.63), (7.66)-(7.67), Example 7.2.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

# Book constants (Eqs. 7.60, 7.63, 7.67)
K_COEF = 162.6
S_COEF = 1.151
S_LOG_CONST = 3.23
A_COEF = 0.2339

# Guard: minimum log-span for the semilog fit (log10 decades)
MIN_LOG_SPAN = 0.30

# Guard: minimum number of pseudosteady points if requested
MIN_POINTS = 2


@dataclass(frozen=True)
class DrawdownResult:
    m_psi_per_cycle: float
    p1hr_psia: float
    k_md: float
    skin: float
    r_squared_semilog: float
    drainage_area_ft2: float | None
    m_prime_psi_per_hr: float | None
    r_squared_cartesian: float | None


def _r_squared(y: np.ndarray, pred: np.ndarray) -> float:
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - float(np.mean(y))) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0.0 else 1.0


def _validate_common(
    q: float, mu: float, B: float, h: float,
    phi: float, ct: float, rw: float, pi: float,
) -> None:
    if not (q > 0.0):
        raise ValueError(f"q_stb_d must be > 0, got {q!r}")
    if not (mu > 0.0):
        raise ValueError(f"mu_cp must be > 0, got {mu!r}")
    if not (B > 0.0):
        raise ValueError(f"B_bbl_stb must be > 0, got {B!r}")
    if not (h > 0.0):
        raise ValueError(f"h_ft must be > 0, got {h!r}")
    if not (0.0 < phi < 1.0):
        raise ValueError(f"phi must be in (0, 1), got {phi!r}")
    if not (ct > 0.0):
        raise ValueError(f"ct_psi_inv must be > 0, got {ct!r}")
    if not (rw > 0.0):
        raise ValueError(f"rw_ft must be > 0, got {rw!r}")
    if not (pi > 0.0):
        raise ValueError(f"pi_psia must be > 0, got {pi!r}")


def drawdown_analysis(
    q_stb_d: float,
    mu_cp: float,
    B_bbl_stb: float,
    h_ft: float,
    phi: float,
    ct_psi_inv: float,
    rw_ft: float,
    pi_psia: float,
    semilog_points: list[tuple[float, float]],
    pseudosteady_points: list[tuple[float, float]] | None = None,
) -> DrawdownResult:
    """Transient drawdown interpretation (Craft Eqs. 7.37, 7.58-7.67).

    The caller is responsible for supplying points that lie on the
    semilog straight-line (transient) region. Book Example 7.2 uses
    the first six points for the transient fit and the last three for
    the cartesian pseudosteady fit.

    Args:
        q_stb_d: Flow rate, STB/day (> 0).
        mu_cp: Viscosity, cp (> 0).
        B_bbl_stb: FVF, bbl/STB (> 0).
        h_ft: Net pay thickness, ft (> 0).
        phi: Porosity, fraction (0, 1).
        ct_psi_inv: Total compressibility, psi^-1 (> 0).
        rw_ft: Wellbore radius, ft (> 0).
        pi_psia: Initial reservoir pressure, psia (> 0).
        semilog_points: List of (t_hr, pwf_psia) on transient region.
        pseudosteady_points: Optional list of (t_hr, pwf_psia) on
            pseudosteady region (>= 2 points) for drainage-area fit.

    Returns:
        DrawdownResult.

    Raises:
        ValueError: invalid input, fewer than 2 points, short log-span,
            non-physical slope, or non-positive k.
    """
    _validate_common(q_stb_d, mu_cp, B_bbl_stb, h_ft,
                     phi, ct_psi_inv, rw_ft, pi_psia)

    if len(semilog_points) < MIN_POINTS:
        raise ValueError(
            f"At least {MIN_POINTS} semilog points required, got "
            f"{len(semilog_points)}"
        )

    t_arr = np.empty(len(semilog_points), dtype=float)
    p_arr = np.empty(len(semilog_points), dtype=float)
    for i, (t, p) in enumerate(semilog_points):
        if not (t > 0.0):
            raise ValueError(
                f"semilog_points[{i}] time must be > 0, got {t!r}"
            )
        if not (p > 0.0):
            raise ValueError(
                f"semilog_points[{i}] pwf must be > 0, got {p!r}"
            )
        t_arr[i] = t
        p_arr[i] = p

    log_t = np.log10(t_arr)
    span = float(np.max(log_t) - np.min(log_t))
    if span < MIN_LOG_SPAN:
        raise ValueError(
            f"Semilog time span is {span:.3f} decades < {MIN_LOG_SPAN}; "
            "slope will be poorly conditioned. Supply points spanning "
            "at least a third decade."
        )

    # Eq. (7.58): pwf = b + m*log10(t). polyfit returns [m, b].
    m, b = np.polyfit(log_t, p_arr, 1)
    m = float(m)
    b = float(b)
    if not (m < 0.0):
        raise ValueError(
            f"Fitted semilog slope m = {m!r} >= 0; a drawdown must "
            "produce declining pwf."
        )
    r2_semilog = _r_squared(p_arr, m * log_t + b)

    # p1hr = value at t = 1 hr (log10(1) = 0)
    p1hr = b

    # Eq. (7.60): k = -162.6 q mu B / (m h)
    k = -K_COEF * q_stb_d * mu_cp * B_bbl_stb / (m * h_ft)
    if not (k > 0.0):
        raise ValueError(
            f"Computed k = {k!r} md <= 0; check inputs."
        )

    # Eq. (7.67): S
    log_arg = k / (phi * mu_cp * ct_psi_inv * rw_ft * rw_ft)
    if not (log_arg > 0.0):
        raise ValueError(
            "log(k/(phi*mu*ct*rw^2)) argument <= 0; check inputs."
        )
    skin = S_COEF * (
        (p1hr - pi_psia) / m - math.log10(log_arg) + S_LOG_CONST
    )

    # Optional pseudosteady cartesian fit for drainage area
    A_ft2: float | None = None
    m_prime: float | None = None
    r2_cart: float | None = None
    if pseudosteady_points is not None:
        if len(pseudosteady_points) < MIN_POINTS:
            raise ValueError(
                f"At least {MIN_POINTS} pseudosteady points required, got "
                f"{len(pseudosteady_points)}"
            )
        tt = np.empty(len(pseudosteady_points), dtype=float)
        pp = np.empty(len(pseudosteady_points), dtype=float)
        for i, (t, p) in enumerate(pseudosteady_points):
            if not (t > 0.0):
                raise ValueError(
                    f"pseudosteady_points[{i}] time must be > 0, got {t!r}"
                )
            if not (p > 0.0):
                raise ValueError(
                    f"pseudosteady_points[{i}] pwf must be > 0, got {p!r}"
                )
            tt[i] = t
            pp[i] = p
        mp, bp = np.polyfit(tt, pp, 1)
        mp = float(mp)
        bp = float(bp)
        if not (mp < 0.0):
            raise ValueError(
                f"Cartesian slope m' = {mp!r} >= 0; pseudosteady flow "
                "must produce declining pwf with time."
            )
        # Eq. (7.63): A = -0.2339 q B / (m' h phi ct)
        A_ft2 = -A_COEF * q_stb_d * B_bbl_stb / (mp * h_ft * phi * ct_psi_inv)
        m_prime = mp
        r2_cart = _r_squared(pp, mp * tt + bp)

    return DrawdownResult(
        m_psi_per_cycle=m,
        p1hr_psia=p1hr,
        k_md=k,
        skin=skin,
        r_squared_semilog=r2_semilog,
        drainage_area_ft2=A_ft2,
        m_prime_psi_per_hr=m_prime,
        r_squared_cartesian=r2_cart,
    )
