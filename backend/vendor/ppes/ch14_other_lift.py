"""Chapter 14 -- Other Artificial Lift."""
import math
from pathlib import Path
import pandas as pd

_DATA = Path(__file__).parent/"data"

def pump_head(dp): return dp/0.433
def min_pump_depth(D, pwf, p_suc, gL):
    return D - (pwf - p_suc)/(0.433*gL)
def hpp_flow_ratio(q_eng, Ap, Ae): return q_eng*Ap/Ae
def hpp_net_lift(Dp, p_in, Gb): return Dp - p_in/Gb
def hpp_pe_ratio(LN): return 10000.0/LN
def pcp_displacement(D, E, Ps): return 0.028*D*E*Ps
def pcp_rate(D, E, Ps, N, Qs=0.0): return 7.12*D*E*Ps*N - Qs
def pcp_head_rating(np_p, dp): return (2*np_p - 1)*dp
def pcp_torque(V0, DP, ep=0.5): return 144*V0*DP/ep
def pcp_thrust(DP, D, E): return math.pi/4*(2*E + D)**2*DP
def plunger_glr_min(D): return 400.0*D/1000.0
def plunger_pressure_improved(pL, psh, fsl=0.55): return pL + psh/fsl

def turner_min_rate_complete(q_liq, gL, sigma, d_in, p, t_F, z,
                               gg, water=True):
    tR = t_F + 460.0
    rg = 2.7*gg*p/(z*tR); rl = gL*62.4
    vs = 1.3*(sigma**0.25)*((rl - rg)**0.25)/((0.44**0.25)*rg**0.5)
    if water: vs *= 1.2
    A = math.pi*(d_in/2/12)**2
    return 3.06*p*vs*A/(tR*z)

def load_hpp_catalog():
    return pd.read_csv(_DATA/"hpp_catalog.csv")

def select_hpp_from_catalog(q_req, net_lift):
    df = load_hpp_catalog()
    pe = 10000.0/max(net_lift, 1.0)
    cand = df[(df.q_max_bpd >= q_req) & (df.P_E_ratio >= pe*0.8)]
    if cand.empty: raise ValueError("No HPP meets requirements")
    r = cand.sort_values("P_E_ratio").iloc[0]
    return {"name": r["name"], "P_E_ratio": float(r["P_E_ratio"]),
            "q_max_bpd": float(r["q_max_bpd"]),
            "N_max_spm": float(r["N_max_spm"])}

def load_esp_catalog():
    return pd.read_csv(_DATA/"esp_catalog.csv")

def select_esp_from_csv(q_req, tdh, tol=1.10):
    import numpy as np
    df = load_esp_catalog()
    for name in df.name.unique():
        s = df[df.name == name]
        qmin = s.min_capacity_bpd.iloc[0]
        qmax = s.max_capacity_bpd.iloc[0]
        if qmin*0.9 <= q_req <= qmax*tol:
            hs = float(np.interp(q_req, s.stages_flow_bpd,
                                  s.stages_head_ft))
            hp = float(np.interp(q_req, s.stages_flow_bpd,
                                  s.stages_hp))
            eff = float(np.interp(q_req, s.stages_flow_bpd,
                                   s.stages_eff))
            n = int(math.ceil(tdh/hs)) if hs > 0 else 0
            return {"series": name, "n_stages": n,
                    "total_hp": hp*n, "eff": eff,
                    "head_per_stage_ft": hs}
    raise ValueError(f"No ESP covers {q_req}")
