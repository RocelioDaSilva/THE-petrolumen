"""Chapter 10 â€” Separation Systems (pp. 10/117 â€“ 10/132)."""
from __future__ import annotations
import math


_SEP_K = {
    "vertical":   (0.06, 0.35),
    "horizontal": (0.40, 0.50),
    "wire_mesh":  (0.35, 0.35),
    "bubble_cap": (0.16, 0.16),
}


def sousa_brown_velocity(K, rho_l, rho_g) -> float:
    """Eq. 10.1 (p. 10/121). [ft/s]"""
    return K * math.sqrt((rho_l - rho_g) / rho_g)


def gas_capacity(D_ft, K, p, T_F, z, gamma_g, rho_l) -> float:
    """Separator gas capacity â€” Eq. 10.3 (p. 10/121). [MMscfd]"""
    rho_g = 2.7 * gamma_g * p / (z * (T_F + 460.0))
    return (2.4*D_ft**2 * K * p / (z * (T_F + 460.0))) * \
        math.sqrt((rho_l - rho_g) / rho_g)


def liquid_capacity(VL_bbl, retention_min) -> float:
    """Eq. 10.4 (p. 10/122). [bbl/day]"""
    return 1440.0 * VL_bbl / retention_min


def stage_separation_pressures(p1, p_stock, n_stages) -> list[float]:
    """Equal pressure ratio â€” Eqs. 10.5â€“10.6 (p. 10/122)."""
    if n_stages < 2:
        return [p1]
    n = n_stages - 1
    Rp = (p1 / p_stock)**(1.0/n)
    pressures = [p1]
    for _ in range(1, n_stages):
        pressures.append(pressures[-1] / Rp)
    pressures[-1] = p_stock
    return pressures


def glycol_circulation(GWR, Cw_in, q_mmscfd) -> float:
    """Eq. 10.8 (p. 10/130). [gal/hr]"""
    return GWR * Cw_in * q_mmscfd / 24.0


def reboiler_heat(q_G_gph) -> float:
    """Eq. 10.9 (p. 10/130). [Btu/hr]"""
    return 2000.0 * q_G_gph


def firebox_area(Ht_btu_hr) -> float:
    """Eq. 10.10 (p. 10/131). [ft2]"""
    return Ht_btu_hr / 7000.0