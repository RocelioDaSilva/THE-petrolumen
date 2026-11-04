"""Chapter 12 â€” Sucker Rod Pumping (pp. 12/161 â€“ 12/180)."""
from __future__ import annotations
import math


def machinery_factor(c_over_h, balanced="conventional") -> float:
    """Eq. 12.11 (p. 12/168)."""
    return 1 + c_over_h if balanced == "conventional" else 1 - c_over_h


def F1(S_in, N_spm, c_over_h, balanced="conventional") -> float:
    """Eq. 12.20 (p. 12/168)."""
    sign = 1 if balanced == "conventional" else -1
    return S_in * N_spm**2 * (1 + sign*c_over_h) / 70471.2


def F2(S_in, N_spm, c_over_h, balanced="conventional") -> float:
    """Eq. 12.23 (p. 12/169)."""
    sign = 1 if balanced == "conventional" else -1
    return S_in * N_spm**2 * (1 - sign*c_over_h) / 70471.2


def prl_max(Wf, Wr, F1_val) -> float:
    """Eq. 12.19 (p. 12/168). [lbf]"""
    return Wf + (0.9 + F1_val) * Wr


def prl_min(Wr, F2_val) -> float:
    """Eq. 12.22 (p. 12/169). [lbf]"""
    return (0.9 - F2_val) * Wr


def peak_torque(S_in, Wf, N_spm, Wr) -> float:
    """Eq. 12.30 (p. 12/169). [in-lb]"""
    return 0.25 * S_in * (Wf + 2 * S_in * N_spm**2 * Wr / 70471.2)


def counterbalance(Wf, Wr, S_in, N_spm, c_over_h) -> float:
    """Eq. 12.26 (p. 12/169). [lbf]"""
    return 0.5*Wf + Wr * (0.9 + S_in * N_spm**2 * c_over_h / 70471.2)


def speed_limit(S_in, c_over_h, L=0.5, balanced="conventional") -> float:
    """Eq. 12.34â€“12.35 (p. 12/169). [SPM]"""
    sign = 1 if balanced == "conventional" else -1
    return math.sqrt(70471.2 * L / (S_in * (1 + sign*c_over_h)))


def plunger_production(Ap, N_spm, Sp, Er, Bo) -> float:
    """Eq. 12.36 (p. 12/170). [stb/day]"""
    return 0.1484 * Ap * N_spm * Sp * Er / Bo