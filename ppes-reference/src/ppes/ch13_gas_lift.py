"""Chapter 13 â€” Gas Lift (pp. 13/181 â€“ 13/206)."""
from __future__ import annotations
import math


def injection_glr(glr_opt, glr_formation) -> float:
    """Eq. 13.1 (p. 13/184). [scf/stb]"""
    return glr_opt - glr_formation


def required_gas_rate(glr_inj, q_o) -> float:
    """Eq. 13.2 (p. 13/184). [scf/day]"""
    return glr_inj * q_o


def valve_opening_pressure(pd, St, R, pt) -> float:
    """Eq. 13.42 (p. 13/193). [psig]"""
    return (1.0/(1.0 - R)) * pd + St - (R/(1.0 - R)) * pt


def valve_closing_pressure(pd, St, R) -> float:
    """Eq. 13.43 (p. 13/193). [psig]"""
    return pd + St * (1.0 - R)


def valve_depth_first(pk_s, dp_km, phf, Gs) -> float:
    """Eq. 13.49 (p. 13/199). [ft]"""
    return (pk_s - dp_km - phf) / (Gs - (pk_s - dp_km)/40000.0)


def valve_depth_i(pc_s, dp_cm, phf_d, Gs, Gfd, D_prev) -> float:
    """Eq. 13.55 (p. 13/199). [ft]"""
    return ((pc_s - dp_cm - phf_d + (Gs - Gfd)*D_prev)
            / (Gs - (pc_s - dp_cm)/40000.0))