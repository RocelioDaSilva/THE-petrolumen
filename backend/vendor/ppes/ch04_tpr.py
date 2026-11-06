"""Chapter 4 -- Wellbore Performance / TPR."""
import math
import numpy as np

def friction_chen(re, rel_rough) -> float:
    """Eq. 4.5."""
    t1 = rel_rough/3.7065
    t2 = (5.0452/re)*math.log10(
        rel_rough**1.1098/2.8257 + (7.149/re)**0.8981)
    return 1.0/(-4*math.log10(t1 - t2))**2

def bhp_average_tz(phf, q_sc, gamma_g, d_i, L, theta_deg,
                    t_avg_R, z_avg, fM) -> float:
    """Eq. 4.54."""
    s = 0.0375*gamma_g*L*math.cos(math.radians(theta_deg))/(z_avg*t_avg_R)
    es = math.exp(s)
    return math.sqrt(es*phf**2 +
        (6.67e-4*(es - 1)*fM*q_sc**2*z_avg**2*t_avg_R**2)
        /(d_i**5*math.cos(math.radians(theta_deg))))

def cullender_smith_bhp(phf, t_head_F, t_bh_F, d_in, L_ft, q_msc,
                          gamma_g, rel_rough=6e-4, theta_deg=0.0):
    """Eqs. 4.59-4.68."""
    from scipy.optimize import brentq
    fM = (1.0/(1.74 - 2.0*math.log10(2.0*rel_rough/d_in)))**2
    def I(p, t_F):
        tR = t_F + 460.0
        return ((p/tR)/(0.001*math.cos(math.radians(theta_deg))
                *(p/tR)**2 + 0.6666*fM*q_msc**2/d_in**5))
    half = 18.75*gamma_g*L_ft/2.0
    def rm(pmid):
        tmid = 0.5*(t_head_F + t_bh_F)
        return half - (pmid - phf)*(I(pmid, tmid) + I(phf, t_head_F))
    pmid = brentq(rm, phf, phf*5 + 1000, xtol=1e-3)
    def rb(pbh):
        return half - (pbh - pmid)*(I(pbh, t_bh_F)
                                    + I(pmid, 0.5*(t_head_F+t_bh_F)))
    return brentq(rb, pmid, pmid*5 + 1000, xtol=1e-3)

def poettmann_carpenter_bhp(phf, t_head_F, t_bh_F, d_in, depth_ft,
                              q_liq, wc, glr, api, gamma_w, gamma_g,
                              dz=100.0):
    """Eqs. 4.8-4.17."""
    go = 141.5/(api + 131.5)
    p = phf; h = 0.0
    while h < depth_ft:
        step = min(dz, depth_ft - h)
        tF = t_head_F + (t_bh_F - t_head_F)*(h + step/2)/depth_ft
        tR = tF + 460.0
        rs = gamma_g*((p/18)*10**(0.0125*api)/10**(0.00091*tF))**1.2048
        bo = 0.9759 + 0.00012*(rs*(gamma_g/go)**0.5 + 1.25*tF)**1.2
        M = 350.17*(go + wc*gamma_w) + glr*0.0764*gamma_g
        vm = 5.615*(bo + wc) + (glr - rs)*(14.7/p)*(tR/520.0)
        rho = M/vm
        dpv = 1.4737e-5*M*q_liq/(d_in/12)
        f2 = 10**(1.444 - 2.5*math.log10(dpv))
        kh = f2*q_liq**2*M**2/(7.4137e10*(d_in/12)**5)
        p += (rho + kh/rho)*step/144.0
        h += step
    return p

def guo_ghalambor_bhp_robust(phf, t_head_F, t_bh_F, d_in, L_ft,
                              theta_deg, q_g, q_o, q_w, q_s,
                              gamma_g, gamma_o, gamma_w, gamma_s,
                              rel_rough=6e-4):
    """Eq. 4.18."""
    from scipy.optimize import brentq
    tR = 0.5*(t_head_F + t_bh_F) + 460.0
    A = math.pi*(d_in/2/12)**2
    dh = d_in/12
    fM = (1.0/(1.74 - 2.0*math.log10(2.0*rel_rough/d_in)))**2
    a = (15.33*gamma_s*q_s + 86.07*gamma_w*q_w
         + 86.07*gamma_o*q_o + 18.79*gamma_g*q_g)/(1e3*tR*q_g)
    b = (0.2456*q_s + 1.379*q_w + 1.379*q_o)/(1e3*tR*q_g)
    c = 6.785e-6*tR*q_g/A
    d = (q_s + 5.615*(q_w + q_o))/(600.0*A)
    e = 6.0*fM/(2*32.17*dh)
    ct = math.cos(math.radians(theta_deg))
    den = ct + d*d*e
    M = c*d*e/den; N = c*c*e*ct/den**2; sn = math.sqrt(N)
    def res(p):
        arg = (144*p + M)**2 + N
        arg_hf = (144*phf + M)**2 + N
        t1 = 144*b*(p - phf)
        t2 = 0.5*(1 - 2*b*M)*math.log(arg/arg_hf)
        coef = (M + b*N/c - b*M**2)/sn
        t3 = coef*(math.atan((144*p+M)/sn) - math.atan((144*phf+M)/sn))
        return t1 + t2 - t3 - a*(1 + d*d*e)*L_ft
    return brentq(res, phf, phf*20 + 10000, xtol=1e-4)

