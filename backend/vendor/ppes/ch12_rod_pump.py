"""Chapter 12 -- Sucker Rod Pumping."""
import math
from dataclasses import dataclass
from pathlib import Path
import pandas as pd

def machinery_factor(coh, bal="conventional"):
    return 1 + coh if bal == "conventional" else 1 - coh

def F1(S, N, coh, bal="conventional"):
    sg = 1 if bal == "conventional" else -1
    return S*N*N*(1 + sg*coh)/70471.2

def F2(S, N, coh, bal="conventional"):
    sg = 1 if bal == "conventional" else -1
    return S*N*N*(1 - sg*coh)/70471.2

def max_acceleration_ft_s2(S, N, coh, bal="conventional"):
    M = 1 + coh if bal == "conventional" else 1 - coh
    return S*N*N*32.17*M/70471.2

def prl_max(Wf, Wr, F1v): return Wf + (0.9 + F1v)*Wr
def prl_min(Wr, F2v): return (0.9 - F2v)*Wr

def peak_torque(S, Wf, N, Wr):
    return 0.25*S*(Wf + 2*S*N*N*Wr/70471.2)

def counterbalance(Wf, Wr, S, N, coh):
    return 0.5*Wf + Wr*(0.9 + S*N*N*coh/70471.2)

def speed_limit(S, coh, L=0.5, bal="conventional"):
    sg = 1 if bal == "conventional" else -1
    return 187.7/math.sqrt(S*(1 + sg*coh))

def plunger_production(Ap, N, Sp, Er, Bo):
    return 0.1484*Ap*N*Sp*Er/Bo

def hydraulic_power(q, gL, LN):
    return 7.36e-6*q*gL*LN

def friction_power(Wr, S, N):
    return 6.31e-7*Wr*S*N

def prime_mover(hyd, fric, Fs=1.35):
    return Fs*(hyd + fric)

def plunger_overtravel(D, S, N, M):
    """Eq. 12.41."""
    return 1.93e-11*D*D*S*N*N*M

@dataclass
class DynamometerReading:
    C: float
    D1: float
    D2: float
    D3: float = 0.0
    A1: float = 0.0
    A2: float = 0.0
    L: float = 1.0
    S: float = 1.0
    N: float = 1.0

def analyze_card(r):
    PPRL = r.C*r.D1
    MPRL = r.C*r.D2
    ROL = r.C*(r.D1 - r.D2)
    AUL = r.C*(r.A1 + r.A2)/r.L if r.L else 0
    ADL = r.C*r.A1/r.L if r.L else 0
    AICB = 0.5*(PPRL + MPRL)
    ACBE = r.C*r.D3
    CCB = r.C*(r.A1 + r.A2)/(2*r.L) if r.L else 0
    PRHP = (r.C*r.S*r.N*r.A2)/(33000*12*r.L) if r.L else 0
    return {"PPRL": PPRL, "MPRL": MPRL, "ROL": ROL, "AUL": AUL,
            "ADL": ADL, "AICB": AICB, "ACBE": ACBE, "CCB": CCB,
            "PRHP": PRHP}

_DATA = Path(__file__).parent/"data"

def load_units():
    return pd.read_csv(_DATA/"api_pumping_units.csv")

@dataclass
class PumpingUnit:
    name: str
    peak_torque_in_lb: float
    prl_lb: float
    stroke_in: float
    d1_in: float = 0
    d2_in: float = 0
    c_in: float = 0
    h_in: float = 0

def select_pumping_unit(need_stroke, need_torque, need_prl,
                         unit_type="conventional"):
    df = load_units()
    df = df[(df.type == unit_type)
            & (df.stroke_in >= need_stroke)
            & (df.torque_in_lb >= need_torque)
            & (df.prl_lb >= need_prl)]
    if df.empty: raise ValueError("No API unit meets requirements")
    r = df.sort_values("torque_in_lb").iloc[0]
    return PumpingUnit(r["name"], r["torque_in_lb"], r["prl_lb"],
                        r["stroke_in"])

def lookup_pump_config(size_unit, pump_depth):
    df = pd.read_csv(_DATA/"api_rod_pump_table_12_4.csv")
    df = df[df.size_unit == size_unit]
    for _, row in df.iterrows():
        lo, hi = map(float, row.pump_depth_ft.split("-"))
        if lo <= pump_depth <= hi:
            return {"plunger_in": row.plunger_in,
                    "tubing_in": row.tubing_in,
                    "rod_in": row.rod_in,
                    "pumping_spm": row.pumping_spm}
    raise ValueError(f"No config for size {size_unit} at {pump_depth}")
