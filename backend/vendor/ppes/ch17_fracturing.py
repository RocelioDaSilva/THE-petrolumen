"""Chapter 17 -- Hydraulic Fracturing."""
import math

def overburden(rho, H): return rho*H/144.0

def breakdown_pressure(sv, alpha, pp, nu, stect, T0):
    """Eq. 17.5."""
    shmin = (nu/(1 - nu))*(sv - alpha*pp) + alpha*pp
    return 3*shmin - (shmin + stect) + T0 - pp

def kgd_width(q, mu, nu, xf, G, hf):
    """Eq. 17.8."""
    return 0.29*((q*mu*(1 - nu)*xf*xf)/(G*hf))**0.25*(math.pi/4)

def pkn_width(q, mu, nu, xf, G, gamma=0.75):
    """Eq. 17.9."""
    return 0.3*((q*mu*(1 - nu)*xf)/G)**0.25*(math.pi/(4*gamma))

def radial_width(q, mu, nu, R, E):
    """Eq. 17.7."""
    return 0.85*((mu*q*(1 - nu)*R/E))**0.25

def fracture_conductivity(kf, w, k, xf):
    """Eq. 17.10."""
    return kf*w/(k*xf)

def fold_of_increase(re, rw, Sf):
    """Eq. 17.12."""
    return math.log(re/rw)/(math.log(re/rw) + Sf)

def sf_high_conductivity(xf, rw):
    """Eq. 17.13."""
    return -0.7 - math.log(xf/rw)

def treatment_surface_pressure(pbd, rho, D, q, mu, d):
    """Eqs. 17.18-17.19."""
    dph = 0.433*rho*D
    dpf = 518*(rho**0.79)*(q**1.79)*(mu**0.207)*D/(1000*d**4.79)
    return pbd - dph + dpf

def kgd_proppant_schedule(t_min, cf, t_pad, t_inj, eta):
    """Eq. 17.29."""
    eps = (1 - eta)/(1 + eta)
    out = []
    for t in t_min:
        if t <= t_pad: out.append(0.0)
        else:
            f = (t - t_pad)/(t_inj - t_pad)
            out.append(cf*f**eps)
    return out

def kgd_proppant_weight(cf, Vinj, Vpad, eta):
    """Eqs. 17.34-17.35."""
    eps = (1 - eta)/(1 + eta)
    return cf/(1 + eps)*(Vinj - Vpad)

def propped_width(Mp, xf, hf, phi_p=0.4, rho_p=165.0):
    """Eqs. 17.32-17.33."""
    Cp = Mp/(2*xf*hf)
    return Cp/((1 - phi_p)*rho_p)

def hydraulic_hp(q, psi):
    return q*psi/40.8