def _mhb_cnl(N_L):
    X1 = math.log10(N_L + 3.0)
    Y = (-2.69851 + 0.15841*X1 - 0.55100*X1**2
         + 0.54785*X1**3 - 0.12195*X1**4)
    return 10**Y

def _mhb_yL_psi(X2):
    x = math.log10(X2) + 6.0
    return (-0.10307 + 0.61777*x - 0.63295*x**2
            + 0.29598*x**3 - 0.0401*x**4)

def _mhb_psi(X3):
    if X3 <= 0.01: return 1.0
    return (0.91163 - 4.82176*X3 + 1232.25*X3**2
            - 22253.6*X3**3 + 116174.3*X3**4)

def mhb_liquid_holdup(N_VL, N_VG, N_D, N_L, p, rho_L=62.4):
    cnl = _mhb_cnl(N_L)
    x2 = N_VL*p**0.1*cnl/(N_VG**0.575*14.7**0.1*N_D)
    ypsi = _mhb_yL_psi(x2)
    x3 = N_VG*N_L**0.38/N_D**2.14
    return ypsi*_mhb_psi(x3)

def mhb_pressure_traverse_full(phf, t_head_F, t_bh_F, d_in, L_ft,
                                 q_liq, glr, wc, api, gamma_g,
                                 gamma_w=1.05, sigma=30.0,
                                 mu_l=5.0, dz=50.0) -> np.ndarray:
    """Full mH-B traverse."""
    go = 141.5/(api + 131.5)
    dh = d_in/12; A = math.pi*(dh/2)**2
    rho_L = 62.4*go
    pts = [(0.0, phf)]
    p = phf; h = 0.0
    while h < L_ft:
        step = min(dz, L_ft - h)
        tF = t_head_F + (t_bh_F - t_head_F)*(h + step/2)/L_ft
        tR = tF + 460.0
        rs = gamma_g*((p/18)*10**(0.0125*api)/10**(0.00091*tF))**1.2048
        bo = 0.9759 + 0.00012*(rs*(gamma_g/go)**0.5 + 1.25*tF)**1.2
        rho_G = 2.7*gamma_g*p/(1.0*tR)
        usl = q_liq*(bo + wc)/(86400*A)
        qgres = q_liq*glr*(tR/520)*(14.7/p)
        usg = qgres/(86400*A)
        NVL = 1.938*usl*math.sqrt(rho_L/sigma)
        NVG = 1.938*usg*math.sqrt(rho_L/sigma)
        ND = 120.872*dh*math.sqrt(rho_L/sigma)
        NL = 0.15726*mu_l*math.sqrt(1.0/(rho_L*sigma**3))
        yL = mhb_liquid_holdup(NVL, NVG, ND, NL, p, rho_L)
        um = usl + usg
        yLns = usl/um if um > 0 else 1.0
        yL = max(yL, yLns)
        rho_m = yL*rho_L + (1-yL)*rho_G
        lamG = usg/um if um > 0 else 0.0
        LB = max(1.071 - 0.2218*um*um/dh, 0.13)
        if lamG < LB:
            u_s = 0.8
            inner = (1 + um/u_s)**2 - 4*usg/u_s
            yL = 1.0 - 0.5*(1 + um/u_s - math.sqrt(max(inner, 0)))
            ml = rho_L*q_liq*bo/86400.0
            Nre = max(2.2e-2*ml/(dh*mu_l), 2100)
        else:
            mu_mix = (mu_l**yL)*(0.02**(1-yL))
            Nre = max(2.2e-2*(q_liq*(bo+wc)*rho_m/86400)
                      /(dh*mu_mix), 2100)
        fF = friction_chen(Nre, 6e-4)
        dpf = 2*fF*rho_m*um*um/(32.17*dh)
        p += (rho_m + dpf)/144.0*step
        h += step
        pts.append((h, p))
    return np.array(pts)

def mist_flow_bhp(phf, t_head_F, t_bh_F, d_in, L_ft, theta_deg,
                   q_g_scfd, q_cond_bpd=0.0, q_w_bpd=0.0,
                   q_sand_ft3d=0.0, gamma_g=0.7, gamma_o=0.85,
                   gamma_w=1.05, gamma_s=2.65, rel_rough=6e-4):
    return guo_ghalambor_bhp_robust(phf, t_head_F, t_bh_F, d_in,
        L_ft, theta_deg, q_g_scfd, q_cond_bpd, q_w_bpd, q_sand_ft3d,
        gamma_g, gamma_o, gamma_w, gamma_s, rel_rough)

def identify_flow_regime(u_sl, u_sg, d_in, rho_l=62.4,
                          rho_g=2.0, sigma=30.0) -> str:
    vm = u_sl + u_sg
    if vm < 1e-9: return "bubble"
    Nvg = 1.938*u_sg*math.sqrt(rho_l/sigma)
    if u_sg < 0.5*u_sl + 0.1: return "bubble"
    if Nvg > 50 and u_sl < 5: return "annular"
    if Nvg > 3: return "churn"
    return "slug"
