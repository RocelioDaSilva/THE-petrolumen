"""Chapter 9 -- Well Tubing."""
import math

def collapse_biaxial(p_c, sa, ym):
    """Eq. 9.19."""
    r = sa/ym
    return p_c*(math.sqrt(1 - 0.75*r*r) - 0.5*r)

def landing_tension(ae, delta_L, L, E=30e6):
    """Eq. 9.22."""
    return ae*E*delta_L/L

def bending_stress(E, Do, Rc):
    """Eq. 9.20."""
    return E*Do/(2*Rc)

def piston_effect(pi_c, po_c, A_p, A_i, A_o, L, E, A_s):
    """Eqs. 9.24-9.28."""
    dF = pi_c*(A_p - A_i) - po_c*(A_p - A_o)
    return dF, L*dF/(A_s*E)

def ballooning_effect(dpi, dpo, A_i, A_o, L):
    """Eq. 9.30."""
    R2 = A_o/A_i
    return (2*L/1e8)*((dpi - R2*dpo)/(R2 - 1))

def buckling_effect(F_bk, r, I, E, W):
    """Eq. 9.31."""
    if F_bk <= 0: return 0.0
    return (r*r*F_bk*F_bk)/(8*E*I*W)

def total_tubing_movement(dL_T, dL_P, dL_B, dL_BK):
    return dL_T + dL_P + dL_B + dL_BK

def force_on_restraining_packer(A_s, E, L, dL):
    return A_s*E*dL/L
