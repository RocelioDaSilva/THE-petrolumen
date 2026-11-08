"""Transient line-source solution (Craft Eqs. 7.36-7.37, pp. 235-241)."""
from __future__ import annotations
import math
from dataclasses import dataclass
from scipy.special import expi

EI_COEF = 70.6
EI_TIME = 0.00105
EULER_GAMMA = 0.5772
LOG_APPROX_X = 0.01


@dataclass(frozen=True)
class TransientEiResult:
    p_psia: float
    dp_psi: float
    x_arg: float
    used_log_approx: bool


def transient_line_source(
    pi_psia: float, q_stb_d: float, mu_cp: float, B_bbl_stb: float,
    k_md: float, h_ft: float, phi: float, ct_psi_inv: float,
    r_ft: float, t_hr: float,
) -> TransientEiResult:
    """Pressure at (r, t) via Eq. (7.36).

    Args:
        pi_psia: Initial pressure, psia (> 0).
        q_stb_d: Production rate, STB/day (> 0).
        mu_cp: Viscosity, cp (> 0).
        B_bbl_stb: FVF, bbl/STB (> 0).
        k_md: Permeability, md (> 0).
        h_ft: Thickness, ft (> 0).
        phi: Porosity, fraction (0, 1).
        ct_psi_inv: Total compressibility, psi^-1 (> 0).
        r_ft: Observation radius, ft (> 0).
        t_hr: Time, hr (> 0).

    Returns:
        TransientEiResult.

    Raises:
        ValueError: any input out of physical range.
    """
    for name, v in [
        ("pi_psia", pi_psia), ("q_stb_d", q_stb_d), ("mu_cp", mu_cp),
        ("B_bbl_stb", B_bbl_stb), ("k_md", k_md), ("h_ft", h_ft),
        ("ct_psi_inv", ct_psi_inv), ("r_ft", r_ft), ("t_hr", t_hr),
    ]:
        if not (v > 0.0):
            raise ValueError(f"{name} must be > 0, got {v!r}")
    if not (0.0 < phi < 1.0):
        raise ValueError(f"phi must be in (0, 1), got {phi!r}")

    x = phi * mu_cp * ct_psi_inv * r_ft * r_ft / (EI_TIME * k_md * t_hr)
    if not (x > 0.0):
        raise ValueError(f"Ei argument x = {x!r} <= 0; check inputs.")

    if x < LOG_APPROX_X:
        # log approximation (book p. 239)
        neg_ei = -math.log(x) - EULER_GAMMA
        used_log = True
    else:
        neg_ei = -float(expi(-x))
        used_log = False

    coef = EI_COEF * q_stb_d * mu_cp * B_bbl_stb / (k_md * h_ft)
    dp = coef * neg_ei
    return TransientEiResult(
        p_psia=pi_psia - dp, dp_psi=dp, x_arg=x,
        used_log_approx=used_log,
    )
