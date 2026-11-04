"""Chapter 2 â€” Properties of Oil and Natural Gas (pp. 2/19 â€“ 2/27).

Every function cites the book equation number, page, units, and
validity range. Functions marked ``NotImplementedError`` (gas viscosity,
gas compressibility) are stubs to fill in following the same pattern.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.optimize import newton

MW_AIR = 28.97


# ---------------------------------------------------------------------------
# Oil
# ---------------------------------------------------------------------------
def rs_standing(p: float, t_F: float, api: float, gamma_g: float) -> float:
    """Solution GOR â€” Eq. 2.2 (p. 2/20). [scf/stb]

    Valid for p <= pb, 15 <= API <= 50, 0.55 <= gamma_g <= 0.90.
    """
    return gamma_g * ((p / 18.0) * (10**(0.0125*api)) / (10**(0.00091*t_F)))**1.2048


def rho_o(p: float, t_F: float, api: float, rs: float, gamma_g: float) -> float:
    """Oil density at p, T â€” Eq. 2.5 (p. 2/20). [lbm/ft3]"""
    gamma_o = 141.5 / (api + 131.5)
    num = 62.4 * gamma_o + 0.0136 * rs * gamma_g
    den = 0.972 + 0.000147 * (rs * math.sqrt(gamma_g / gamma_o) + 1.25*t_F)**1.175
    return num / den


def bo_standing(t_F: float, api: float, rs: float, gamma_g: float) -> float:
    """Oil FVF â€” Eq. 2.7 (p. 2/20). [rb/stb]"""
    gamma_o = 141.5 / (api + 131.5)
    return 0.9759 + 0.00012 * (rs * math.sqrt(gamma_g / gamma_o) + 1.25*t_F)**1.2


def mu_dead_oil(api: float, t_F: float) -> float:
    """Dead-oil viscosity â€” Eq. 2.8/2.9 (p. 2/21). [cp]"""
    A = 10**(0.43 + 8.33 / api)
    return (0.32 + 1.8e7 / api**4.53) * (360.0 / (t_F + 200.0))**A


def mu_sat_oil(rs: float, mu_od: float) -> float:
    """Saturated-oil viscosity â€” Eqs. 2.10â€“2.15 (p. 2/22). [cp]"""
    a = rs * (2.2e-7*rs - 7.4e-4)
    c = 8.62e-5 * rs
    d = 1.10e-3 * rs
    e = 3.74e-3 * rs
    b = 0.68/(10**c) + 0.25/(10**d) + 0.062/(10**e)
    return 10**a * mu_od**b


def mu_unsat_oil(p: float, pb: float, mu_od: float, mu_ob: float) -> float:
    """Unsaturated-oil viscosity â€” Eq. 2.16 (p. 2/22). [cp]"""
    return mu_ob + 0.001*(p - pb)*(0.024*mu_od**1.6 + 0.38*mu_ob**0.56)


# ---------------------------------------------------------------------------
# Gas
# ---------------------------------------------------------------------------
def z_brill_beggs(p_pr: float, t_pr: float) -> float:
    """Gas z-factor â€” Brill & Beggs, Eqs. 2.45â€“2.51 (p. 2/24)."""
    A = 1.39 * (t_pr - 0.92)**0.5 - 0.36*t_pr - 0.10
    E = 9.0 * (t_pr - 1.0)
    B = ((0.62 - 0.23*t_pr) * p_pr
         + (0.066/(t_pr - 0.86) - 0.037) * p_pr**2
         + 0.32 * p_pr**6 / 10**E)
    C = 0.132 - 0.32 * math.log10(t_pr)
    F = 0.3106 - 0.49*t_pr + 0.1824*t_pr**2
    return A + (1 - A)/math.exp(B) + C * p_pr**(10**F)


def z_hall_yarborough(p_pr: float, t_pr: float) -> float:
    """Gas z-factor â€” Hall & Yarborough, Eqs. 2.52â€“2.59 (p. 2/24)."""
    t_r = 1.0/t_pr
    A = 0.06125 * t_r * math.exp(-1.2*(1-t_r)**2)
    B = t_r * (14.76 - 9.76*t_r + 4.58*t_r**2)
    C = t_r * (90.7 - 242.2*t_r + 42.4*t_r**2)
    D = 2.18 + 2.82*t_r

    def f(Y):
        return (Y + Y**2 + Y**3 - Y**4)/(1-Y)**3 - A*p_pr - B*Y**2 + C*Y**D

    def df(Y):
        return ((1 + 4*Y + 4*Y**2 - 4*Y**3 + Y**4)/(1-Y)**4
                - 2*B*Y + C*D*Y**(D-1))

    Y = newton(f, x0=0.1, fprime=df, tol=1e-12, maxiter=200)
    return A * p_pr / Y


def pseudo_critical_from_sg(gamma_g: float) -> tuple[float, float]:
    """p_pc, T_pc from gamma_g â€” Eqs. 2.22â€“2.23 (p. 2/21)."""
    return (709.604 - 58.718*gamma_g, 170.491 + 307.344*gamma_g)


def rho_gas(p: float, t_R: float, gamma_g: float, z: float) -> float:
    """Gas density â€” Eq. 2.61 (p. 2/24). [lbm/ft3]"""
    return 2.7 * gamma_g * p / (z * t_R)


def bg(p: float, t_R: float, z: float) -> float:
    """Gas FVF â€” Eq. 2.62 (p. 2/25). [ft3/scf]"""
    return 0.0283 * z * t_R / p


def eg(p: float, t_R: float, z: float) -> float:
    """Gas expansion factor â€” Eq. 2.64 (p. 2/26). [scf/ft3]"""
    return 35.3 * p / (z * t_R)


def mu_gas_carr_kobayashi_burrows(gamma_g, t_R, y_N2=0.0, y_CO2=0.0, y_H2S=0.0):
    """Gas viscosity â€” Eqs. 2.35â€“2.41 (p. 2/23).

    TODO: implement per book pp. 2/23. Expected behavior: returns
    mu_g [cp] as a function of gamma_g, T, and impurity mole fractions.
    """
    raise NotImplementedError(
        "Implement Carr-Kobayashi-Burrows per Eq. 2.35â€“2.41, p. 2/23."
    )