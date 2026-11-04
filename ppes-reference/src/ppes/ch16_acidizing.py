"""Chapter 16 â€” Matrix Acidizing (pp. 16/243 â€“ 16/249)."""
from __future__ import annotations
import math


def gravimetric_power(Ca, n_m, MW_m, n_a, MW_a) -> float:
    """Eq. 16.1 (p. 16/244). [lbm mineral / lbm solution]"""
    return Ca * n_m * MW_m / (n_a * MW_a)


def volumetric_power(beta, rho_a, rho_m) -> float:
    """Eq. 16.2 (p. 16/244). [ft3 mineral / ft3 solution]"""
    return beta * rho_a / rho_m


def preflush_volume(r_a, r_w, phi, C_m, beta, rho_a, rho_m) -> float:
    """Eqs. 16.3â€“16.5 (p. 16/245). [ft3 per ft pay]"""
    Vm = math.pi * (r_a**2 - r_w**2) * (1 - phi) * C_m
    Vp = math.pi * (r_a**2 - r_w**2) * phi
    X = volumetric_power(beta, rho_a, rho_m)
    return Vm / X + Vp + Vm


def max_injection_rate(k, h, pbd, p, dpsf, mu_a, re_ft, rw_ft, S) -> float:
    """Eq. 16.6 (p. 16/246). [bbl/min]"""
    return (4.917e-6 * k * h * (pbd - p - dpsf)
            / (mu_a * math.log(0.472 * re_ft / rw_ft) + S))