"""Chapter 5 -- Choke Performance."""
import math
from dataclasses import dataclass

_GILBERT = {
    "Gilbert": (10.00, 0.546, 1.89),
    "Ros": (17.40, 0.500, 1.89),
    "Baxendell": (9.56, 0.546, 1.93),
    "Achong": (3.82, 0.650, 1.88),
    "Pilehvari": (46.67, 0.313, 2.11),
}

def critical_ratio(k) -> float:
    """Eq. 5.1."""
    return (2.0/(k+1.0))**(k/(k-1.0))

def q_sonic_gas(cd, A2_in2, p_up, t_up_R, gamma_g, k) -> float:
    """Eq. 5.8. [Mscf/day]"""
    return 879*cd*A2_in2*p_up*math.sqrt(
        (k/(gamma_g*t_up_R))*(2.0/(k+1.0))**((k+1.0)/(k-1.0)))

def q_subsonic_gas(cd, A2_in2, p_up, p_dn, t_up_R, gamma_g, k) -> float:
    """Eq. 5.5. [Mscf/day]"""
    r = p_dn/p_up
    term = r**(2.0/k) - r**((k+1.0)/k)
    return 1248*cd*A2_in2*p_up*math.sqrt(
        (k/((k-1.0)*gamma_g*t_up_R))*term)

def q_liquid(cd, d2_in, dp_psi, rho) -> float:
    """Eq. 5.3. [bbl/day]"""
    return 8074*cd*d2_in**2*math.sqrt(dp_psi/rho)

def gilbert_choke(q_bpd, glr, choke_64, correlation="Gilbert") -> float:
    """Eq. 5.12. [psia]"""
    C, m, n = _GILBERT[correlation]
    return C*(glr**m)*q_bpd/(choke_64**n)

def choke_downstream_temperature(t_up_R, p_up, p_dn, k,
                                   z_up=1.0, z_out=1.0) -> float:
    """Eq. 5.11."""
    return t_up_R*(z_up/z_out)*(p_dn/p_up)**((k-1)/k)

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

def sachdeva_critical_ratio(inp, tol=1e-9, max_iter=100) -> float:
    """Eq. 5.13."""
    from scipy.optimize import brentq
    k = inp.Cp_gas/inp.Cv_gas
    n = 1 + inp.x1*(inp.Cp_gas - inp.Cv_gas)/(
        inp.x1*inp.Cv_gas + (1-inp.x1)*inp.Cp_liquid)
    rhoL = inp.gamma_L*62.4; VL = 1.0/rhoL
    MWg = 28.97*inp.gamma_g
    VG1 = 10.73*(inp.t1_F + 460)/(inp.p1*MWg)
    def VG2(y): return VG1*y**(-1.0/k)
    def res(y):
        num = (k/(k-1)) + (1-inp.x1)*VL*(1-y)/(inp.x1*VG1)
        den = ((k-1) + n/2 + n*(1-inp.x1)*VL/(inp.x1*VG2(y))
               + (n/2)*((1-inp.x1)*VL/(inp.x1*VG2(y)))**2)
        return num/den - y**(k-1)
    return brentq(res, 1e-6, 1-1e-6, xtol=tol, maxiter=max_iter)

def sachdeva_flow(inp, max_iter=50, tol=1e-4) -> dict:
    """Full Sachdeva multiphase choke."""
    from .ch02_pvt import z_hall_yarborough, pseudo_critical_from_sg
    y_c = sachdeva_critical_ratio(inp)
    y_a = inp.p2/inp.p1
    y_u = y_c if y_a < y_c else y_a
    regime = "critical" if y_a < y_c else "subcritical"
    p_pc, t_pc = pseudo_critical_from_sg(inp.gamma_g)
    zv = 0.95; G2 = 0.0; q_liq = q_gas = 0.0
    for _ in range(max_iter):
        k = inp.Cp_gas/inp.Cv_gas
        rhoL = inp.gamma_L*62.4; VL = 1.0/rhoL
        MWg = 28.97*inp.gamma_g
        VG1 = zv*10.73*(inp.t1_F+460)/(inp.p1*MWg)
        VG2 = VG1*y_u**(-1.0/k)
        rho_m2 = 1.0/(inp.x1*VG2 + (1-inp.x1)*VL)
        bracket = ((1-inp.x1)*(1-y_u)/rhoL
                   + (inp.x1*k/(k-1))*(VG1 - y_u*VG2))
        G2 = inp.cd*math.sqrt(288*32.174*inp.p1*144*rho_m2*bracket)
        A2 = math.pi*(inp.d2_in/2/12)**2
        m = G2*A2
        mliq = (1-inp.x1)*m; mgas = inp.x1*m
        q_liq = mliq*86400/(rhoL*5.615)
        t2R = inp.t2_F + 460
        q_gas = mgas*10.73*t2R/(MWg*inp.p2)*86400/1e6
        zn = float(z_hall_yarborough(inp.p2/p_pc, t2R/t_pc))
        if abs(zn - zv) < tol: break
        zv = zn
    return dict(y_c=y_c, y_a=y_a, regime=regime, G2=G2,
                q_liq=q_liq, q_gas=q_gas, z_used=zv)
