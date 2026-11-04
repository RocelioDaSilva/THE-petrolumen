"""Chapter 9 â€” Well Tubing (pp. 9/109 â€“ 9/115)."""
from __future__ import annotations
import math


def collapse_biaxial(p_c: float, sa: float, ym: float) -> float:
    """Axial-load-corrected collapse â€” Eq. 9.19 (p. 9/112).

    p_c: uncorrected collapse resistance (Appendix B).
    sa:  axial stress = W/A.
    ym:  minimum yield stress (Table 9.1).
    """
    r = sa / ym
    return p_c * (math.sqrt(1 - 0.75*r**2) - 0.5*r)


def landing_tension(ae: float, delta_L: float, L: float,
                    E: float = 30e6) -> float:
    """Thermal landing tension â€” Eq. 9.22 (p. 9/112). [lbf]"""
    return ae * E * delta_L / L


def bending_stress(E: float, Do: float, Rc: float) -> float:
    """Bending stress â€” Eq. 9.20 (p. 9/112). [psi]"""
    return E * Do / (2*Rc)