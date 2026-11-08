"""Pseudosteady-state flow and drainage volume.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 7, Sec. 7, pp. 242-246, Eqs. (7.47)-(7.51), (7.61)-(7.63),
Table 7.2; Ch. 7 Eq. (7.6), p. 217.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

PW_COEF = 162.6          # Eq. (7.47) leading coefficient
A_SHAPE = 4.0            # Eq. (7.47) log numerator constant
EULER_SHAPE = 1.781      # Eq. (7.47) log denominator constant
TIME_COEF = 0.2339       # Eq. (7.47) time-term coefficient
STDY_COEF = 0.00708      # Eq. (7.50)
STEADY_OFFSET = 0.75     # Eq. (7.50)
TPSS_COEF = 1200.0       # Eq. (7.6)


@dataclass(frozen=True)
class PseudosteadyResult:
    mode: Literal["pwf", "area_from_slope", "re_from_area", "tpss"]
    pwf_psia: float | None
    log_term_psi: float | None
    time_term_psi: float | None
    area_ft2: float | None
    r_e_ft: float | None
    t_pss_hr: float | None


def pseudosteady_pwf(
    pi_psia: float,
    q_stb_d: float,
    mu_cp: float,
    B_bbl_stb: float,
    k_md: float,
    h_ft: float,
    A_ft2: float,
    CA: float,
    rw_ft: float,
    t_hr: float,
    phi: float,
    ct_psi_inv: float,
) -> PseudosteadyResult:
    """pwf(t) in pseudosteady state (Eq. 7.47, p. 243).

    Args:
        pi_psia: Initial pressure at start of pseudosteady, psia (> 0).
        q_stb_d: Production rate, STB/day (> 0).
        mu_cp: Viscosity, cp (> 0).
        B_bbl_stb: FVF, bbl/STB (> 0).
        k_md: Permeability, md (> 0).
        h_ft: Thickness, ft (> 0).
        A_ft2: Drainage area, ft^2 (> 0).
        CA: Shape factor (Table 7.2, p. 245; > 0).
        rw_ft: Wellbore radius, ft (> 0).
        t_hr: Time since pseudosteady start, hr (>= 0).
        phi: Porosity, fraction (0, 1).
        ct_psi_inv: Total compressibility, psi^-1 (> 0).

    Returns:
        PseudosteadyResult with pwf and term decomposition.
    """
    for name, v in [
        ("pi_psia", pi_psia), ("q_stb_d", q_stb_d), ("mu_cp", mu_cp),
        ("B_bbl_stb", B_bbl_stb), ("k_md", k_md), ("h_ft", h_ft),
        ("A_ft2", A_ft2), ("CA", CA), ("rw_ft", rw_ft),
        ("ct_psi_inv", ct_psi_inv),
    ]:
        if not (v > 0.0):
            raise ValueError(f"{name} must be > 0, got {v!r}")
    if not (0.0 < phi < 1.0):
        raise ValueError(f"phi must be in (0, 1), got {phi!r}")
    if not (t_hr >= 0.0):
        raise ValueError(f"t_hr must be >= 0, got {t_hr!r}")

    log_arg = A_SHAPE * A_ft2 / (EULER_SHAPE * CA * rw_ft * rw_ft)
    if not (log_arg > 0.0):
        raise ValueError(
            f"log argument 4A/(1.781 CA rw^2) = {log_arg!r} <= 0"
        )
    log_term = PW_COEF * q_stb_d * mu_cp * B_bbl_stb / (k_md * h_ft) \
        * math.log10(log_arg)
    time_term = TIME_COEF * q_stb_d * B_bbl_stb * t_hr \
        / (A_ft2 * h_ft * phi * ct_psi_inv)
    pwf = pi_psia - log_term - time_term
    return PseudosteadyResult(
        mode="pwf",
        pwf_psia=pwf,
        log_term_psi=log_term,
        time_term_psi=time_term,
        area_ft2=None, r_e_ft=None, t_pss_hr=None,
    )


def drainage_area_from_slope(
    m_prime_psi_per_hr: float,
    q_stb_d: float,
    B_bbl_stb: float,
    h_ft: float,
    phi: float,
    ct_psi_inv: float,
) -> PseudosteadyResult:
    """Drainage area from cartesian slope (Eq. 7.63, p. 254)."""
    if not (m_prime_psi_per_hr < 0.0):
        raise ValueError(
            f"m_prime_psi_per_hr must be < 0 (production), "
            f"got {m_prime_psi_per_hr!r}"
        )
    for name, v in [
        ("q_stb_d", q_stb_d), ("B_bbl_stb", B_bbl_stb),
        ("h_ft", h_ft), ("ct_psi_inv", ct_psi_inv),
    ]:
        if not (v > 0.0):
            raise ValueError(f"{name} must be > 0, got {v!r}")
    if not (0.0 < phi < 1.0):
        raise ValueError(f"phi must be in (0, 1), got {phi!r}")

    A = (
        -TIME_COEF * q_stb_d * B_bbl_stb
        / (m_prime_psi_per_hr * h_ft * phi * ct_psi_inv)
    )
    return PseudosteadyResult(
        mode="area_from_slope",
        pwf_psia=None, log_term_psi=None, time_term_psi=None,
        area_ft2=A, r_e_ft=None, t_pss_hr=None,
    )


def re_from_area(A_ft2: float) -> PseudosteadyResult:
    """Equivalent drainage radius from area: r_e = sqrt(A/pi)."""
    if not (A_ft2 > 0.0):
        raise ValueError(f"A_ft2 must be > 0, got {A_ft2!r}")
    return PseudosteadyResult(
        mode="re_from_area",
        pwf_psia=None, log_term_psi=None, time_term_psi=None,
        area_ft2=A_ft2, r_e_ft=math.sqrt(A_ft2 / math.pi), t_pss_hr=None,
    )


def time_to_pseudosteady(
    phi: float, mu_cp: float, ct_psi_inv: float,
    re_ft: float, k_md: float,
) -> PseudosteadyResult:
    """Time to reach pseudosteady (Eq. 7.6, p. 217)."""
    if not (0.0 < phi < 1.0):
        raise ValueError(f"phi must be in (0, 1), got {phi!r}")
    for name, v in [
        ("mu_cp", mu_cp), ("ct_psi_inv", ct_psi_inv),
        ("re_ft", re_ft), ("k_md", k_md),
    ]:
        if not (v > 0.0):
            raise ValueError(f"{name} must be > 0, got {v!r}")
    t_pss = TPSS_COEF * phi * mu_cp * ct_psi_inv * re_ft * re_ft / k_md
    return PseudosteadyResult(
        mode="tpss",
        pwf_psia=None, log_term_psi=None, time_term_psi=None,
        area_ft2=None, r_e_ft=re_ft, t_pss_hr=t_pss,
    )
