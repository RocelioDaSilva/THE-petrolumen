"""Chapter 17 â€” Hydraulic Fracturing (pp. 17/251 â€“ 17/265)."""
from __future__ import annotations
import math


def overburden(rho, H_ft) -> float:
    """Eq. 17.1 (p. 17/252). [psi]"""
    return rho * H_ft / 144.0


def breakdown_pressure(sv, alpha, pp, nu, stect, T0) -> float:
    """Terzaghi breakdown â€” Eq. 17.5 (p. 17/253). [psi]"""
    sh_min = (nu / (1 - nu)) * (sv - alpha*pp) + alpha*pp
    sh_max = sh_min + stect
    return 3*sh_min - sh_max + T0 - pp


def kgd_width(q_bpm, mu_cp, nu, xf_ft, G_psi, hf_ft) -> float:
    """KGD average width â€” Eq. 17.8 (p. 17/254). [in]"""
    return 0.29 * ((q_bpm * mu_cp * (1 - nu) * xf_ft**2)
                   / (G_psi * hf_ft))**0.25 * (math.pi/4)


def pkn_width(q_bpm, mu_cp, nu, xf_ft, G_psi, gamma=0.75) -> float:
    """PKN average width â€” Eq. 17.9 (p. 17/255). [in]"""
    return 0.3 * ((q_bpm * mu_cp * (1 - nu) * xf_ft) / G_psi)**0.25 \
        * (math.pi / (4*gamma))


def fold_of_increase(re_ft, rw_ft, Sf) -> float:
    """J/J_o â€” Eq. 17.12 (p. 17/257)."""
    return math.log(re_ft / rw_ft) / math.log(re_ft / rw_ft + Sf)


def treatment_surface_pressure(pbd, rho, D_ft, q_bpm, mu, d_in) -> float:
    """Eqs. 17.18â€“17.19 (p. 17/259). [psia]"""
    dph = 0.433 * rho * D_ft
    dpf = (518 * (rho**0.79) * (q_bpm**1.79) * (mu**0.207) * D_ft
           / (1000 * d_in**4.79))
    return pbd - dph + dpf