"""Guthrie-Greenberger water-drive recovery factor correlation.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 5, Sec. 2, p. 152, Eq. (5.5).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class GuthrieGreenbergerResult:
    RF: float
    term_k: float
    term_Swi: float
    term_mu: float
    term_phi: float
    term_h: float
    out_of_physical_range: bool


def guthrie_greenberger_rf(
    k_md: float, Swi: float, mu_o_cp: float, phi: float, h_ft: float,
) -> GuthrieGreenbergerResult:
    """Water-drive recovery factor (Craft Eq. 5.5, p. 152).

    Args:
        k_md: Permeability, md (> 0).
        Swi: Connate water saturation, fraction [0, 1).
        mu_o_cp: Oil viscosity, cp (> 0).
        phi: Porosity, fraction (0, 1).
        h_ft: Net pay thickness, ft (> 0).

    Returns:
        GuthrieGreenbergerResult.

    Raises:
        ValueError: any input out of physical range.
    """
    if not (k_md > 0.0):
        raise ValueError(f"k_md must be > 0, got {k_md!r}")
    if not (0.0 <= Swi < 1.0):
        raise ValueError(f"Swi must be in [0, 1), got {Swi!r}")
    if not (mu_o_cp > 0.0):
        raise ValueError(f"mu_o_cp must be > 0, got {mu_o_cp!r}")
    if not (0.0 < phi < 1.0):
        raise ValueError(f"phi must be in (0, 1), got {phi!r}")
    if not (h_ft > 0.0):
        raise ValueError(f"h_ft must be > 0, got {h_ft!r}")

    t_k = 0.272 * math.log10(k_md)
    t_swi = 0.256 * Swi
    t_mu = -0.136 * math.log10(mu_o_cp)
    t_phi = -1.538 * phi
    t_h = -0.00035 * h_ft
    rf = 0.114 + t_k + t_swi + t_mu + t_phi + t_h
    return GuthrieGreenbergerResult(
        RF=rf, term_k=t_k, term_Swi=t_swi, term_mu=t_mu,
        term_phi=t_phi, term_h=t_h,
        out_of_physical_range=not (0.0 <= rf <= 1.0),
    )
