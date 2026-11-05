"""Chapter 13 -- Gas Lift."""
import math

def injection_glr(glr_opt, glr_form): return glr_opt - glr_form
def required_gas_rate(glr_inj, q_o): return glr_inj*q_o
def pcv_from_ptv(ptv, dp=100.0): return ptv + dp
def surface_injection_approx(pcv, Dv):
    return pcv/(1 + Dv/40000.0)
def critical_ratio_gas(k=1.28):
    return (2.0/(k+1.0))**(1.0/(k-1.0))

def valve_opening_pressure(pd, St, R, pt):
    """Eq. 13.42."""
    return (1/(1-R))*pd + St - (R/(1-R))*pt

def valve_closing_pressure(pd, St, R):
    """Eq. 13.43."""
    return pd + St*(1-R)

def valve_depth_first(pk_s, dp_km, phf, Gs):
    """Eq. 13.49."""
    return (pk_s - dp_km - phf)/(Gs - (pk_s - dp_km)/40000.0)

def valve_depth_i(pc_s, dp_cm, phf_d, Gs, Gfd, Dp):
    """Eq. 13.55."""
    return ((pc_s - dp_cm - phf_d + (Gs - Gfd)*Dp)
            /(Gs - (pc_s - dp_cm)/40000.0))

def weymouth_distribution_pressure(p_up, q_mmscfd, gg, T_R,
                                     L_mi, D_in, Tb=520, pb=14.7):
    """Eq. 13.18."""
    q = q_mmscfd*1e6; L = L_mi*5280
    c = (q*pb/(0.433*Tb))
    dp2 = (c*c)*(gg*T_R*L)/(D_in**(16/3))
    return math.sqrt(p_up**2 + dp2)

def size_orifice_port(q_mscfd, p_up, p_dn, gg, t_R, k=1.28, cd=0.6):
    """Eq. 13.56."""
    from scipy.optimize import brentq
    from .ch05_choke import q_subsonic_gas, q_sonic_gas, critical_ratio
    rc = critical_ratio(k); ratio = p_dn/p_up
    def res(A):
        if ratio < rc:
            return q_sonic_gas(cd, A, p_up, t_R, gg, k) - q_mscfd
        return q_subsonic_gas(cd, A, p_up, p_dn, t_R, gg, k) - q_mscfd
    return brentq(res, 1e-4, 10.0, xtol=1e-6)

def port_diameter_from_area(A):
    return 1.1284*math.sqrt(A)

def intermittent_gas_lift(D_ft, ps_o, d_tbg, d_csg, gamma_o,
                           BHP, PI, ptf, t_avg_F, cycle_min,
                           q_desired, gg, fallback=0.40):
    Gs = gamma_o*0.433
    SFL = D_ft - (BHP - ptf)/Gs
    dds = (BHP - ptf)/Gs
    WFL = SFL + dds
    cyc = int(24*60/cycle_min)
    slug = q_desired/cyc if cyc > 0 else 0.0
    starting = slug/(1 - fallback)
    A = math.pi*(d_tbg/2)**2
    cap = A/(144*5.615)
    length = starting/cap if cap > 0 else 0.0
    D_op = WFL + length/2.0
    pt_valve = ptf + length*Gs
    p_cm = pt_valve + max(pt_valve*0.5, 200.0)
    return {"cycles_per_day": cyc, "slug_bbl": slug,
            "starting_slug": starting, "D_op_ft": D_op,
            "casing_min_psig": p_cm, "WFL_ft": WFL}
