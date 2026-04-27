import numpy as np
from typing import Callable, List, Dict, Any
from scipy.interpolate import interp1d

def ipr_vogel(p_res: float, p_wf_range: np.ndarray, q_max: float) -> np.ndarray:
    """Vogel's IPR: q/q_max = 1 - 0.2*(p_wf/p_res) - 0.8*(p_wf/p_res)**2"""
    return q_max * (1 - 0.2 * (p_wf_range / p_res) - 0.8 * (p_wf_range / p_res)**2)

def ipr_fetkovich(p_res: float, p_wf_range: np.ndarray, C: float, n: float) -> np.ndarray:
    """Fetkovich IPR: q = C * (p_res**2 - p_wf**2)**n"""
    return C * (p_res**2 - p_wf_range**2)**n

def vlp_beggs_brill_simplified(q_range: np.ndarray, p_wh: float, depth: float, d_in: float) -> np.ndarray:
    """
    EXTREMELY simplified VLP for skeleton.
    """
    return p_wh + 0.01 * depth + 0.0005 * q_range**1.8

def solve_nodal(p_res: float, q_max: float, p_wh: float, depth: float) -> Dict[str, Any]:
    q_range = np.linspace(0, q_max, 50)
    p_wf_test = np.linspace(0, p_res, 100)
    q_vogel = ipr_vogel(p_res, p_wf_test, q_max)

    pwf_vlp = vlp_beggs_brill_simplified(q_range, p_wh, depth, 2.441)

    # Intersection
    f_ipr = interp1d(q_vogel[::-1], p_wf_test[::-1], bounds_error=False, fill_value="extrapolate")
    pwf_ipr_resampled = f_ipr(q_range)

    diff = pwf_ipr_resampled - pwf_vlp
    # Find root
    idx = np.where(np.diff(np.sign(diff)))[0]
    if len(idx) > 0:
        q_op = float(q_range[idx[0]])
        p_op = float(pwf_vlp[idx[0]])
    else:
        q_op, p_op = 0.0, 0.0

    return {
        "operating_point": {"q": q_op, "p": p_op},
        "curves": {
            "q": q_range.tolist(),
            "p_ipr": pwf_ipr_resampled.tolist(),
            "p_vlp": pwf_vlp.tolist()
        }
    }
