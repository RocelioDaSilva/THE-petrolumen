"""Chapter 18 -- Production Optimization."""
import math
import numpy as np
from dataclasses import dataclass
from scipy.optimize import brentq, minimize

def ki_standing(p, tR, pc, Tb, Tc):
    a = 1.2 + 4.5e-4*p + 1.5e-9*p**2
    c = 0.89 - 1.7e-4*p - 3.5e-8*p**2
    bi = math.log10(pc/14.7)/(1.0/Tb - 1.0/Tc)
    Fi = bi*(1.0/Tb - 1.0/tR)
    return (1.0/p)*10**(a + c*Fi)

def flash_standing(z, p, tR, pc, Tb, Tc, MW):
    ki = np.array([ki_standing(p, tR, pc[i], Tb[i], Tc[i])
                   for i in range(len(z))])
    def rr(nv):
        return np.sum(z*(ki - 1)/(nv*(ki - 1) + 1))
    try: nv = brentq(rr, 1e-9, 1 - 1e-9, xtol=1e-12)
    except ValueError: nv = 1.0 if rr(0.5) > 0 else 0.0
    nl = 1.0 - nv
    x = z/(nl + ki*nv); y = ki*x
    return {"nv": nv, "nl": nl, "x": x, "y": y,
            "MW_L": float(np.sum(x*MW)),
            "MW_V": float(np.sum(y*MW)), "ki": ki}

def series_capacity_ratio(L, D1, L1, D2):
    return math.sqrt((L/D1**(16/3))
                      /(L1/D1**(16/3) + (L - L1)/D2**(16/3)))

def parallel_capacity_ratio(D1, D2):
    return ((math.sqrt(D1**(16/3)) + math.sqrt(D2**(16/3)))
            /math.sqrt(D1**(16/3)))

def looped_capacity_ratio(L, D1, L1, D2):
    den = (L1/(math.sqrt(D1**(16/3)) + math.sqrt(D2**(16/3)))**2
           + (L - L1)/D1**(16/3))
    return math.sqrt((L/D1**(16/3))/den)

def npv(cfs, i):
    return sum(cf/(1 + i)**t for t, cf in enumerate(cfs))

def project_npv(dnp, price, disc, cost):
    return npv([price*d for d in dnp], disc) - cost

def optimize_lift_gas_allocation(wells, total_gas,
                                  max_per_well=float("inf")):
    n = len(wells)
    def neg(x): return -sum(wells[i]["q_vs_gas"](x[i])
                            for i in range(n))
    def cons(x): return total_gas - sum(x)
    bounds = [(0, min(max_per_well, total_gas))]*n
    x0 = np.full(n, total_gas/n)
    res = minimize(neg, x0, method="SLSQP", bounds=bounds,
                   constraints=[{"type": "ineq", "fun": cons}],
                   options={"ftol": 1e-6, "maxiter": 200})
    return {"allocation": res.x.tolist(),
            "total_oil": float(-res.fun), "success": res.success}

@dataclass
class NetworkNode:
    name: str
    pressure_required: float = 0.0
    max_rate: float = float("inf")

@dataclass
class NetworkEdge:
    from_node: str
    to_node: str
    L_mi: float
    D_in: float
    gamma_g: float = 0.7
    T_R: float = 520.0

    def pressure_drop(self, q):
        c = q*14.7/(0.433*520.0)
        return (c*c)*(self.gamma_g*self.T_R*self.L_mi*5280
                      /self.D_in**(16/3))

def optimize_network(nodes, edges, supply, p_supply, demand,
                      q_lo=100.0, q_hi=1e8, tol=1e-3):
    def res(q):
        p2 = p_supply*p_supply
        for e in edges:
            p2 -= e.pressure_drop(q)
            if p2 < 0: return -1e9
        return math.sqrt(p2) - nodes[demand].pressure_required
    try: q = brentq(res, q_lo, q_hi, xtol=tol)
    except ValueError: q = q_lo
    return {"flow_scfd": q}
