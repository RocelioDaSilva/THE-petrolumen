"""Oil viscosity, Egbogah / Beggs-Robinson / Vasquez-Beggs.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 1, Sec. 6.4, pp. 40-44, Eqs. (1.34)-(1.36),
Example 1.7 (pp. 42-44).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

# Eq. (1.34), p. 41: Egbogah dead-oil coefficients
EGB_C0 = 1.8653
EGB_C_API = -0.025086          # 1/degAPI
EGB_C_LOG_T = -0.5644          # dimensionless

# Eq. (1.35), p. 41: Beggs-Robinson live-oil coefficients
BR_A_PREFAC = 10.715           # cp
BR_A_OFFSET = 100.0            # SCF/STB
BR_A_EXP = -0.515              # dimensionless
BR_B_PREFAC = 5.44             # dimensionless
BR_B_OFFSET = 150.0            # SCF/STB
BR_B_EXP = -0.338              # dimensionless

# Eq. (1.36), p. 41: Vasquez-Beggs above-bubble coefficients
VB_M_PREFAC = 2.6
VB_M_PEXP = 1.187
VB_M_E0 = -11.513
VB_M_E1 = -8.98e-5             # 1/psia

# Validity ranges (book pp. 41-42)
EGB_T_MIN_F = 59.0
EGB_T_MAX_F = 176.0
EGB_API_MIN = 5.0
EGB_API_MAX = 58.0

BR_P_MIN_PSIG = 0.0
BR_P_MAX_PSIG = 5250.0
BR_T_MIN_F = 70.0
BR_T_MAX_F = 295.0
BR_RS_MIN = 20.0
BR_RS_MAX = 2070.0
BR_API_MIN = 16.0
BR_API_MAX = 58.0

VB_P_MIN_PSIG = 126.0
VB_P_MAX_PSIG = 9500.0
VB_RS_MIN = 9.3
VB_RS_MAX = 2199.0
VB_API_MIN = 15.3
VB_API_MAX = 59.5
VB_SG_MIN = 0.511
VB_SG_MAX = 1.351
VB_MU_MIN = 0.117
VB_MU_MAX = 148.0

MIN_T_F = -459.67
API_PHYS_LO = -10.0
API_PHYS_HI = 100.0

Formulation = Literal["beggs_robinson", "vasquez_beggs"]


@dataclass(frozen=True)
class OilViscosityResult:
    mu_cp: float
    mu_od_cp: float
    mu_ob_cp: float
    A: float
    B: float
    m: float | None
    formulation: Formulation
    in_validity_range: bool


def _dead_oil_visc(api: float, T_F: float) -> float:
    """Egbogah dead-oil viscosity (Eq. 1.34). Requires T_F > 0."""
    log_log = (
        EGB_C0 + EGB_C_API * api + EGB_C_LOG_T * math.log10(T_F)
    )
    # log10(mu_od + 1) = 10^(...)
    return math.pow(10.0, math.pow(10.0, log_log)) - 1.0


def _live_oil_visc(mu_od: float, rso: float) -> tuple[float, float, float]:
    """Beggs-Robinson live-oil viscosity (Eq. 1.35)."""
    A = BR_A_PREFAC * math.pow(rso + BR_A_OFFSET, BR_A_EXP)
    B = BR_B_PREFAC * math.pow(rso + BR_B_OFFSET, BR_B_EXP)
    # mu_ob = A * mu_od^B via exp(B*ln(mu_od)) for stability when B<0.
    mu_ob = A * math.exp(B * math.log(mu_od))
    return mu_ob, A, B


def _vb_exponent(p_psia: float) -> float:
    """Vasquez-Beggs m exponent (Eq. 1.36)."""
    return (
        VB_M_PREFAC
        * math.pow(p_psia, VB_M_PEXP)
        * math.exp(VB_M_E0 + VB_M_E1 * p_psia)
    )


def oil_viscosity(
    p_psia: float,
    T_F: float,
    gas_sg: float,
    oil_api: float,
    pb_psia: float,
) -> OilViscosityResult:
    """Return oil viscosity mu_o in cp.

    Chains Egbogah (Eq. 1.34), Beggs-Robinson (Eq. 1.35), and
    Vasquez-Beggs (Eq. 1.36) from Craft, Hawkins, Terry (1991),
    Ch. 1, Sec. 6.4, pp. 40-44. Rso is taken from Feature 4 at the
    appropriate pressure.

    Args:
        p_psia: Pressure in psia. Must be > 0.
        T_F: Reservoir temperature in deg F. Must be > 0 for log10(T)
            in Eq. 1.34 (physically, must be > -459.67 but the
            correlation form requires > 0).
        gas_sg: Gas specific gravity (air=1). Must be in (0, 2).
        oil_api: Stock-tank oil gravity in deg API. Physical range
            (-10, 100).
        pb_psia: Bubble-point pressure in psia. Must be > 0.

    Returns:
        OilViscosityResult.

    Raises:
        ValueError: any input out of physical range, T <= 0 deg F
            (log10 domain of Eq. 1.34), or mu_od <= 0.
    """
    if not (p_psia > 0.0):
        raise ValueError(f"p_psia must be > 0, got {p_psia!r}")
    if not (pb_psia > 0.0):
        raise ValueError(f"pb_psia must be > 0, got {pb_psia!r}")
    if not (T_F > MIN_T_F):
        raise ValueError(f"T_F must be above {MIN_T_F} deg F, got {T_F!r}")
    if not (T_F > 0.0):
        raise ValueError(
            f"T_F must be > 0 deg F for log10(T) in Eq. 1.34, got {T_F!r}"
        )
    if not (0.0 < gas_sg < 2.0):
        raise ValueError(f"gas_sg must be in (0, 2), got {gas_sg!r}")
    if not (API_PHYS_LO < oil_api < API_PHYS_HI):
        raise ValueError(
            f"oil_api must be in ({API_PHYS_LO}, {API_PHYS_HI}), "
            f"got {oil_api!r}"
        )

    from app.reservoir.oil_rso import oil_rso

    mu_od = _dead_oil_visc(oil_api, T_F)
    if not (mu_od > 0.0):
        raise ValueError(
            f"Egbogah Eq. 1.34 produced mu_od = {mu_od!r} <= 0; "
            "check T_F, oil_api."
        )

    if p_psia <= pb_psia:
        rso_ref = oil_rso(
            p_psia=p_psia, T_F=T_F, gas_sg=gas_sg,
            oil_api=oil_api, pb_psia=pb_psia,
        ).rso_scf_stb
        mu, A, B = _live_oil_visc(mu_od, rso_ref)
        formulation: Formulation = "beggs_robinson"
        m: float | None = None
        mu_ob = mu
    else:
        rsob = oil_rso(
            p_psia=pb_psia, T_F=T_F, gas_sg=gas_sg,
            oil_api=oil_api, pb_psia=pb_psia,
        ).rso_scf_stb
        mu_ob, A, B = _live_oil_visc(mu_od, rsob)
        m = _vb_exponent(p_psia)
        mu = mu_ob * math.pow(p_psia / pb_psia, m)
        formulation = "vasquez_beggs"

    # Validity checks
    if formulation == "beggs_robinson":
        in_range = (
            BR_P_MIN_PSIG <= p_psia <= BR_P_MAX_PSIG
            and BR_T_MIN_F <= T_F <= BR_T_MAX_F
            and BR_API_MIN <= oil_api <= BR_API_MAX
        )
    else:
        in_range = (
            VB_P_MIN_PSIG <= p_psia <= VB_P_MAX_PSIG
            and VB_API_MIN <= oil_api <= VB_API_MAX
            and VB_SG_MIN <= gas_sg <= VB_SG_MAX
            and VB_MU_MIN <= mu <= VB_MU_MAX
        )
    return OilViscosityResult(
        mu_cp=mu, mu_od_cp=mu_od, mu_ob_cp=mu_ob,
        A=A, B=B, m=m, formulation=formulation,
        in_validity_range=in_range,
    )
