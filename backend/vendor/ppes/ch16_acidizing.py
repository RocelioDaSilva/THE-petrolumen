"""Chapter 16 -- Matrix Acidizing."""
import math

def gravimetric_power(Ca, nm, MWm, na, MWa):
    """Eq. 16.1."""
    return Ca*nm*MWm/(na*MWa)

def volumetric_power(beta, rho_a, rho_m):
    """Eq. 16.2."""
    return beta*rho_a/rho_m

def preflush_volume(r_a, r_w, phi, C_m, beta, rho_a, rho_m):
    """Eqs. 16.3-16.5."""
    Vm = math.pi*(r_a**2 - r_w**2)*(1 - phi)*C_m
    Vp = math.pi*(r_a**2 - r_w**2)*phi
    X = volumetric_power(beta, rho_a, rho_m)
    return Vm/X + Vp + Vm

def max_injection_rate(k, h, pbd, p, dpsf, mu_a, re, rw, S):
    """Eq. 16.6."""
    return 4.917e-6*k*h*(pbd - p - dpsf)/(
        mu_a*math.log(0.472*re/rw) + S)

def surface_injection_pressure(pwf, rho, D, q, mu, d):
    """Eqs. 16.7-16.8."""
    dph = 0.433*rho*D
    dpf = 518*(rho**0.79)*(q**1.79)*(mu**0.207)*D/(1000*d**4.79)
    return pwf - dph + dpf

def daccord_volume(phi, D, qh, rwh, beta, N_Ac, df=1.6):
    """Eq. 16.9."""
    b = 1.5e-5
    return (math.pi*phi*D**(2/3)*qh**(1/3)*rwh**df
            /(b*beta*N_Ac))

def acid_capillary_number(phi, beta, ga, gm):
    """Eq. 16.10."""
    return phi*beta*ga/((1 - phi)*gm)

def volumetric_wormhole_volume(phi, rwh, rw, PV_bt):
    """Eq. 16.11."""
    return math.pi*phi*(rwh**2 - rw**2)*PV_bt
