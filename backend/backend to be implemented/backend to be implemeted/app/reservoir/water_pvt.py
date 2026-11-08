"""Water PVT properties (McCain, Osif).

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 1, Sec. 7.1-7.4, pp. 45-48, Eqs. (1.37)-(1.43).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Eq. (1.37), p. 45: Bw coefficients
BW_T_C0 = -1.00010e-2
BW_T_C1 = 1.33391e-4
BW_T_C2 = 5.50654e-7
BW_P_C0_T = -1.95301e-9      # p*T coefficient
BW_P_C0_P2_T = -1.72834e-13  # p^2*T coefficient
BW_P_C1 = -3.58922e-7        # p coefficient
BW_P_C2 = -2.25341e-10       # p^2 coefficient

# Eq. (1.38), p. 45: Rsw ratio coefficients
RSW_C1 = -0.0840655
RSW_T_EXP = -0.285854

# Eq. (1.40), p. 46: cw coefficients
CW_P = 7.033
CW_SALT = 541.5
CW_T = -537.0
CW_CONST = 403300.0

# Eq. (1.43), p. 48: mu_w pressure correction
MUW_P_C0 = 0.9994
MUW_P_C1 = 4.0295e-5
MUW_P_C2 = 3.1062e-9

# Salinity conversion: pct -> g/L (approximate pure-NaCl equivalent)
PCT_TO_GPL = 10.0

MIN_T_F = -459.67
T_POS_MIN_F = 0.0


@dataclass(frozen=True)
class WaterPVTResult:
    bw_bbl_stb: float
    rswp_scf_stb: float
    rsw_scf_stb: float
    cw_psi_inv: float
    mu_w_cp: float
    bw_in_validity: bool
    rsw_in_validity: bool
    cw_in_validity: bool
    mu_w_in_validity: bool


def _bw(p_psia: float, T_F: float) -> float:
    """Formation volume factor Bw (Eq. 1.37)."""
    dVwT = BW_T_C0 + BW_T_C1 * T_F + BW_T_C2 * T_F * T_F
    dVwp = (
        BW_P_C0_T * p_psia * T_F
        + BW_P_C0_P2_T * p_psia * p_psia * T_F
        + BW_P_C1 * p_psia
        + BW_P_C2 * p_psia * p_psia
    )
    return (1.0 + dVwT) * (1.0 + dVwp)


def _rswp(p_psia: float, T_F: float) -> float:
    """Pure-water solution GWR Rswp (Eq. 1.39)."""
    A = (
        8.15839
        - 6.12265e-2 * T_F
        + 1.91663e-4 * T_F * T_F
        - 2.1654e-7 * T_F * T_F * T_F
    )
    B = (
        1.01021e-2
        - 7.44241e-5 * T_F
        + 3.05553e-7 * T_F * T_F
        - 2.94883e-10 * T_F * T_F * T_F
    )
    C = -1.0e-7 * (
        9.02505
        - 0.130237 * T_F
        + 8.53425e-4 * T_F * T_F
        - 2.34122e-6 * T_F * T_F * T_F
        + 2.37049e-9 * T_F * T_F * T_F * T_F
    )
    return A + B * p_psia + C * p_psia * p_psia


def _rsw_ratio(salinity_pct: float, T_F: float) -> float:
    """Salinity correction to Rsw (Eq. 1.38)."""
    return math.pow(10.0, RSW_C1 * salinity_pct * math.pow(T_F, RSW_T_EXP))


def _cw(p_psia: float, T_F: float, c_nacl: float) -> float:
    """Water isothermal compressibility, Eq. (1.40)."""
    denom = CW_P * p_psia + CW_SALT * c_nacl + CW_T * T_F + CW_CONST
    if denom <= 0.0:
        raise ValueError(
            f"Eq. (1.40) denominator = {denom:.3f} <= 0; inputs give "
            "non-physical (negative or infinite) cw."
        )
    return 1.0 / denom


def _mu_w(p_psia: float, T_F: float, salinity_pct: float) -> float:
    """Water viscosity mu_w (Eqs. 1.42-1.43)."""
    S = salinity_pct
    A = 109.574 - 8.40564 * S + 0.313314 * S * S + 8.72213e-3 * S * S * S
    B = (
        -1.12166
        + 2.63951e-2 * S
        - 6.79461e-4 * S * S
        - 5.47119e-5 * S * S * S
        + 1.55586e-6 * S * S * S * S
    )
    mu_w1 = A * math.pow(T_F, B)
    ratio = MUW_P_C0 + MUW_P_C1 * p_psia + MUW_P_C2 * p_psia * p_psia
    return mu_w1 * ratio


def water_pvt(
    p_psia: float,
    T_F: float,
    salinity_pct: float,
    c_nacl_g_l: float | None = None,
) -> WaterPVTResult:
    """Return Bw, Rsw, cw, mu_w for formation water.

    Implements Eqs. (1.37)-(1.40), (1.42)-(1.43) from Craft, Hawkins,
    Terry (1991), Ch. 1, Sec. 7.1-7.4, pp. 45-48. Eq. (1.41)
    (below-bubble cw correction) is not implemented because the book
    itself notes it is unverified (p. 46); caller should apply the
    above-bubble cw with that caveat (see Limitations).

    Args:
        p_psia: Pressure in psia. Must be > 0.
        T_F: Temperature in deg F. Must be > 0.
        salinity_pct: Salinity, % by weight solids, in (0, 40).
        c_nacl_g_l: Optional NaCl concentration, g/L, in [0, 200]. If
            None, derived as 10*salinity_pct (approximately pure-NaCl
            equivalent).

    Returns:
        WaterPVTResult with Bw, Rswp, Rsw, cw, mu_w and per-quantity
        validity flags.

    Raises:
        ValueError: any input out of physical range; cw denominator
            <= 0; Rswp < 0.
    """
    if not (p_psia > 0.0):
        raise ValueError(f"p_psia must be > 0, got {p_psia!r}")
    if not (T_F > T_POS_MIN_F):
        raise ValueError(
            f"T_F must be > {T_POS_MIN_F} deg F for T^-0.285854 and "
            f"T^B in Eqs. 1.38, 1.42, got {T_F!r}"
        )
    if not (0.0 < salinity_pct < 40.0):
        raise ValueError(
            f"salinity_pct must be in (0, 40), got {salinity_pct!r}"
        )
    if c_nacl_g_l is None:
        c_nacl = PCT_TO_GPL * salinity_pct
    else:
        if not (0.0 <= c_nacl_g_l <= 200.0):
            raise ValueError(
                f"c_nacl_g_l must be in [0, 200], got {c_nacl_g_l!r}"
            )
        c_nacl = float(c_nacl_g_l)

    bw = _bw(p_psia, T_F)
    rswp = _rswp(p_psia, T_F)
    if rswp < 0.0:
        raise ValueError(
            f"Eq. (1.39) produced negative Rswp = {rswp:.3f}; inputs "
            "outside the McCain validity range."
        )
    ratio = _rsw_ratio(salinity_pct, T_F)
    rsw = rswp * ratio
    cw = _cw(p_psia, T_F, c_nacl)
    mu = _mu_w(p_psia, T_F, salinity_pct)

    bw_in = True  # McCain gives 2% accuracy over typical ranges
    rsw_in = (
        1000.0 <= p_psia <= 10000.0
        and 100.0 <= T_F <= 340.0
        and 0.0 < salinity_pct < 30.0
    )
    cw_in = (
        1000.0 <= p_psia <= 20000.0
        and 0.0 <= c_nacl <= 200.0
        and 200.0 <= T_F <= 270.0
    )
    mu_in = 86.0 <= T_F <= 167.0
    return WaterPVTResult(
        bw_bbl_stb=bw, rswp_scf_stb=rswp, rsw_scf_stb=rsw,
        cw_psi_inv=cw, mu_w_cp=mu,
        bw_in_validity=bw_in, rsw_in_validity=rsw_in,
        cw_in_validity=cw_in, mu_w_in_validity=mu_in,
    )
