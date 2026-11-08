"""Oil isothermal compressibility, Villena-Lanzi / Vasquez-Beggs.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 1, Sec. 6.3, pp. 38-40, Eqs. (1.32) and (1.33),
Example 1.7 (pp. 42-43).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

# Eq. (1.32), p. 39: Villena-Lanzi (below bubble point)
VL_C0 = -0.664
VL_C_P = -1.430
VL_C_PB = -0.395
VL_C_T = 0.390
VL_C_RS = 0.455
VL_C_API = 0.262

# Eq. (1.33), p. 39: Vasquez-Beggs (above bubble point)
VB_C_RS = 5.0
VB_C_T = 17.2
VB_C_SG = -1180.0
VB_C_API = 12.61
VB_C_CONST = -1433.0
VB_P_DENOM = 1.0e5            # psi^-1 numerator scale

# Validity ranges (book p. 39)
VL_P_MIN_PSIG = 500.0
VL_P_MAX_PSIG = 5300.0
VL_PB_MIN_PSIG = 763.0
VL_PB_MAX_PSIG = 5300.0
VL_T_MIN_F = 78.0
VL_T_MAX_F = 330.0
VL_RS_MIN = 1.5
VL_RS_MAX = 1947.0
VL_API_MIN = 6.0
VL_API_MAX = 52.0
VL_SG_MIN = 0.58
VL_SG_MAX = 1.20

VB_P_MIN_PSIG = 126.0
VB_P_MAX_PSIG = 9500.0
VB_RS_MIN = 9.3
VB_RS_MAX = 2199.0
VB_API_MIN = 15.3
VB_API_MAX = 59.5
VB_SG_MIN = 0.511
VB_SG_MAX = 1.351

MIN_T_F = -459.67
API_PHYS_LO = -10.0
API_PHYS_HI = 100.0

Formulation = Literal["villena_lanzi", "vasquez_beggs"]


@dataclass(frozen=True)
class OilCompressibilityResult:
    co_psi_inv: float
    formulation: Formulation
    rsob_scf_stb: float
    in_validity_range: bool


def _villena_lanzi(
    p_psia: float, pb_psia: float, T_F: float,
    rsob: float, oil_api: float,
) -> float:
    """Evaluate Eq. (1.32). Assumes all inputs > 0 except where API check
    has already been done; ln() requires strict positivity."""
    ln_co = (
        VL_C0
        + VL_C_P * math.log(p_psia)
        + VL_C_PB * math.log(pb_psia)
        + VL_C_T * math.log(T_F + 459.67)  # see note in docstring
        + VL_C_RS * math.log(rsob)
        + VL_C_API * math.log(oil_api)
    )
    return math.exp(ln_co)


def _vasquez_beggs(
    p_psia: float, T_F: float, gas_sg: float,
    oil_api: float, rsob: float,
) -> float:
    """Evaluate Eq. (1.33)."""
    num = (
        VB_C_RS * rsob
        + VB_C_T * T_F
        + VB_C_SG * gas_sg
        + VB_C_API * oil_api
        + VB_C_CONST
    )
    if num <= 0.0:
        raise ValueError(
            f"Vasquez-Beggs numerator = {num:.3f} <= 0; "
            "inputs lead to non-physical co. Verify T, gas_sg, oil_api, "
            "and Rsob."
        )
    return num / (p_psia * VB_P_DENOM)


def oil_compressibility(
    p_psia: float,
    T_F: float,
    gas_sg: float,
    oil_api: float,
    pb_psia: float,
) -> OilCompressibilityResult:
    """Return oil isothermal compressibility co in psi^-1.

    Implements Villena-Lanzi (Eq. 1.32) below bubble point and
    Vasquez-Beggs (Eq. 1.33) above bubble point from Craft, Hawkins,
    Terry (1991), Ch. 1, Sec. 6.3, pp. 38-40.

    Note on temperature units: the book's formula uses T in deg F for
    both correlations. For the Villena-Lanzi ln() to be well-defined
    we evaluate ln(T + 459.67) to keep the argument strictly positive
    for any physically meaningful T; the book's numerical example
    (p. 42) uses T in deg F directly. Because ln(T+459.67) != ln(T_F)
    for T_F as used in the book example, we use T_R (deg R) in the
    ln() call -- but the book's example (T=180) resolves to
    ln(639.67). If the caller expects the book's exact form, see
    \S14 Limitations (ambiguous unit convention in Eq. 1.32).

    Args:
        p_psia: Pressure in psia. Must be > 0.
        T_F: Temperature in deg F. Must be above absolute zero.
        gas_sg: Gas specific gravity (air=1). Must be in (0, 2).
        oil_api: Stock-tank oil gravity in deg API. Physical range
            (-10, 100).
        pb_psia: Bubble-point pressure in psia. Must be > 0.

    Returns:
        OilCompressibilityResult(co_psi_inv, formulation,
        rsob_scf_stb, in_validity_range).

    Raises:
        ValueError: any input out of physical range, or V-B numerator
            non-positive.
    """
    # Validations
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
            f"oil_api must be in ({API_PHYS_LO}, {API_PHYS_HI}), "
            f"got {oil_api!r}"
        )

    # Lazy import Feature 4 (oil_rso)
    from app.reservoir.oil_rso import oil_rso

    rsob = oil_rso(
        p_psia=pb_psia, T_F=T_F, gas_sg=gas_sg,
        oil_api=oil_api, pb_psia=pb_psia,
    ).rso_scf_stb

    if p_psia <= pb_psia:
        # Eq. (1.32). NB: ln(oil_api) requires oil_api > 0. Physical
        # range is (-10, 100); values in (-10, 0] would break ln().
        # Guard below.
        if oil_api <= 0.0:
            raise ValueError(
                f"Villena-Lanzi ln(API) requires oil_api > 0, got {oil_api!r}"
            )
        co = _villena_lanzi(p_psia, pb_psia, T_F, rsob, oil_api)
        formulation: Formulation = "villena_lanzi"
    else:
        co = _vasquez_beggs(p_psia, T_F, gas_sg, oil_api, rsob)
        formulation = "vasquez_beggs"

    # Validity: use psig-as-psia approximation (book p. 39 gives psig;
    # atmospheric contribution is negligible at the pressures used).
    if formulation == "villena_lanzi":
        in_range = (
            VL_P_MIN_PSIG <= p_psia <= VL_P_MAX_PSIG
            and VL_PB_MIN_PSIG <= pb_psia <= VL_PB_MAX_PSIG
            and VL_T_MIN_F <= T_F <= VL_T_MAX_F
            and VL_RS_MIN <= rsob <= VL_RS_MAX
            and VL_API_MIN <= oil_api <= VL_API_MAX
            and VL_SG_MIN <= gas_sg <= VL_SG_MAX
        )
    else:
        in_range = (
            VB_P_MIN_PSIG <= p_psia <= VB_P_MAX_PSIG
            and VB_RS_MIN <= rsob <= VB_RS_MAX
            and VB_API_MIN <= oil_api <= VB_API_MAX
            and VB_SG_MIN <= gas_sg <= VB_SG_MAX
        )
    return OilCompressibilityResult(
        co_psi_inv=co, formulation=formulation,
        rsob_scf_stb=rsob, in_validity_range=in_range,
    )
