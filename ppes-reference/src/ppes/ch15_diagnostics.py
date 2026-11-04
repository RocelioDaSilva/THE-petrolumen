"""Chapter 15 â€” Well Problem Identification (pp. 15/227 â€“ 15/242)."""
from __future__ import annotations
import math


def turner_slip_velocity(sigma, rho_L, rho_g, Cd=0.44) -> float:
    """Turner slip velocity â€” Eq. 15.23 (p. 15/233). [ft/s]"""
    return (1.3 * (sigma**0.25) * ((rho_L - rho_g)**0.25)
            / (Cd**0.25 * rho_g**0.5))


def turner_min_gas_rate(v_sl, A_ft2, p, T_R, z) -> float:
    """Turner minimum rate â€” Eq. 15.24 (p. 15/234). [MMcf/d]"""
    return 3.06 * p * v_sl * A_ft2 / (T_R * z)


def skin_decomposition(SD=0.0, SCu=0.0, SP=0.0, SPS=0.0) -> float:
    """Skin decomposition â€” Eq. 15.22 (p. 15/230)."""
    return SD + SCu + SP + SPS