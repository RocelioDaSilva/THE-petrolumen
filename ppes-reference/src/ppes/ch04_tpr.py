"""Chapter 4 â€” Wellbore Performance (pp. 4/45 â€“ 4/58).

Implemented: Chen friction (Eq. 4.5), Average T/z BHP (Eq. 4.54).
Stubs: Poettmannâ€“Carpenter, Guoâ€“Ghalambor, mHâ€“B, Cullenderâ€“Smith.
"""
from __future__ import annotations
import math


def friction_chen(re: float, rel_rough: float) -> float:
    """Fanning friction factor â€” Chen, Eq. 4.5 (p. 4/46)."""
    t1 = rel_rough / 3.7065
    t2 = (5.0452 / re) * math.log10(
        rel_rough**1.1098 / 2.8257 + (7.149/re)**0.8981)
    rhs = -4 * math.log10(t1 - t2)
    return 1.0 / (rhs**2)


def bhp_average_tz(phf, q_sc, gamma_g, d_i, L, theta_deg,
                   t_avg_R, z_avg, fM) -> float:
    """Gas-well BHP â€” Average T/z â€” Eq. 4.54 (p. 4/55). [psia]

    phf: psia, q_sc: Mscl/d, d_i: in, L: ft, t_avg_R: Â°R.
    """
    s = (0.0375 * gamma_g * L * math.cos(math.radians(theta_deg))
         / (z_avg * t_avg_R))
    es = math.exp(s)
    return math.sqrt(
        es * phf**2
        + (6.67e-4 * (es - 1) * fM * q_sc**2
           * z_avg**2 * t_avg_R**2)
          / (d_i**5 * math.cos(math.radians(theta_deg)))
    )


def poettmann_carpenter_bhp(*args, **kwargs) -> float:
    """Poettmannâ€“Carpenter pressure traverse â€” Eqs. 4.8â€“4.17 (p. 4/49).

    TODO: piecewise integration over dz. Returns p_wf [psia].
    """
    raise NotImplementedError("Implement per Eqs. 4.8â€“4.17, p. 4/49.")


def guo_ghalambor_bhp(*args, **kwargs) -> float:
    """Guoâ€“Ghalambor four-phase BHP â€” Eq. 4.18 (p. 4/50)."""
    raise NotImplementedError("Implement per Eq. 4.18, p. 4/50.")


def mhb_pressure_traverse(*args, **kwargs):
    """Modified Hagedornâ€“Brown traverse â€” Eqs. 4.26â€“4.48 (p. 4/52)."""
    raise NotImplementedError("Implement per Eqs. 4.26â€“4.48, p. 4/52.")


def cullender_smith_bhp(*args, **kwargs) -> float:
    """Cullenderâ€“Smith gas BHP â€” Eqs. 4.59â€“4.68 (p. 4/57)."""
    raise NotImplementedError("Implement per Eqs. 4.59â€“4.68, p. 4/57.")