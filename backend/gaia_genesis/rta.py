import numpy as np
from typing import Dict, Any
from .pvt import calculate_zfactor

def fmb_gas(p_wf: np.ndarray, Gp: np.ndarray, p_i: float, T_f: float, gamma_g: float) -> Dict[str, Any]:
    """
    Flowing Material Balance for Gas.
    p_wf/Z vs Gp should be a straight line.
    """
    z_wf = np.array([calculate_zfactor(p, T_f, gamma_g) for p in p_wf])
    pz = p_wf / z_wf
    zi = calculate_zfactor(p_i, T_f, gamma_g)
    pi_zi = p_i / zi

    # Linear fit: pz = pi_zi - (pi_zi/OGIP) * Gp
    # y = c + m*x => c = pi_zi, m = -pi_zi/OGIP
    slope, intercept = np.polyfit(Gp, pz, 1)

    ogip = -pi_zi / slope if slope != 0 else 0

    return {
        "ogip": float(ogip),
        "pi_zi": float(pi_zi),
        "slope": float(slope),
        "intercept": float(intercept),
        "data": {
            "Gp": Gp.tolist(),
            "pz": pz.tolist()
        }
    }

def fmb_oil(p_wf: np.ndarray, Np: np.ndarray, p_i: float, Boi: float, co: float) -> Dict[str, Any]:
    """
    Flowing Material Balance for Oil (Under-saturated).
    p_wf vs Np.
    """
    # p_wf = p_i - (Boi / (OOIP * Boi * co)) * Np
    # p_wf = p_i - (1 / (OOIP * co)) * Np
    slope, intercept = np.polyfit(Np, p_wf, 1)

    ooip = -1 / (slope * co) if slope != 0 else 0

    return {
        "ooip": float(ooip),
        "pi": float(intercept),
        "slope": float(slope),
        "data": {
            "Np": Np.tolist(),
            "pwf": p_wf.tolist()
        }
    }
