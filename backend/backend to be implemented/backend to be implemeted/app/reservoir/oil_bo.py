"""Oil formation volume factor, Standing/Beggs correlation.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 1, Sec. 6.2, pp. 34-37, Eqs. (1.29) and (1.30),
and Example 1.7 (pp. 42-43).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Eq. (1.29), p. 36: coefficients
BO_INTERCEPT = 0.972        # bbl/STB
BO_COEFF = 0.000147         # bbl/STB
BO_EXP = 1.175              # dimensionless
F_T_COEFF = 1.25            # 1/degF
F_GAMMA_EXP = 0.5           # dimensionless

# Standing gamma_o from API (book p. 36)
API_NUM = 141.5
API_DEN_OFFSET = 131.5

# Book validity ranges (p. 36)
P_MIN_PSIA = 130.0
P_MAX_PSIA = 7000.0
T_MIN_F = 100.0
T_MAX_F = 258.0
API_MIN = 16.5
API_MAX = 63.8
GAS_SG_MIN = 0.59
GAS_SG_MAX = 0.95
BO_VALID_MIN = 1.024
BO_VALID_MAX = 2.05

MIN_T_F = -459.67
API_PHYS_LO = -10.0
API_PHYS_HI = 100.0


@dataclass(frozen=True)
class BoResult:
    bo_bbl_stb: float
    f_term: float
    gamma_o: float
    clamped: bool
    in_validity_range: bool
    co_used: float | None


def oil_api_to_sg(oil_api: float) -> float:
    """Convert stock-tank oil gravity (deg API) to specific gravity."""
    return API_NUM / (API_DEN_OFFSET + oil_api)


def _standing_bo(
    rso: float, gamma_o: float, gas_sg: float, T_F: float,
) -> tuple[float, float]:
    """Evaluate Eq. (1.29) at one Rso. Returns (Bo, F)."""
    F = rso * math.pow(gas_sg / gamma_o, F_GAMMA_EXP) + F_T_COEFF * T_F
    bo = BO_INTERCEPT + BO_COEFF * math.pow(F, BO_EXP)
    return bo, F


def oil_bo(
    p_psia: float,
    T_F: float,
    gas_sg: float,
    oil_api: float,
    pb_psia: float,
    co_psi_inv: float | None = None,
) -> BoResult:
    """Return oil formation volume factor Bo in bbl/STB.

    Implements Eq. (1.29) below bubble point and Eq. (1.30) above
    bubble point (Craft, Hawkins, Terry 1991, Ch. 1, Sec. 6.2,
    pp. 34-37). Rso is taken from Feature 4 at the appropriate pressure;
    co is taken from Feature 6 (or supplied) for p > pb.

    Args:
        p_psia: Pressure in psia. Must be > 0.
        T_F: Reservoir temperature in deg F. Must be above absolute zero.
        gas_sg: Gas specific gravity (air=1). Must be in (0, 2).
        oil_api: Stock-tank oil gravity in deg API, physical range
            (-10, 100); correlation-valid range 16.5-63.8.
        pb_psia: Bubble-point pressure in psia. Must be > 0.
        co_psi_inv: Optional oil compressibility psi^-1 (>0). If None and
            p > pb, computed from Feature 6 (Vasquez-Beggs, Eq. 1.33).

    Returns:
        BoResult(bo_bbl_stb, f_term, gamma_o, clamped, in_validity_range,
        co_used).

    Raises:
        ValueError: any input out of physical range.
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
    if co_psi_inv is not None and not (co_psi_inv > 0.0):
        raise ValueError(f"co_psi_inv must be > 0, got {co_psi_inv!r}")

    # Lazy imports to avoid module-load order issues.
    from app.reservoir.oil_rso import oil_rso
    from app.reservoir.oil_compressibility import oil_compressibility

    gamma_o = oil_api_to_sg(oil_api)

    if p_psia <= pb_psia:
        # Eq. (1.29) directly at p; Rso(p) from Feature 4.
        rso_p = oil_rso(
            p_psia=p_psia, T_F=T_F, gas_sg=gas_sg,
            oil_api=oil_api, pb_psia=pb_psia,
        ).rso_scf_stb
        bo, F = _standing_bo(rso_p, gamma_o, gas_sg, T_F)
        clamped = False
        co_used: float | None = None
    else:
        # Eq. (1.30) with Bob at pb and co from Feature 6.
        rsob = oil_rso(
            p_psia=pb_psia, T_F=T_F, gas_sg=gas_sg,
            oil_api=oil_api, pb_psia=pb_psia,
        ).rso_scf_stb
        bob, F = _standing_bo(rsob, gamma_o, gas_sg, T_F)
        if co_psi_inv is None:
            co_r = oil_compressibility(
                p_psia=p_psia, T_F=T_F, gas_sg=gas_sg,
                oil_api=oil_api, pb_psia=pb_psia,
            )
            co = co_r.co_psi_inv
        else:
            co = float(co_psi_inv)
        bo = bob * math.exp(co * (pb_psia - p_psia))
        clamped = True
        co_used = co

    in_range = (
        P_MIN_PSIA <= pb_psia <= P_MAX_PSIA
        and T_MIN_F <= T_F <= T_MAX_F
        and API_MIN <= oil_api <= API_MAX
        and GAS_SG_MIN <= gas_sg <= GAS_SG_MAX
        and BO_VALID_MIN <= bo <= BO_VALID_MAX
    )
    return BoResult(
        bo_bbl_stb=bo, f_term=F, gamma_o=gamma_o, clamped=clamped,
        in_validity_range=in_range, co_used=co_used,
    )
