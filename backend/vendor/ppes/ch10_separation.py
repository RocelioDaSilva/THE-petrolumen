"""Chapter 10 -- Separation Systems."""
import math

_SEP_K = {"vertical": (0.06, 0.35), "horizontal": (0.40, 0.50),
          "wire_mesh": (0.35, 0.35), "bubble_cap": (0.16, 0.16)}

def sousa_brown_velocity(K, rho_l, rho_g):
    """Eq. 10.1."""
    return K*math.sqrt((rho_l - rho_g)/rho_g)

def gas_capacity(D_ft, K, p, T_F, z, gamma_g, rho_l):
    """Eq. 10.3."""
    rho_g = 2.7*gamma_g*p/(z*(T_F + 460.0))
    return (2.4*D_ft**2*K*p/(z*(T_F + 460.0))
            *math.sqrt((rho_l - rho_g)/rho_g))

def liquid_capacity(VL, t_min):
    """Eq. 10.4."""
    return 1440.0*VL/t_min

def stage_separation_pressures(p1, p_stock, n_stages):
    """Eqs. 10.5-10.6."""
    if n_stages < 2: return [p1]
    n = n_stages - 1
    Rp = (p1/p_stock)**(1.0/n)
    pr = [p1]
    for i in range(1, n_stages): pr.append(pr[-1]/Rp)
    pr[-1] = p_stock
    return pr

def water_content_lbm_per_mmscf(p_psia, t_F):
    """Approximate Fig. 10.6."""
    A = 3.03*math.exp(0.0256*t_F)
    B = 1.0/(1.0 + 1.5e-4*p_psia)
    return A*B

def glycol_circulation(GWR, Cw_in, q_mmscfd):
    """Eq. 10.8."""
    return GWR*Cw_in*q_mmscfd/24.0

def reboiler_heat(q_G_gph):
    """Eq. 10.9."""
    return 2000.0*q_G_gph

def firebox_area(Ht):
    """Eq. 10.10."""
    return Ht/7000.0

def glycol_flash_separator_sizing(q_G_gph, t_min=5.0):
    """Eq. 10.11."""
    Vs = q_G_gph*t_min/60.0
    D = 12 if Vs < 20 else 18 if Vs < 40 else 24
    return {"settling_volume_gal": Vs, "suggested_diameter_in": D}

def select_contactor(q_std, contactor_type="trayed", Ct=1.0, Cg=1.0):
    """Approximate Fig. 10.10/10.11."""
    qc = q_std/(Ct*Cg)
    table = {12: 8.5, 15: 14, 18: 20, 20: 25, 24: 36, 30: 55,
             36: 80, 42: 105, 48: 140, 54: 175, 60: 215,
             66: 260, 72: 310}
    for d in sorted(table):
        if table[d] >= qc:
            return {"diameter_in": d, "capacity_mmscfd": table[d],
                    "q_corrected": qc}
    raise ValueError(f"q={qc:.1f} exceeds all contactors")

def trays_or_packing(delta_td, GWR):
    """Approximate Fig. 10.12."""
    n = 3 if delta_td <= 55 else 4 if delta_td <= 75 else 5 if delta_td <= 95 else 6
    return {"trays": n, "packing_ft": max(6.0, n*2.5), "GWR": GWR}
