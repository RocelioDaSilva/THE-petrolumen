"""Gas-condensate initial in place (rate basis).

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 4, Sec. 2, pp. 110-118, Eqs. (4.1)-(4.3), Example 4.1.
"""

from __future__ import annotations

from dataclasses import dataclass

# Eq. (4.1), p. 111: constants (book values, internally consistent)
GW_GAMMA_O_COEF = 4602.0
GW_DEN_GAMMA_O_COEF = 133316.0
GW_GAMMA_1_COEF = 1.0
GW_GAMMA_3_COEF = 1.0

# Eq. (4.2), p. 112
API_NUM = 141.5
API_DEN_OFFSET = 131.5

# Eq. (3.22), p. 92
MW_NUM = 5954.0
MW_API_OFFSET = 8.811

# Eq. (4.3), p. 113: molar-volume / mass constant
SCF_PER_LBMOL = 379.4
LB_PER_BBL_WATER = 350.5

# Unit basis (p. 111): cu ft/ac-ft
CUFT_PER_ACFT = 43560.0

# Real gas constant
R_PRIME = 10.73             # psia*cu ft/(lbmol*degR)
K_1000 = 1000.0             # M SCF conversion


@dataclass(frozen=True)
class GCInitialRateResult:
    gamma_o: float
    mw_o: float
    r1_sep_scf_stb: float
    r3_tank_scf_stb: float
    gamma_w: float
    f_s_gas_frac: float
    g_unit_mmscf_per_acft: float
    g_gas_unit_mmscf_per_acft: float
    n_oil_unit_stb_per_acft: float
    in_validity: bool


def gas_condensate_initial_place_rate(
    pi_psia: float,
    T_F: float,
    phi_frac: float,
    Swi_frac: float,
    oil_rate_stb_d: float,
    gas_sep_rate_scf_d: float,
    gas_sep_sg: float,
    gas_tank_rate_scf_d: float,
    gas_tank_sg: float,
    oil_api: float,
    z_at_pi: float,
) -> GCInitialRateResult:
    """Gas-condensate initial G and N per acre-foot (rate basis).

    Implements Eqs. (4.1)-(4.3) and the real-gas law as in Craft,
    Hawkins, Terry (1991), Ch. 4, Sec. 2, pp. 110-118, Example 4.1.

    Args:
        pi_psia: Initial pressure, psia (>0).
        T_F: Reservoir temperature, deg F (> -459.67).
        phi_frac: Porosity, fraction (0,1).
        Swi_frac: Connate water, fraction [0,1).
        oil_rate_stb_d: Stock-tank condensate rate, STB/day (>0).
        gas_sep_rate_scf_d: Separator gas rate, SCF/day (>0).
        gas_sep_sg: Separator gas specific gravity (air=1), (0,2).
        gas_tank_rate_scf_d: Stock-tank gas rate, SCF/day (>=0).
        gas_tank_sg: Stock-tank gas specific gravity (air=1), (0,2).
        oil_api: Stock-tank gravity, deg API (>8.811, <100).
        z_at_pi: Gas deviation factor at pi, T (>0).

    Returns:
        GCInitialRateResult.

    Raises:
        ValueError: any input out of physical range.
    """
    if not (pi_psia > 0.0):
        raise ValueError(f"pi_psia must be > 0, got {pi_psia!r}")
    if not (T_F > -459.67):
        raise ValueError(f"T_F must be > -459.67, got {T_F!r}")
    if not (0.0 < phi_frac < 1.0):
        raise ValueError(f"phi_frac must be in (0,1), got {phi_frac!r}")
    if not (0.0 <= Swi_frac < 1.0):
        raise ValueError(f"Swi_frac must be in [0,1), got {Swi_frac!r}")
    if not (oil_rate_stb_d > 0.0):
        raise ValueError(f"oil_rate_stb_d must be > 0, got {oil_rate_stb_d!r}")
    if not (gas_sep_rate_scf_d > 0.0):
        raise ValueError(
            f"gas_sep_rate_scf_d must be > 0, got {gas_sep_rate_scf_d!r}"
        )
    if not (gas_tank_rate_scf_d >= 0.0):
        raise ValueError(
            f"gas_tank_rate_scf_d must be >= 0, got {gas_tank_rate_scf_d!r}"
        )
    if not (0.0 < gas_sep_sg < 2.0):
        raise ValueError(f"gas_sep_sg must be in (0,2), got {gas_sep_sg!r}")
    if not (0.0 < gas_tank_sg < 2.0):
        raise ValueError(f"gas_tank_sg must be in (0,2), got {gas_tank_sg!r}")
    if not (MW_API_OFFSET < oil_api < 100.0):
        raise ValueError(
            f"oil_api must be in ({MW_API_OFFSET}, 100), got {oil_api!r}"
        )
    if not (z_at_pi > 0.0):
        raise ValueError(f"z_at_pi must be > 0, got {z_at_pi!r}")

    # Eq. (4.2): gamma_o from API
    gamma_o = API_NUM / (API_DEN_OFFSET + oil_api)
    # Eq. (3.22): M_wo from API
    mw_o = MW_NUM / (oil_api - MW_API_OFFSET)

    r1 = gas_sep_rate_scf_d / oil_rate_stb_d
    r3 = gas_tank_rate_scf_d / oil_rate_stb_d

    # Eq. (4.1): gamma_w
    num = r1 * gas_sep_sg + GW_GAMMA_O_COEF * gamma_o + r3 * gas_tank_sg
    den = r1 + GW_DEN_GAMMA_O_COEF * gamma_o / mw_o + r3
    gamma_w = num / den

    # Real-gas law, unit basis (see book p. 113)
    T_R = T_F + 459.67
    V_HC = CUFT_PER_ACFT * phi_frac * (1.0 - Swi_frac)
    g_unit = (SCF_PER_LBMOL * pi_psia * V_HC
              / (K_1000 * z_at_pi * R_PRIME * T_R))

    # Eq. (4.3): f_s
    n_s = (r1 + r3) / SCF_PER_LBMOL
    n_o = LB_PER_BBL_WATER * gamma_o / mw_o
    f_s = n_s / (n_s + n_o)

    g_gas_unit = f_s * g_unit
    n_oil_unit = (g_gas_unit * K_1000) / (r1 + r3)

    in_validity = (30.0 <= oil_api <= 70.0)

    return GCInitialRateResult(
        gamma_o=gamma_o,
        mw_o=mw_o,
        r1_sep_scf_stb=r1,
        r3_tank_scf_stb=r3,
        gamma_w=gamma_w,
        f_s_gas_frac=f_s,
        g_unit_mmscf_per_acft=g_unit,
        g_gas_unit_mmscf_per_acft=g_gas_unit,
        n_oil_unit_stb_per_acft=n_oil_unit,
        in_validity=in_validity,
    )
