"""Capillary-number EOR screening.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 9, Sec. 5.1, pp. 380-381, Eq. (9.58) and Fig. 9.19.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

# Eq. (9.58), p. 381: conversion constant for md, psi, ft, dyn/cm
# derivation: k_o [md] -> [darcy] = /1000; the units of (darcy*psi/ft)
# and dyn/cm differ by a factor that has been absorbed into C = 1e-3
# for the field-unit gradient form. See the write-up for details.
CONV_C = 1.0e-3

# Fig. 9.19 logistic fit (visual calibration)
NW0 = 1.0e-4       # transition center
NW_EXP = 3.0       # logistic steepness

# Thresholds from Fig. 9.19
NW_LOW = 1.0e-5
NW_HIGH = 1.0e-2

Category = Literal["below_threshold", "transition", "aggressive_EOR"]


@dataclass(frozen=True)
class CapillaryNumberResult:
    N_w: float
    gradient_psi_ft: float
    sor_reduction_fraction: float
    sor_after: float | None
    category: Category


def capillary_number(
    k_o_md: float,
    delta_p_psi: float,
    L_ft: float,
    phi: float,
    sigma_ow_dyn_cm: float,
    Sor_before: float | None = None,
) -> CapillaryNumberResult:
    """Capillary number and residual-oil reduction (Eq. 9.58, Fig. 9.19).

    Implements Eq. (9.58) from Craft, Hawkins, Terry (1991), Ch. 9,
    Sec. 5.1, pp. 380-381, and the visual Fig. 9.19 correlation for
    residual-oil reduction as a function of N_w.

    Args:
        k_o_md: Effective permeability to oil, md (> 0).
        delta_p_psi: Pressure drop across length L, psi (> 0).
        L_ft: Length over which dp acts, ft (> 0).
        phi: Porosity, fraction (0, 1).
        sigma_ow_dyn_cm: Oil-water interfacial tension, dyn/cm (> 0).
        Sor_before: Optional residual oil saturation before EOR
            (fraction, 0 <= Sor_before < 1). If supplied, Sor_after
            is returned.

    Returns:
        CapillaryNumberResult.

    Raises:
        ValueError: any input out of range.
    """
    if not (k_o_md > 0.0):
        raise ValueError(f"k_o_md must be > 0, got {k_o_md!r}")
    if not (delta_p_psi > 0.0):
        raise ValueError(f"delta_p_psi must be > 0, got {delta_p_psi!r}")
    if not (L_ft > 0.0):
        raise ValueError(f"L_ft must be > 0, got {L_ft!r}")
    if not (0.0 < phi < 1.0):
        raise ValueError(f"phi must be in (0, 1), got {phi!r}")
    if not (sigma_ow_dyn_cm > 0.0):
        raise ValueError(
            f"sigma_ow_dyn_cm must be > 0, got {sigma_ow_dyn_cm!r}"
        )
    if Sor_before is not None and not (0.0 <= Sor_before < 1.0):
        raise ValueError(
            f"Sor_before must be in [0, 1), got {Sor_before!r}"
        )

    gradient = delta_p_psi / L_ft
    N_w = (
        CONV_C * k_o_md * delta_p_psi
        / (phi * sigma_ow_dyn_cm * L_ft)
    )
    if not (N_w > 0.0):
        raise ValueError(
            f"computed N_w = {N_w!r} <= 0; check inputs."
        )

    # Logistic reduction: (Sor_after/Sor_before) = 1 / (1 + (Nw/Nw0)^p)
    reduction = 1.0 / (1.0 + math.pow(N_w / NW0, NW_EXP))

    if N_w < NW_LOW:
        category: Category = "below_threshold"
    elif N_w <= NW_HIGH:
        category = "transition"
    else:
        category = "aggressive_EOR"

    sor_after = reduction * Sor_before if Sor_before is not None else None

    return CapillaryNumberResult(
        N_w=N_w,
        gradient_psi_ft=gradient,
        sor_reduction_fraction=reduction,
        sor_after=sor_after,
        category=category,
    )
