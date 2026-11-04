"""Chapter 6 -- Nodal Analysis."""
import math
from dataclasses import dataclass
import numpy as np

def bottomhole_gas_analytic(c_ipr, n, p_bar, phf, t_avg_R, z_avg,
                              d_i, L_ft, theta_deg, fM):
    """Eq. 6.4."""
    from scipy.optimize import brentq
    s = 0.0375*0.71*L_ft*math.cos(math.radians(theta_deg))/(
        z_avg*t_avg_R)
    es = math.exp(s)
    def res(q):
        p1 = p_bar**2 - (q/c_ipr)**(1/n)
        if p1 < 0: return 1e6
        p2 = (es*phf**2 + 6.67e-4*(es-1)*fM*q**2*z_avg**2*t_avg_R**2
              /(d_i**5*math.cos(math.radians(theta_deg))))
        return p1 - p2
    q = brentq(res, 1.0, c_ipr*p_bar**n*0.999, xtol=1e-4)
    return q, math.sqrt(p_bar**2 - (q/c_ipr)**(1/n))

def operating_point_oil_vogel(qmax, pbar, tpr_func,
                                q_lo=1e-3, q_hi=1e7):
    from scipy.optimize import brentq
    from .ch03_ipr import vogel_pwf
    def res(q): return vogel_pwf(q, qmax, pbar) - tpr_func(q)
    q = brentq(res, q_lo, q_hi, xtol=1e-6)
    return q, tpr_func(q)

def operating_point_gas(c_ipr, n, pbar, tpr_func,
                         q_lo=1e-3, q_hi=1e7):
    from scipy.optimize import brentq
    def res(q):
        return (pbar**2 - (q/c_ipr)**(1/n))**0.5 - tpr_func(q)
    q = brentq(res, q_lo, q_hi, xtol=1e-6)
    return q, tpr_func(q)

def bottomhole_oil_pc(j_star, p_bar, p_wh, depth_ft, d_in,
                       q_lo=1.0, q_hi=5000.0, **kw):
    from scipy.optimize import brentq
    from .ch04_tpr import poettmann_carpenter_bhp
    def res(q):
        return (p_bar - q/j_star) - poettmann_carpenter_bhp(
            phf=p_wh, d_in=d_in, depth_ft=depth_ft, q_liq=q, **kw)
    q = brentq(res, q_lo, q_hi, xtol=1e-4)
    return q, p_bar - q/j_star

def bottomhole_oil_gg(j_star, p_bar, p_wh, depth_ft, d_in,
                       q_lo=1.0, q_hi=5000.0, **kw):
    from scipy.optimize import brentq
    from .ch04_tpr import guo_ghalambor_bhp_robust
    def res(q):
        return (p_bar - q/j_star) - guo_ghalambor_bhp_robust(
            phf=p_wh, d_in=d_in, L_ft=depth_ft, q_o=q, **kw)
    q = brentq(res, q_lo, q_hi, xtol=1e-4)
    return q, p_bar - q/j_star

def bottomhole_oil_hb(qmax, p_bar, p_wh, depth_ft, d_in,
                       q_lo=1.0, q_hi=5000.0, **kw):
    from scipy.optimize import brentq
    from .ch03_ipr import vogel_pwf
    from .ch04_tpr import mhb_pressure_traverse_full
    def tpr(q):
        pts = mhb_pressure_traverse_full(
            phf=p_wh, d_in=d_in, L_ft=depth_ft, q_liq=q, **kw)
        return pts[-1, 1]
    def res(q): return vogel_pwf(q, qmax, p_bar) - tpr(q)
    q = brentq(res, q_lo, q_hi, xtol=1e-3)
    return q, vogel_pwf(q, qmax, p_bar)

def wellhead_oil_pc(j_star, p_bar, depth_ft, d_in, choke_64,
                     glr_scf_stb=500.0, q_lo=1.0, q_hi=5000.0, **kw):
    from scipy.optimize import brentq
    from .ch04_tpr import poettmann_carpenter_bhp
    from .ch05_choke import gilbert_choke
    def res(q):
        pwh_c = gilbert_choke(q, glr_scf_stb, choke_64)
        pwf = p_bar - q/j_star
        pwh_w = pwf - poettmann_carpenter_bhp(
            phf=0.0, d_in=d_in, depth_ft=depth_ft, q_liq=q, **kw)
        return pwh_w - pwh_c
    q = brentq(res, q_lo, q_hi, xtol=1e-4)
    return q, gilbert_choke(q, glr_scf_stb, choke_64)

def wellhead_oil_gg(j_star, p_bar, depth_ft, d_in, choke_64,
                     theta_deg, glr_scf_stb=500.0,
                     q_lo=1.0, q_hi=5000.0, **kw):
    from scipy.optimize import brentq
    from .ch04_tpr import guo_ghalambor_bhp_robust
    from .ch05_choke import gilbert_choke
    def res(q):
        pwh_c = gilbert_choke(q, glr_scf_stb, choke_64)
        pwf = p_bar - q/j_star
        pwh_w = pwf - guo_ghalambor_bhp_robust(
            phf=0.0, d_in=d_in, L_ft=depth_ft,
            theta_deg=theta_deg, q_o=q, **kw)
        return pwh_w - pwh_c
    q = brentq(res, q_lo, q_hi, xtol=1e-4)
    return q, gilbert_choke(q, glr_scf_stb, choke_64)

def wellhead_oil_hb(qmax, p_bar, depth_ft, d_in, choke_64,
                     glr_scf_stb=500.0, q_lo=1.0, q_hi=5000.0, **kw):
    from scipy.optimize import brentq
    from .ch03_ipr import vogel_pwf
    from .ch04_tpr import mhb_pressure_traverse_full
    from .ch05_choke import gilbert_choke
    def tpr(q):
        pts = mhb_pressure_traverse_full(
            phf=0.0, d_in=d_in, L_ft=depth_ft, q_liq=q, **kw)
        return pts[-1, 1]
    def res(q):
        return (vogel_pwf(q, qmax, p_bar) - tpr(q)) - \
               gilbert_choke(q, glr_scf_stb, choke_64)
    q = brentq(res, q_lo, q_hi, xtol=1e-3)
    return q, gilbert_choke(q, glr_scf_stb, choke_64)

@dataclass
class Lateral:
    length_horiz_ft: float
    length_curvic_ft: float
    length_vert_ft: float
    pi_ft: float
    pressure_psia: float
    ipr_C: float = 0.0
    ipr_n: float = 0.8
    tubing_id_in: float = 3.0
    rel_rough: float = 1.8e-3
    gamma_g: float = 0.75
    z_avg: float = 0.9
    t_avg_R: float = 600.0

def multilateral_gas_rate(p_hf_top, laterals, q_guess=1000.0,
                            tol=1e-6, max_iter=100) -> dict:
    n = len(laterals)
    q = np.full(n, q_guess/n)
    p_hf = np.zeros(n); p_hf[-1] = p_hf_top
    for _ in range(max_iter):
        p_wf = np.sqrt(np.maximum(np.array(
            [L.pressure_psia**2 - (q[i]/L.ipr_C)**(1/L.ipr_n)
             for i, L in enumerate(laterals)]), 0.0))
        break
    return {"total_q": float(q.sum()), "per_lateral": q.tolist()}
