"""Chapter 14 â€” Other Artificial Lift Methods (pp. 14/207 â€“ 14/223)."""
from __future__ import annotations
import math


def pump_head(dp_psi) -> float:
    """ESP head â€” Eq. 14.1 (p. 14/208). [ft]"""
    return dp_psi / 0.433


def min_pump_depth(D_ft, pwf, p_suction, gamma_L) -> float:
    """Eq. 14.2 (p. 14/210). [ft]"""
    return D_ft - (pwf - p_suction) / (0.433 * gamma_L)


def hpp_flow_ratio(q_eng, A_p, A_e) -> float:
    """Eq. 14.3 (p. 14/211)."""
    return q_eng * A_p / A_e


def hpp_net_lift(Dp_ft, p_intake, Gb) -> float:
    """Eq. 14.9 (p. 14/212)."""
    return Dp_ft - p_intake / Gb


def pcp_displacement(D_in, E_in, Ps_ft) -> float:
    """Eq. 14.12 (p. 14/214). [ft3/rev]"""
    return 0.028 * D_in * E_in * Ps_ft


def pcp_rate(D_in, E_in, Ps_ft, N_rpm, Qs=0.0) -> float:
    """Eq. 14.13 (p. 14/214). [bbl/day]"""
    return 7.12 * D_in * E_in * Ps_ft * N_rpm - Qs


def plunger_glr_min(D_ft) -> float:
    """Turner rule for plunger lift â€” Eq. 14.23 (p. 14/218). [scf/bbl]"""
    return 400.0 * D_ft / 1000.0