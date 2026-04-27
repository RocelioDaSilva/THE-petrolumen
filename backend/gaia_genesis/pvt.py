import numpy as np
from typing import Tuple, Optional

def pseudocritical_props(gamma_g: float) -> Tuple[float, float]:
    """
    Sutton (1985) correlation for pseudocritical properties.

    Args:
        gamma_g (float): Gas specific gravity (air = 1.0)

    Returns:
        tuple: (Tpc, Ppc) in Rankine and psia.
    """
    Tpc = 169.2 + 349.5 * gamma_g - 74.0 * gamma_g**2
    Ppc = 756.8 - 131.0 * gamma_g - 3.6 * gamma_g**2
    return Tpc, Ppc

def zfactor_dak(Tpr: float, Ppr: float, tol: float = 1e-6, max_iter: int = 100) -> float:
    """
    Dranchuk-Abou-Kassem (1975) correlation for Z-factor.

    Args:
        Tpr (float): Pseudo-reduced temperature.
        Ppr (float): Pseudo-reduced pressure.

    Returns:
        float: Gas compressibility factor Z.
    """
    A1, A2, A3, A4, A5 = 0.3265, -1.0700, -0.5339, 0.01569, -0.05165
    A6, A7, A8, A9, A10, A11 = 0.5475, -0.7361, 0.1844, 0.1056, 0.6134, 0.7210

    rho_r = 0.27 * Ppr / Tpr # initial guess

    for _ in range(max_iter):
        term1 = (A1 + A2/Tpr + A3/Tpr**3 + A4/Tpr**4 + A5/Tpr**5)*rho_r
        term2 = (A6 + A7/Tpr + A8/Tpr**2)*rho_r**2
        term3 = A9*(A7/Tpr + A8/Tpr**2)*rho_r**5
        term4 = (A10/Tpr**3)*rho_r**2*(1+A11*rho_r**2)*np.exp(-A11*rho_r**2)

        Z = 1 + term1 + term2 + term3 + term4
        f = Z - 0.27 * Ppr / (rho_r * Tpr)

        # Derivative df/drho_r
        dZ_drho = (A1 + A2/Tpr + A3/Tpr**3 + A4/Tpr**4 + A5/Tpr**5) + \
                 2*(A6 + A7/Tpr + A8/Tpr**2)*rho_r + \
                 5*A9*(A7/Tpr + A8/Tpr**2)*rho_r**4 + \
                 (2*A10*rho_r/Tpr**3)*(1 + A11*rho_r**2 - (A11*rho_r**2)**2)*np.exp(-A11*rho_r**2)

        df = dZ_drho + 0.27 * Ppr / (rho_r**2 * Tpr)

        rho_r_new = rho_r - f/df
        if abs(rho_r_new - rho_r) < tol:
            return 0.27 * Ppr / (rho_r_new * Tpr)
        rho_r = rho_r_new

    return 1.0 # fallback

def calculate_zfactor(P: float, T_f: float, gamma_g: float) -> float:
    T_r = T_f + 459.67
    Tpc, Ppc = pseudocritical_props(gamma_g)
    Tpr = T_r / Tpc
    Ppr = P / Ppc
    return zfactor_dak(Tpr, Ppr)

def gas_viscosity_lee(P: float, T_f: float, gamma_g: float, z: float) -> float:
    """
    Lee, Gonzalez, and Eakin (1966) correlation for gas viscosity.
    """
    T_r = T_f + 459.67
    MW = 28.96 * gamma_g
    rho_g = (P * MW) / (z * 10.732 * T_r) / 62.4 # lb/ft3 to g/cm3

    X = 3.5 + 986 / T_r + 0.01 * MW
    Y = 2.4 - 0.2 * X
    K = (9.4 + 0.02 * MW) * T_r**1.5 / (209 + 19 * MW + T_r)

    mu_g = K * 1e-4 * np.exp(X * rho_g**Y)
    return mu_g

def oil_bubble_point_standing(Rs: float, gamma_g: float, api: float, T_f: float) -> float:
    """
    Standing (1947) correlation for bubble point pressure.
    """
    a = 0.00091 * T_f - 0.0125 * api
    Pb = 18.2 * ((Rs / gamma_g)**0.83 * 10**a - 1.4)
    return Pb

def oil_fvf_standing(Rs: float, gamma_g: float, gamma_o: float, T_f: float) -> float:
    """
    Standing (1947) correlation for oil formation volume factor.
    """
    F = Rs * (gamma_g / gamma_o)**0.5 + 1.25 * T_f
    Bo = 0.9759 + 0.00012 * F**1.2
    return Bo

def water_fvf_mccain(P: float, T_f: float) -> float:
    """
    McCain (1991) correlation for water formation volume factor.
    """
    dV_wt = -1.0001e-2 + 1.33391e-4 * T_f + 5.50654e-7 * T_f**2
    dV_wp = -1.95301e-9 * P * T_f - 1.72834e-13 * P**2 * T_f - 3.58922e-7 * P - 2.25341e-10 * P**2
    Bw = (1 + dV_wt) * (1 + dV_wp)
    return Bw

def calculate_gas_compressibility(pressure: float, temperature: float, gamma_g: float) -> float:
    """
    Calculates isothermal gas compressibility (cg).
    """
    dp = 1.0
    z1 = calculate_zfactor(pressure, temperature, gamma_g)
    z2 = calculate_zfactor(pressure + dp, temperature, gamma_g)
    dz_dp = (z2 - z1) / dp
    cg = (1.0 / pressure) - (1.0 / z1) * dz_dp
    return cg
