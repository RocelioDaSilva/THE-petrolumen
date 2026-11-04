"""Chapter 5 â€” Choke Performance (pp. 5/59 â€“ 5/67)."""
from __future__ import annotations
import math
from dataclasses import dataclass


def critical_ratio(k: float) -> float:
    """Critical pressure ratio â€” Eq. 5.1 (p. 5/60)."""
    return (2.0/(k + 1.0))**(k/(k - 1.0))


def q_sonic_gas(cd, A2_in2, p_up, t_up_R, gamma_g, k) -> float:
    """Sonic gas choke â€” Eq. 5.8 (p. 5/62). [Mscf/day]"""
    return 879*cd*A2_in2*p_up*math.sqrt(
        (k/(gamma_g*t_up_R)) * (2.0/(k+1.0))**((k+1.0)/(k-1.0)))


def q_subsonic_gas(cd, A2_in2, p_up, p_dn, t_up_R, gamma_g, k) -> float:
    """Subsonic gas choke â€” Eq. 5.5 (p. 5/61). [Mscf/day]"""
    r = p_dn/p_up
    term = r**(2.0/k) - r**((k+1.0)/k)
    return 1248*cd*A2_in2*p_up*math.sqrt(
        (k/((k-1.0)*gamma_g*t_up_R)) * term)


def q_liquid(cd, d2_in, dp_psi, rho) -> float:
    """Liquid choke â€” Eq. 5.3 (p. 5/60). [bbl/day]"""
    return 8074 * cd * d2_in**2 * math.sqrt(dp_psi / rho)


_GILBERT = {
    "Gilbert":    (10.00, 0.546, 1.89),
    "Ros":        (17.40, 0.500, 1.89),
    "Baxendell":  (9.56,  0.546, 1.93),
    "Achong":     (3.82,  0.650, 1.88),
    "Pilehvari":  (46.67, 0.313, 2.11),
}


def gilbert_choke(q_bpd, glr, choke_64, correlation="Gilbert") -> float:
    """Gilbert-type multiphase choke â€” Eq. 5.12 (p. 5/63). [psia]"""
    C, m, n = _GILBERT[correlation]
    return C * (glr**m) * q_bpd / (choke_64**n)


@dataclass
class SachdevaInput:
    d2_in: float
    cd: float
    p1: float
    p2: float
    t1_F: float
    t2_F: float
    x1: float
    gamma_L: float
    gamma_g: float
    Cp_gas: float = 0.24
    Cv_gas: float = 0.171429
    Cp_liquid: float = 0.8


def sachdeva_flow(inp: SachdevaInput) -> dict:
    """Sachdeva multiphase choke â€” Eqs. 5.13â€“5.21 (p. 5/64).

    TODO: implement iterative critical-ratio solver, then compute
    q_liq and q_gas. See book Table 5.4 for a worked example.
    """
    raise NotImplementedError("Implement per Eqs. 5.13â€“5.21, p. 5/64.")