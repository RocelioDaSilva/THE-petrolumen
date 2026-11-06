"""Chapter 11 -- Transportation Systems."""
import math

def triplex_hp_input(p, d, l, N, em=0.85):
    """Eq. 11.11."""
    return p*d*d*l*N/(168067*em)

def triplex_rate(d, l, N, ev=0.95):
    """Eq. 11.8. [bbl/day]"""
    return 0.35*ev*l*N*d*d

def duplex_hp_input(p, d1, d2, l, N, em=0.85):
    """Eq. 11.22."""
    return p*(2*d1*d1 - d2*d2)*l*N/(252101*em)

def recip_hp_per_mmscfd(p1, p2, t1_R, gamma_g, z1, k=1.25):
    """Eq. 11.26."""
    return ((k/(k-1))*(3.027*14.7/520.0)*t1_R
            *((p2/p1)**(z1*(k-1)/k) - 1.0))

def ep_rollins(q1):
    """Eq. 11.68."""
    return 0.61 + 0.03*math.log10(q1)

def gas_hp_centrifugal(q1, p1, z1, z2, r, Rp, Ep):
    """Eq. 11.74."""
    return (q1*p1/(229.0*Ep))*((z1+z2)/(2*z1))*((r**Rp - 1)/Rp)

def oil_pipeline_dp(p1, gamma_o, L_mi, Q_bpd, d_in, fM, sin_theta=0.0):
    """Eq. 11.93."""
    return (0.433*gamma_o*L_mi*5280*sin_theta
            + 1.15e-5*fM*gamma_o*Q_bpd**2*L_mi*5280/d_in**5)

def weymouth_horizontal(q_scfd, p1, p2, d_in, L_ft, gamma_g, T_R,
                        Tb_R=520, pb=14.7):
    """Eq. 11.101."""
    return ((18.062*Tb_R/pb)
            *math.sqrt((p1**2 - p2**2)*d_in**(16.0/3.0)
                        /(gamma_g*T_R*L_ft)))

def panhandle_a(q_scfd, p1, p2, d_in, L_ft, gamma_g, T_R,
                Tb_R=520, pb=14.7):
    E = 0.92
    return (435.87*(Tb_R/pb)**1.07881*E
            *((p1**2 - p2**2)*d_in**4.7353
              /(gamma_g**0.4609*T_R*L_ft))**0.5394)

def panhandle_b(q_scfd, p1, p2, d_in, L_ft, gamma_g, T_R,
                Tb_R=520, pb=14.7):
    E = 0.92
    return (737.0*(Tb_R/pb)**1.02*E
            *((p1**2 - p2**2)*d_in**4.96
              /(gamma_g**0.961*T_R*L_ft))**0.510)

def wall_thickness_internal(pd, D, sigma_y, eta=0.72,
                             Ew=1.0, Ft=1.0, t_a=0.0625):
    """Eq. 11.116."""
    return pd*D/(2*Ew*eta*sigma_y*Ft) + t_a

def pipeline_insulation_temperature(T_en, T_amb, v, rho, cp,
                                      D, k, s, L):
    R = D/2; A = math.pi*R*R
    m = rho*A*v
    if m <= 0: return T_en
    alpha = 2*math.pi*R*k/(s*m*cp)
    Ten_C = (T_en - 32)*5/9
    Tamb_C = (T_amb - 32)*5/9
    Tex_C = Tamb_C + (Ten_C - Tamb_C)*math.exp(-alpha*L)
    return Tex_C*9/5 + 32

def pipeline_heat_loss_W(T_en, T_amb, v, rho, cp, D, k, s, L):
    Tex = pipeline_insulation_temperature(T_en, T_amb, v, rho, cp,
                                            D, k, s, L)
    R = D/2; A = math.pi*R*R
    return rho*A*v*cp*(T_en - Tex)*5/9
