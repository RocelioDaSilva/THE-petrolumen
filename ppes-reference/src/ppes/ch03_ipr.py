"""Chapter 3 â€” Reservoir Deliverability (pp. 3/29 â€“ 3/43)."""
from __future__ import annotations
import math
import numpy as np


def j_star_pseudosteady(k, h, bo, mu, A, ca, rw, skin) -> float:
    """Pseudo-steady productivity index â€” Eq. 3.17 (p. 3/33). [stb/d/psi]"""
    gamma = 1.78  # Euler's constant, Eq. 3.9
    return k*h / (141.2 * bo * mu
                  * (0.5*math.log(4*A/(gamma*ca*rw**2)) + skin))


def vogel_rate(qmax: float, pwf: float, pbar: float) -> float:
    """Vogel IPR â€” Eq. 3.19 (p. 3/34)."""
    r = pwf / pbar
    return qmax * (1 - 0.2*r - 0.8*r*r)


def vogel_pwf(q: float, qmax: float, pbar: float) -> float:
    """Vogel inverted â€” Eq. 3.20 (p. 3/34)."""
    return 0.125 * pbar * (math.sqrt(max(81 - 80*q/qmax, 0.0)) - 1)


def qmax_from_j(j_star: float, pbar: float) -> float:
    """Vogel qmax from J* â€” Eq. 3.21 (p. 3/34)."""
    return j_star * pbar / 1.8


def fetkovich_rate(qmax: float, pwf: float, pbar: float, n: float) -> float:
    """Fetkovich IPR â€” Eq. 3.22 (p. 3/34)."""
    return qmax * (1 - (pwf/pbar)**2)**n


def generalized_vogel(j_star, pbar, pb, pwf) -> float:
    """Generalized Vogel â€” Eq. 3.28 (p. 3/35). [stb/d]"""
    if pwf >= pb:
        return j_star * (pbar - pwf)
    qb = j_star * (pbar - pb)
    qv = j_star * pb / 1.8
    r = pwf / pb
    return qb + qv * (1 - 0.2*r - 0.8*r*r)


def composite_ipr_single_phase(layer_data: list[dict]) -> float:
    """Composite single-phase AOF â€” Eq. 3.40 (p. 3/38).

    Each layer: {"J_star": stb/d/psi, "p_bar": psia}.
    """
    return sum(L["J_star"] * L["p_bar"] for L in layer_data)


def composite_ipr_two_phase(layer_data: list[dict]) -> float:
    """Composite two-phase AOF â€” Eq. 3.43 (p. 3/38)."""
    return sum(L["J_star"] * L["p_bar"] / 1.8 for L in layer_data)


def future_j_vogel(j_present, kro_f, mu_f, bo_f, kro_p, mu_p, bo_p):
    """Future J* by Vogel â€” Eq. 3.50 (p. 3/41)."""
    return j_present * (kro_f/(bo_f*mu_f)) / (kro_p/(bo_p*mu_p))


def joski_horizontal_ipr(kH, kV, h, bo, mu, L_ft, reH_ft, rw_ft,
                         pe, pwf, skin=0.0):
    """Joshi horizontal-well IPR â€” Eq. 3.11 (p. 3/32). [stb/d]"""
    Iani = math.sqrt(kH / kV)
    a = (L_ft/2.0) * math.sqrt(
        0.5 + math.sqrt(0.25 + (reH_ft/(L_ft/2.0))**4))
    L2 = L_ft/2.0
    l1 = math.log((a + math.sqrt(a*a - L2*L2)) / L2)
    l2 = (Iani*h/L_ft) * math.log(Iani*h / (rw_ft*(Iani*h + 1.0)))
    return kH*h*(pe - pwf) / (141.2*bo*mu*(l1 + l2 + skin))