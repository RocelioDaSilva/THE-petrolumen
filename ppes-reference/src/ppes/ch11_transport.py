"""Chapter 11 â€” Transportation Systems (pp. 11/133 â€“ 11/157)."""
from __future__ import annotations
import math


def triplex_hp_input(p_psi, d_in, l_in, N_spm, em=0.85) -> float:
    """Eq. 11.11 (p. 11/135)."""
    return p_psi * d_in**2 * l_in * N_spm / (168_067 * em)


def triplex_rate(d_in, l_in, N_spm, ev=0.95) -> float:
    """Eq. 11.8 (p. 11/135). [bbl/day]"""
    return 0.35 * ev * l_in * N_spm * d_in**2


def duplex_hp_input(p_psi, d1_in, d2_in, l_in, N_spm, em=0.85) -> float:
    """Eq. 11.22 (p. 11/136)."""
    return p_psi * (2*d1_in**2 - d2_in**2) * l_in * N_spm / (252_101 * em)


def recip_compressor_hp_per_mmscfd(p1, p2, t1_R, gamma_g, z1, k=1.25) -> float:
    """Eq. 11.26 (p. 11/139)."""
    return (k/(k-1)) * (3.027*14.7/520.0) * t1_R * (
        (p2/p1)**(z1*(k-1)/k) - 1.0)


def weymouth_horizontal(q_scfd, p1, p2, d_in, L_ft, gamma_g,
                        T_R, Tb_R=520, pb=14.7) -> float:
    """Weymouth horizontal â€” Eq. 11.101 (p. 11/147)."""
    return (18.062 * Tb_R / pb) * math.sqrt(
        (p1**2 - p2**2) * d_in**(16.0/3.0)
        / (gamma_g * T_R * L_ft))


def wall_thickness_internal(pd, D_in, sigma_y, eta=0.72,
                            Ew=1.0, Ft=1.0, t_a=0.0625) -> float:
    """Wall thickness â€” Eq. 11.116 (p. 11/149). [in]"""
    return pd * D_in / (2 * Ew * eta * sigma_y * Ft) + t_a