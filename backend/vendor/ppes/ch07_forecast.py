"""Chapter 7 -- Production Forecast."""
from dataclasses import dataclass, field
import math
import numpy as np

@dataclass
class ForecastStep:
    pressure: float
    rate: float
    cum_prod: float
    time_days: float

@dataclass
class ForecastResult:
    steps: list[ForecastStep] = field(default_factory=list)

    def to_table(self):
        import pandas as pd
        return pd.DataFrame([s.__dict__ for s in self.steps])

@dataclass
class PVTTable:
    pressures: np.ndarray
    Rs: np.ndarray
    Bo: np.ndarray
    Bg: np.ndarray
    mu_o: np.ndarray
    kro: np.ndarray
    krg: np.ndarray

    def interp(self, p):
        return {
            "Rs": float(np.interp(p, self.pressures, self.Rs)),
            "Bo": float(np.interp(p, self.pressures, self.Bo)),
            "Bg": float(np.interp(p, self.pressures, self.Bg)),
            "mu_o": float(np.interp(p, self.pressures, self.mu_o)),
            "kro": float(np.interp(p, self.pressures, self.kro)),
            "krg": float(np.interp(p, self.pressures, self.krg)),
        }

def transient_forecast_oil(k, h, bo, mu, phi, ct, rw, skin,
                             p_i, t_months, tpr_func):
    from scipy.optimize import brentq
    from .ch03_ipr import transient_ipr_oil
    res = ForecastResult()
    cum = 0.0
    for m in range(1, t_months + 1):
        th = m*30*24.0
        def rq(q):
            return transient_ipr_oil(p_i, k, h, bo, mu, phi, ct,
                                      rw, skin, th, q) - tpr_func(q)
        try: q = brentq(rq, 0.1, 5000.0, xtol=1e-3)
        except ValueError: q = 0.0
        cum += q*30
        res.steps.append(ForecastStep(
            transient_ipr_oil(p_i, k, h, bo, mu, phi, ct,
                                rw, skin, th, q),
            q, cum, m*30))
    return res

def pseudo_steady_1phase_oil(p_initial, p_bubble, p_abandon,
                               j_star, bo, ct, ooip, tpr_func,
                               n_steps=10):
    from scipy.optimize import brentq
    pr = np.linspace(p_initial, max(p_abandon, p_bubble), n_steps)
    res = ForecastResult()
    cum = 0.0; t = 0.0
    for i in range(len(pr)-1):
        p0, p1 = pr[i], pr[i+1]
        pbar = 0.5*(p0 + p1)
        def rq(q): return j_star*(pbar - tpr_func(q)) - q
        try: q = brentq(rq, 1e-3, j_star*pbar*0.99, xtol=1e-4)
        except ValueError: q = 0.0
        r0 = np.exp(ct*(p_initial - p0)) - 1
        r1 = np.exp(ct*(p_initial - p1)) - 1
        dnp = (r1 - r0)*ooip
        dt = dnp/q if q > 0 else 0.0
        cum += dnp; t += dt
        res.steps.append(ForecastStep(pbar, q, cum, t))
    return res

def tarver_two_phase(p_initial, p_abandon, swi, N_ooip, pvt,
                      n_steps=10, max_iter=200, tol=1e-8):
    pr = np.linspace(p_initial, p_abandon, n_steps)
    Np = [0.0]; Gp = [0.0]; R_h = [float(pvt.interp(p_initial)["Rs"])]
    So_h = [1.0 - swi]
    for i in range(1, n_steps):
        p0, p1 = pr[i-1], pr[i]
        d0, d1 = pvt.interp(p0), pvt.interp(p1)
        Bo0, Bo1 = d0["Bo"], d1["Bo"]
        Bg0 = d0["Bg"]; Rs0, Rs1 = d0["Rs"], d1["Rs"]
        dB = Bo0 - Bo1; dR = Rs1 - Rs0
        den = dB + dR*Bg0
        phi_o = (Bo0 - Rs0*Bg0)/den if den else 0.0
        phi_g = Bg0/den if den else 0.0
        R = Rs1
        for _ in range(max_iter):
            Np_p = Np[-1]; Gp_p = Gp[-1]
            dN = (1 - phi_o*Np_p - phi_g*Gp_p)/(phi_o + R*phi_g)
            Np_n = Np_p + dN; Gp_n = Gp_p + dN*R
            So = (Bo1/Bo0)*(1-swi)*(1-Np_n)
            kro = d1["kro"]; krg = d1["krg"]
            Rn = Rs1 + (krg/kro)*(Bo1/Bg0 if Bg0 > 0 else 0)
            if abs(Rn - R)/max(R, 1.0) < tol: R = Rn; break
            R = Rn
        Np.append(Np_n); Gp.append(Gp_n); R_h.append(R); So_h.append(So)
    return {"pressures": pr, "Np": np.array(Np)*N_ooip,
            "Gp": np.array(Gp)*N_ooip,
            "R": np.array(R_h), "So": np.array(So_h)}

def gas_forecast_pseudo_steady(k, h, t_R, phi, ct, rw, re,
                                p_initial, p_abandon, G_initial,
                                m_pwf, n_steps=10):
    pr = np.linspace(p_initial, p_abandon, n_steps)
    Gp = [0.0]; q_h = []
    for i in range(1, n_steps):
        p = pr[i]
        q = (k*h*(p*p - m_pwf))/(1424*t_R*math.log(0.472*re/rw))
        q_h.append(q); Gp.append(Gp[-1] + q*30.0)
    return {"pressures": pr, "Gp": np.array(Gp), "q": np.array(q_h)}
