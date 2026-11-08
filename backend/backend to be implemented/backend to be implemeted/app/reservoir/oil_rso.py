"""Oil solution gas-oil ratio, Standing/Beggs correlation.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 1, Sec. 6.1, pp. 32-34, Eq. (1.26) and Example 1.7 (p. 42).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Eq. (1.26), p. 32: denominators and exponents
STANDING_DENOM = 18.0       # psia
STANDING_EXP = 1.204        # dimensionless
YG_T_COEFF = 0.00091        # 1/degF
YG_API_COEFF = 0.0125       # 1/degAPI

# Book validity ranges (p. 34)
P_MIN_PSIA = 130.0
P_MAX_PSIA = 7000.0
T_MIN_F = 100.0
T_MAX_F = 258.0
GAS_SG_MIN = 0.59
GAS_SG_MAX = 0.95
API_MIN = 16.5
API_MAX = 63.8

MIN_T_F = -459.67
API_PHYS_LO = -10.0
API_PHYS_HI = 100.0


@dataclass(frozen=True)
class RsoResult:
    rso_scf_stb: float
    y_g: float
    clamped: bool
    in_validity_range: bool


def _standing_at_p(
    p_psia: float, y_g: float, gas_sg: float,
) -> float:
    """Evaluate Eq. (1.26) at a single pressure."""
    return gas_sg * math.pow(p_psia / (STANDING_DENOM * math.pow(10.0, y_g)),
                             STANDING_EXP)


def oil_rso(
    p_psia: float,
    T_F: float,
    gas_sg: float,
    oil_api: float,
    pb_psia: float,
) -> RsoResult:
    """Return solution gas-oil ratio Rso in SCF/STB, Eq. (1.26).

    Implements Standing's correlation as presented by Beggs (Craft, Hawkins,
    Terry 1991, Ch. 1, Sec. 6.1, pp. 32-34). Above the bubble point the
    engine returns Rso at pb (book p. 33; Example 1.7 p. 42).

    Args:
        p_psia: Pressure in psia. Must be > 0.
        T_F: Reservoir temperature in deg F. Must be above absolute zero.
        gas_sg: Gas specific gravity (air=1). Must be in (0, 2).
        oil_api: Stock-tank oil gravity in deg API. Physical range
            (-10, 100); correlation-valid range 16.5-63.8.
        pb_psia: Bubble-point pressure in psia. Must be > 0.

    Returns:
        RsoResult(rso_scf_stb, y_g, clamped, in_validity_range).

    Raises:
        ValueError: any input out of physical range.
    """
    if not (p_psia > 0.0):
        raise ValueError(f"p_psia must be > 0, got {p_psia!r}")
    if not (pb_psia > 0.0):
        raise ValueError(f"pb_psia must be > 0, got {pb_psia!r}")
    if not (T_F > MIN_T_F):
        raise ValueError(f"T_F must be above {MIN_T_F} deg F, got {T_F!r}")
    if not (0.0 < gas_sg < 2.0):
        raise ValueError(f"gas_sg must be in (0, 2), got {gas_sg!r}")
    if not (API_PHYS_LO < oil_api < API_PHYS_HI):
        raise ValueError(
            f"oil_api must be in ({API_PHYS_LO}, {API_PHYS_HI}), got {oil_api!r}"
        )

    # Yg term (Standing)
    y_g = YG_T_COEFF * T_F - YG_API_COEFF * oil_api

    # Eq. (1.26) at p or at pb
    if p_psia <= pb_psia:
        rso = _standing_at_p(p_psia, y_g, gas_sg)
        clamped = False
    else:
        rso = _standing_at_p(pb_psia, y_g, gas_sg)
        clamped = True

    # Book validity: check pb (or p if pb not limiting), T, gas_sg, API.
    pb_used = pb_psia
    in_range = (
        P_MIN_PSIA <= pb_used <= P_MAX_PSIA
        and T_MIN_F <= T_F <= T_MAX_F
        and GAS_SG_MIN <= gas_sg <= GAS_SG_MAX
        and API_MIN <= oil_api <= API_MAX
    )
    return RsoResult(
        rso_scf_stb=rso, y_g=y_g, clamped=clamped, in_validity_range=in_range,
    )
