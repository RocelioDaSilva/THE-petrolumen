"""FastAPI REST layer."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .. import (ch02_pvt, ch03_ipr, ch04_tpr, ch05_choke,
                 ch06_nodal, ch08_decline, ch09_tubing,
                 ch10_separation, ch11_transport, ch12_rod_pump,
                 ch13_gas_lift, ch16_acidizing, ch17_fracturing,
                 ch18_optimization)

app = FastAPI(title="PPES", version="1.0.0")

class OilPVTIn(BaseModel):
    p: float = Field(..., gt=0)
    t_F: float
    api: float = Field(..., gt=0, lt=100)
    rs: float = Field(..., ge=0)
    gamma_g: float = Field(..., gt=0, lt=2)

class ZIn(BaseModel):
    p: float; t_F: float; gamma_g: float
    method: str = "hall_yarborough"

class VogelIn(BaseModel):
    qmax: float; pwf: float; pbar: float

class ChokeGasIn(BaseModel):
    cd: float; d2_in: float; p_up: float; p_dn: float
    t_up_F: float; gamma_g: float; k: float = 1.28

class GilbertIn(BaseModel):
    q_bpd: float; glr: float; choke_64: float
    correlation: str = "Gilbert"

class DeclineIn(BaseModel):
    model: str; qi: float; b: float; t: float; a: float = 1.5

class TubingCollapseIn(BaseModel):
    p_c: float; sa: float; ym: float

class SeparatorIn(BaseModel):
    D_ft: float; K: float; p: float; T_F: float; z: float
    gamma_g: float; rho_l: float

class WallThickIn(BaseModel):
    pd: float; D_in: float; sigma_y: float
    eta: float = 0.72; t_a: float = 0.0625

class RodPRLIn(BaseModel):
    Wf: float; Wr: float; S_in: float; N_spm: float
    c_over_h: float

class ValveIn(BaseModel):
    pd: float; St: float; R: float; pt: float

class AcidIn(BaseModel):
    r_a: float; r_w: float; phi: float; C_m: float
    beta: float; rho_a: float; rho_m: float

class FracBreakIn(BaseModel):
    rho: float; H_ft: float; alpha: float; pp: float
    nu: float; stect: float; T0: float

class FoldIn(BaseModel):
    re: float; rw: float; Sf: float

@app.get("/health")
def health(): return {"status": "ok", "version": "1.0.0"}

@app.post("/pvt/oil")
def api_pvt_oil(req: OilPVTIn):
    return {
        "gamma_o": 141.5/(req.api + 131.5),
        "rho_o": ch02_pvt.rho_o(req.p, req.t_F, req.api,
                                  req.rs, req.gamma_g),
        "Bo": ch02_pvt.bo_standing(req.t_F, req.api, req.rs,
                                     req.gamma_g),
        "mu_od": ch02_pvt.mu_dead_oil(req.api, req.t_F),
    }

@app.post("/pvt/z")
def api_z(req: ZIn):
    ppc, tpc = ch02_pvt.pseudo_critical_from_sg(req.gamma_g)
    ppr = req.p/ppc; tpr = (req.t_F + 460)/tpc
    if req.method == "brill_beggs":
        return {"z": ch02_pvt.z_brill_beggs(ppr, tpr)}
    return {"z": ch02_pvt.z_hall_yarborough(ppr, tpr)}

@app.post("/ipr/vogel")
def api_vogel(req: VogelIn):
    return {"q": ch03_ipr.vogel_rate(req.qmax, req.pwf, req.pbar)}

@app.post("/choke/gas")
def api_choke_gas(req: ChokeGasIn):
    import math
    A2 = math.pi*(req.d2_in/2)**2
    rc = ch05_choke.critical_ratio(req.k)
    ratio = req.p_dn/req.p_up
    if ratio < rc:
        q = ch05_choke.q_sonic_gas(req.cd, A2, req.p_up,
                                     req.t_up_F+460, req.gamma_g, req.k)
        return {"q_Mscf_d": q, "regime": "sonic"}
    q = ch05_choke.q_subsonic_gas(req.cd, A2, req.p_up, req.p_dn,
                                    req.t_up_F+460, req.gamma_g, req.k)
    return {"q_Mscf_d": q, "regime": "subsonic"}

@app.post("/choke/gilbert")
def api_gilbert(req: GilbertIn):
    return {"p_up": ch05_choke.gilbert_choke(
        req.q_bpd, req.glr, req.choke_64, req.correlation)}

@app.post("/decline/rate")
def api_dec_rate(req: DeclineIn):
    if req.model == "exponential":
        return {"q": ch08_decline.exponential_rate(req.qi, req.b, req.t)}
    if req.model == "harmonic":
        return {"q": ch08_decline.harmonic_rate(req.qi, req.b, req.t)}
    return {"q": ch08_decline.hyperbolic_rate(req.qi, req.a, req.b, req.t)}

@app.post("/tubing/collapse")
def api_tubing_collapse(req: TubingCollapseIn):
    return {"p_cc": ch09_tubing.collapse_biaxial(
        req.p_c, req.sa, req.ym)}

@app.post("/separator/gas")
def api_sep_gas(req: SeparatorIn):
    return {"q_mmscfd": ch10_separation.gas_capacity(
        req.D_ft, req.K, req.p, req.T_F, req.z, req.gamma_g, req.rho_l)}

@app.post("/pipeline/wall")
def api_wall(req: WallThickIn):
    return {"t_in": ch11_transport.wall_thickness_internal(
        req.pd, req.D_in, req.sigma_y, req.eta, t_a=req.t_a)}

@app.post("/rod-pump/prl")
def api_rod_prl(req: RodPRLIn):
    F1 = ch12_rod_pump.F1(req.S_in, req.N_spm, req.c_over_h)
    F2 = ch12_rod_pump.F2(req.S_in, req.N_spm, req.c_over_h)
    return {"PRL_max": ch12_rod_pump.prl_max(req.Wf, req.Wr, F1),
            "PRL_min": ch12_rod_pump.prl_min(req.Wr, F2),
            "peak_torque": ch12_rod_pump.peak_torque(
                req.S_in, req.Wf, req.N_spm, req.Wr)}

@app.post("/gas-lift/valve")
def api_valve(req: ValveIn):
    return {"p_open": ch13_gas_lift.valve_opening_pressure(
        req.pd, req.St, req.R, req.pt),
        "p_close": ch13_gas_lift.valve_closing_pressure(
            req.pd, req.St, req.R)}

@app.post("/acid/preflush")
def api_acid(req: AcidIn):
    return {"V_gal": ch16_acidizing.preflush_volume(
        req.r_a, req.r_w, req.phi, req.C_m, req.beta,
        req.rho_a, req.rho_m)*7.48}

@app.post("/frac/breakdown")
def api_frac_bd(req: FracBreakIn):
    sv = ch17_fracturing.overburden(req.rho, req.H_ft)
    return {"p_bd": ch17_fracturing.breakdown_pressure(
        sv, req.alpha, req.pp, req.nu, req.stect, req.T0)}

@app.post("/frac/fold")
def api_fold(req: FoldIn):
    return {"J_ratio": ch17_fracturing.fold_of_increase(
        req.re, req.rw, req.Sf)}

@app.post("/pipeline/loop")
def api_loop(L: float, D1: float, L1: float, D2: float):
    return {"ratio": ch18_optimization.looped_capacity_ratio(
        L, D1, L1, D2)}
