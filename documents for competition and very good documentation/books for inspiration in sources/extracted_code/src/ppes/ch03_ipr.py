"""Chapter 3 -- Reservoir Deliverability / IPR."""
import math
import numpy as np

def j_star_pseudosteady(k, h, bo, mu, A, ca, rw, skin) -> float:
    """Eq. 3.17."""
    return k*h/(141.2*bo*mu*(0.5*math.log(4*A/(1.78*ca*rw**2)) + skin))

def vogel_rate(qmax, pwf, pbar) -> float:
    """Eq. 3.19."""
    r = pwf/pbar
    return qmax*(1 - 0.2*r - 0.8*r*r)

def vogel_pwf(q, qmax, pbar) -> float:
    """Eq. 3.20."""
    return 0.125*pbar*(math.sqrt(max(81-80*q/qmax, 0.0)) - 1)

def qmax_from_j(j_star, pbar) -> float:
    """Eq. 3.21."""
    return j_star*pbar/1.8

def fetkovich_rate(qmax, pwf, pbar, n) -> float:
    """Eq. 3.22."""
    return qmax*(1 - (pwf/pbar)**2)**n

def generalized_vogel(j_star, pbar, pb, pwf) -> float:
    """Eq. 3.28."""
    if pwf >= pb: return j_star*(pbar - pwf)
    qb = j_star*(pbar - pb); qv = j_star*pb/1.8
    r = pwf/pb
    return qb + qv*(1 - 0.2*r - 0.8*r*r)

def transient_ipr_oil(p_i, k, h, bo, mu, phi, ct, rw, skin,
                       t_hours, q) -> float:
    """Eq. 3.1."""
    lt = (math.log10(t_hours) + math.log10(k/(phi*mu*ct*rw**2))
          - 3.23 + 0.87*skin)
    return p_i - 162.6*q*bo*mu*lt/(k*h)

def transient_rate_from_pwf(p_i, k, h, bo, mu, phi, ct, rw, skin,
                             t_hours, pwf) -> float:
    lt = (math.log10(t_hours) + math.log10(k/(phi*mu*ct*rw**2))
          - 3.23 + 0.87*skin)
    return k*h*(p_i - pwf)/(162.6*bo*mu*lt)

def transient_ipr_gas(k, h, t_R, phi, mu, ct, rw, skin,
                       t_hours, q_mscf, m_pi, m_pwf) -> float:
    """Eq. 3.3 -- residual."""
    lt = (math.log10(t_hours) + math.log10(k/(phi*mu*ct*rw**2))
          - 3.23 + 0.87*skin)
    return q_mscf*1e3*1638*t_R*lt - k*h*(m_pi - m_pwf)

def joski_horizontal_ipr(kH, kV, h, bo, mu, L_ft, reH_ft, rw_ft,
                          pe, pwf, skin=0.0) -> float:
    """Eq. 3.11."""
    Iani = math.sqrt(kH/kV)
    a = (L_ft/2.0)*math.sqrt(0.5 + math.sqrt(
        0.25 + (reH_ft/(L_ft/2.0))**4))
    L2 = L_ft/2.0
    l1 = math.log((a + math.sqrt(a*a - L2*L2))/L2)
    l2 = (Iani*h/L_ft)*math.log(Iani*h/(rw_ft*(Iani*h + 1.0)))
    return kH*h*(pe - pwf)/(141.2*bo*mu*(l1 + l2 + skin))

def composite_ipr_single_phase(layer_data) -> float:
    """Eq. 3.40."""
    return sum(L["J_star"]*L["p_bar"] for L in layer_data)

def composite_ipr_two_phase(layer_data) -> float:
    """Eq. 3.43."""
    return sum(L["J_star"]*L["p_bar"]/1.8 for L in layer_data)

def composite_ipr_two_phase_rate(layer_data, pwf) -> float:
    """Eq. 3.42."""
    tot = 0.0
    for L in layer_data:
        j, p, pb = L["J_star"], L["p_bar"], L["p_b"]
        if pwf >= pb:
            tot += j*(p - pwf)
        else:
            qb = j*(p - pb); qv = j*pb/1.8; r = pwf/pb
            tot += qb + qv*(1 - 0.2*r - 0.8*r*r)
    return tot

def composite_pwf_two_phase(layer_data, q_total, p_lo=0.0, p_hi=None):
    from scipy.optimize import brentq
    if p_hi is None:
        p_hi = max(L["p_bar"] for L in layer_data)*0.999
    def res(p):
        return composite_ipr_two_phase_rate(layer_data, p) - q_total
    return brentq(res, p_lo, p_hi, xtol=1e-6)

def layer_ji_from_test(qi, pi, pwfi, pb=None) -> float:
    if pb is None or pwfi >= pb:
        return qi/(pi - pwfi)
    return qi/((pi - pb) + (pb/1.8)*(
        1 - 0.2*(pwfi/pb) - 0.8*(pwfi/pb)**2))

def future_j_vogel(j_present, kro_f, mu_f, bo_f, kro_p, mu_p, bo_p):
    return j_present*(kro_f/(bo_f*mu_f))/(kro_p/(bo_p*mu_p))

def future_rate_vogel(j_future, p_future, pwf):
    r = pwf/p_future
    return (j_future*p_future/1.8)*(1 - 0.2*r - 0.8*r**2)

def future_j_fetkovich(j_initial, p_future, p_initial):
    return j_initial*p_future/p_initial
