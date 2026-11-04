"""Chapter 6 â€” Well Deliverability / Nodal Analysis (pp. 6/69 â€“ 6/85)."""
from __future__ import annotations
from scipy.optimize import brentq


def operating_point_gas(ipr_c, ipr_n, pbar, tpr_func,
                        q_lo=1e-3, q_hi=1e7):
    """Gas well nodal â€” intersection of Eq. 6.1 (IPR) and Eq. 6.2 (TPR).

    tpr_func(q_sc) -> p_wf [psia]. Returns (q_sc, p_wf).
    """
    def residual(q):
        p_ipr = (pbar**2 - (q/ipr_c)**(1.0/ipr_n))**0.5
        return p_ipr - tpr_func(q)
    q = brentq(residual, q_lo, q_hi, xtol=1e-6)
    return q, tpr_func(q)


def operating_point_oil_vogel(qmax, pbar, tpr_func,
                              q_lo=1e-3, q_hi=1e7):
    """Oil well nodal â€” Vogel IPR + arbitrary TPR (Eqs. 6.8, 6.9)."""
    from .ch03_ipr import vogel_pwf
    def residual(q):
        return vogel_pwf(q, qmax, pbar) - tpr_func(q)
    q = brentq(residual, q_lo, q_hi, xtol=1e-6)
    return q, tpr_func(q)


def multilateral_oil_rate(*args, **kwargs):
    """Multilateral oil deliverability â€” Eqs. 6.44â€“6.59 (p. 6/82).

    TODO: solve the (4n-1) nonlinear system of Eqs. 6.44â€“6.57 with
    scipy.optimize.fsolve. Validate against Example 6.10 (973 stb/d).
    """
    raise NotImplementedError("Implement per Eqs. 6.44â€“6.59, p. 6/82.")


def multilateral_gas_rate(*args, **kwargs):
    """Multilateral gas deliverability â€” Eqs. 6.32â€“6.42 (p. 6/82).

    TODO: solve the coupled system. Validate against Example 6.9
    (total 4,280 Mscl/d).
    """
    raise NotImplementedError("Implement per Eqs. 6.32â€“6.42, p. 6/82.")