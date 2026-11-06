"""Chapter 15 -- Well Problem Identification."""
import math
import numpy as np

def diagnostic_derivative(t, dp):
    """Eq. 15.7."""
    t = np.asarray(t); dp = np.asarray(dp)
    lt = np.log(t); pp = np.zeros_like(dp)
    if len(t) < 3: return pp
    for i in range(1, len(t)-1):
        pp[i] = (np.log(dp[i+1]) - np.log(dp[i-1]))/(lt[i+1] - lt[i-1])
    pp[0] = pp[1]; pp[-1] = pp[-2]
    return pp

def identify_flow_regime_from_derivative(t, p_prime):
    t = np.asarray(t, dtype=float)
    pp = np.asarray(p_prime, dtype=float)
    mask = (t > 0) & (pp > 0)
    if mask.sum() < 5: return "unknown"
    s = np.polyfit(np.log(t[mask]), np.log(pp[mask]), 1)[0]
    if abs(s) < 0.1: return "radial"
    if abs(s - 0.5) < 0.15: return "linear"
    if abs(s - 0.25) < 0.1: return "bilinear"
    return "unknown"

def permeability_from_radial_slope(q, bo, mu, h, slope):
    """Eq. 15.17."""
    return -q*bo*mu/(4*math.pi*h*slope)

def permeability_from_linear_slope(q, bo, mu, h, xf, phi, ct, slope):
    return (q*bo*mu/(slope*h*xf))**2/(math.pi*phi*ct)

def skin_decomposition_full(SD=0.0, S_Cu=0.0, S_P=0.0,
                              S_PS=0.0, S_nd=0.0, S_mp=0.0):
    tot = SD + S_Cu + S_P + S_PS + S_nd + S_mp
    return {"damage": SD, "completion_deviation": S_Cu,
            "perforation": S_P, "pseudo_skin": S_PS,
            "non_darcy": S_nd, "multiphase": S_mp, "total": tot}

def turner_slip_velocity(sigma, rl, rg, Cd=0.44):
    return 1.3*(sigma**0.25)*((rl - rg)**0.25)/((Cd**0.25)*rg**0.5)

def turner_min_gas_rate(v_sl, A_ft2, p, tR, z):
    return 3.06*p*v_sl*A_ft2/(tR*z)

def guo_four_phase_bhp(phf, t_head_F, t_bh_F, d_in, L_ft,
                        theta_deg, q_g, q_o, q_w, q_s,
                        gamma_g, gamma_o, gamma_w, gamma_s,
                        rel_rough=6e-4):
    from .ch04_tpr import guo_ghalambor_bhp_robust
    return guo_ghalambor_bhp_robust(phf, t_head_F, t_bh_F, d_in,
        L_ft, theta_deg, q_g, q_o, q_w, q_s, gamma_g, gamma_o,
        gamma_w, gamma_s, rel_rough)

def guo_min_rate_solved(phf, t_head_F, t_bh_F, d_in, L_ft,
                         theta_deg, q_o, q_w, q_s, gamma_g,
                         gamma_o, gamma_w, gamma_s,
                         sigma=60.0, rho_L=65.0, rel_rough=6e-4,
                         tol=1e-3):
    from scipy.optimize import brentq
    A = math.pi*(d_in/2/12)**2
    Ekm = 0.0576*math.sqrt(sigma*rho_L)
    def res(qg):
        pb = guo_four_phase_bhp(phf, t_head_F, t_bh_F, d_in, L_ft,
                                 theta_deg, qg, q_o, q_w, q_s,
                                 gamma_g, gamma_o, gamma_w, gamma_s,
                                 rel_rough)
        tR = t_bh_F + 460.0
        Ek = 9.3e-5*gamma_g*tR*qg*qg/(A*A*pb)
        return Ek - Ekm
    qs = np.logspace(1, 7, 60)
    fs = np.array([res(q) for q in qs])
    ch = np.where(np.sign(fs[:-1])*np.sign(fs[1:]) < 0)[0]
    if len(ch) == 0: raise ValueError("Cannot bracket")
    i = ch[0]
    return brentq(res, qs[i], qs[i+1], xtol=tol, maxiter=200)
