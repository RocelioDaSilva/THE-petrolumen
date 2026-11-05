"""Chapter 2 -- Properties of Oil and Natural Gas."""
import math
import numpy as np
from scipy.optimize import newton

MW_AIR = 28.97

def rs_standing(p, t_F, api, gamma_g) -> float:
    """Eq. 2.2. [scf/stb]"""
    return gamma_g * ((p/18) * (10**(0.0125*api))
                       / (10**(0.00091*t_F)))**1.2048

def rho_o(p, t_F, api, rs, gamma_g) -> float:
    """Eq. 2.5. [lbm/ft3]"""
    go = 141.5/(api+131.5)
    num = 62.4*go + 0.0136*rs*gamma_g
    den = 0.972 + 0.000147*(rs*math.sqrt(gamma_g/go) + 1.25*t_F)**1.175
    return num/den

def bo_standing(t_F, api, rs, gamma_g) -> float:
    """Eq. 2.7. [rb/stb]"""
    go = 141.5/(api+131.5)
    return 0.9759 + 0.00012*(rs*math.sqrt(gamma_g/go) + 1.25*t_F)**1.2

def mu_dead_oil(api, t_F) -> float:
    """Eqs. 2.8-2.9. [cp]"""
    A = 10**(0.43 + 8.33/api)
    return (0.32 + 1.8e7/api**4.53)*(360.0/(t_F+200.0))**A

def mu_sat_oil(rs, mu_od) -> float:
    """Eqs. 2.10-2.15. [cp]"""
    a = rs*(2.2e-7*rs - 7.4e-4)
    c = 8.62e-5*rs; d = 1.10e-3*rs; e = 3.74e-3*rs
    b = 0.68/(10**c) + 0.25/(10**d) + 0.062/(10**e)
    return 10**a * mu_od**b

def mu_unsat_oil(p, pb, mu_od, mu_ob) -> float:
    """Eq. 2.16. [cp]"""
    return mu_ob + 0.001*(p-pb)*(0.024*mu_od**1.6 + 0.38*mu_ob**0.56)

def oil_compressibility(p, rs, t_F, api, gamma_g) -> float:
    """Eq. 2.17. [1/psi]"""
    c = (-1433 + 5*rs + 17.2*t_F - 1180*gamma_g + 12.61*api) / (1e6*p)
    return max(c, 1e-7)

def z_brill_beggs(p_pr, t_pr) -> float:
    """Eqs. 2.45-2.51."""
    A = 1.39*(t_pr-0.92)**0.5 - 0.36*t_pr - 0.10
    E = 9.0*(t_pr-1.0)
    B = (0.62-0.23*t_pr)*p_pr + (0.066/(t_pr-0.86) - 0.037)*p_pr**2 \
        + 0.32*p_pr**6/10**E
    C = 0.132 - 0.32*math.log10(t_pr)
    F = 0.3106 - 0.49*t_pr + 0.1824*t_pr**2
    D = 10**F
    return A + (1-A)/math.exp(B) + C*p_pr**D

def z_hall_yarborough(p_pr, t_pr) -> float:
    """Eqs. 2.52-2.59."""
    tr = 1.0/t_pr
    A = 0.06125*tr*math.exp(-1.2*(1-tr)**2)
    B = tr*(14.76 - 9.76*tr + 4.58*tr**2)
    C = tr*(90.7 - 242.2*tr + 42.4*tr**2)
    D = 2.18 + 2.82*tr
    def f(Y):
        return (Y + Y**2 + Y**3 - Y**4)/(1-Y)**3 \
               - A*p_pr - B*Y**2 + C*Y**D
    def df(Y):
        return (1+4*Y+4*Y**2-4*Y**3+Y**4)/(1-Y)**4 - 2*B*Y \
               + C*D*Y**(D-1)
    Y = newton(f, x0=0.1, fprime=df, tol=1e-12, maxiter=200)
    return A*p_pr/Y

def pseudo_critical_from_sg(gamma_g):
    """Eqs. 2.22-2.23."""
    return 709.604 - 58.718*gamma_g, 170.491 + 307.344*gamma_g

def pseudo_critical_from_composition(y, p_c, t_c):
    """Eqs. 2.20-2.21."""
    return float(np.sum(y*p_c)), float(np.sum(y*t_c))

def wichert_aziz_correction(y_H2S, y_CO2, p_pc, t_pc):
    """Eqs. 2.24-2.28."""
    A = y_H2S + y_CO2; B = y_H2S
    e3 = 120*(A**0.9 - A**1.6) + 15*(B**0.5 - B**4.0)
    t_new = t_pc - e3
    p_new = p_pc*t_new/(t_pc + B*(1-B)*e3)
    return p_new, t_new

_DEMPSEY = (
    -2.46211820, 2.97054714, -0.28626405, 0.00805420,
     2.80860949, -3.49803305, 0.36037302, -0.01044324,
    -0.79338568, 1.39643306, -0.14914493, 0.00441016,
     0.08393872, -0.18640885, 0.02033679, -0.00060958,
)

def mu_gas_low_pressure(gamma_g, t_R, y_N2=0.0, y_CO2=0.0, y_H2S=0.0):
    """Eqs. 2.36-2.39. [cp]"""
    lg = math.log10(gamma_g)
    mhc = (8.188e-3 - 6.15e-3*lg) + (1.709e-5 - 2.062e-6*gamma_g)*t_R
    return (mhc + (9.59e-3 + 8.48e-3*lg)*y_N2
            + (6.24e-3 + 9.08e-3*lg)*y_CO2
            + (3.73e-3 + 8.49e-3*lg)*y_H2S)

def mu_gas_corr(p_pr, t_pr, mu1):
    """Eqs. 2.40-2.41. [cp]"""
    a = _DEMPSEY
    ln_mr = (a[0]+a[1]*p_pr+a[2]*p_pr**2+a[3]*p_pr**3
             + t_pr*(a[4]+a[5]*p_pr+a[6]*p_pr**2+a[7]*p_pr**3)
             + t_pr**2*(a[8]+a[9]*p_pr+a[10]*p_pr**2+a[11]*p_pr**3)
             + t_pr**3*(a[12]+a[13]*p_pr+a[14]*p_pr**2+a[15]*p_pr**3))
    return (mu1/math.exp(ln_mr))*math.exp(math.exp(ln_mr))

def rho_gas(p, t_R, gamma_g, z):
    """Eq. 2.61. [lbm/ft3]"""
    return 2.7*gamma_g*p/(z*t_R)

def bg(p, t_R, z):
    """Eq. 2.62. [ft3/scf]"""
    return 0.0283*z*t_R/p

def eg(p, t_R, z):
    """Eq. 2.64. [scf/ft3]"""
    return 35.3*p/(z*t_R)

def gas_compressibility(p, z, dz_dp):
    """Eq. 2.68."""
    return 1.0/p - (1.0/z)*dz_dp
