"""General oil material balance with Pirson drive indices.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 2, Sec. 2-3, pp. 56-64, Eqs. (2.7)-(2.11);
Ch. 6, Sec. 2, pp. 186-191, Example 6.1 (p. 187).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OilMaterialBalanceResult:
    n_estimated: float
    ddi: float
    sdi: float
    wdi: float
    index_sum: float
    rhs_hc_bbl: float
    net_water_influx_bbl: float
    expansion_oil_bbl: float
    expansion_gas_bbl: float
    expansion_water_bbl: float
    denom_bbl_stb: float


def oil_material_balance(
    Np: float,
    Rp: float,
    Wp: float,
    Bt: float,
    Bti: float,
    Bg: float,
    Rsoi: float,
    m: float = 0.0,
    Bgi: float | None = None,
    We: float = 0.0,
    Bw: float = 1.0,
    Swi: float = 0.0,
    cw: float = 0.0,
    cf: float = 0.0,
    delta_p: float = 0.0,
) -> OilMaterialBalanceResult:
    """Single-point general material balance (Craft Eq. 2.7 / 2.11).

    Solves for N given current production and PVT, and returns the
    Pirson drive indices DDI/SDI/WDI (Eq. 2.11). The compressibility
    term is included in N but neglected in the drive indices, matching
    the book's convention on p. 63.

    Args:
        Np: Cumulative oil produced, STB (>= 0).
        Rp: Cumulative produced GOR, SCF/STB (>= 0).
        Wp: Cumulative water produced, STB (>= 0).
        Bt: Two-phase oil FVF at current pressure, bbl/STB (> 0).
        Bti: Two-phase oil FVF at initial pressure, bbl/STB (> 0).
        Bg: Gas FVF at current pressure, bbl/SCF (> 0).
        Rsoi: Initial solution GOR, SCF/STB (>= 0).
        m: Initial gas-cap / oil-zone ratio (>= 0; default 0).
        Bgi: Initial gas FVF, bbl/SCF (> 0; required iff m > 0).
        We: Cumulative water influx, bbl (>= 0; default 0).
        Bw: Water FVF, bbl/STB (> 0; default 1.0).
        Swi: Connate water saturation, fraction ([0, 1); default 0).
        cw: Water isothermal compressibility, psi^-1 (>= 0; default 0).
        cf: Formation compressibility, psi^-1 (>= 0; default 0).
        delta_p: Pressure drop pi - p, psi (>= 0; default 0).

    Returns:
        OilMaterialBalanceResult.

    Raises:
        ValueError: any input out of physical range, or denominator
            <= 0 (no expansion despite production).
    """
    # Validation
    if not (Np >= 0.0):
        raise ValueError(f"Np must be >= 0, got {Np!r}")
    if not (Rp >= 0.0):
        raise ValueError(f"Rp must be >= 0, got {Rp!r}")
    if not (Wp >= 0.0):
        raise ValueError(f"Wp must be >= 0, got {Wp!r}")
    if not (Bt > 0.0):
        raise ValueError(f"Bt must be > 0, got {Bt!r}")
    if not (Bti > 0.0):
        raise ValueError(f"Bti must be > 0, got {Bti!r}")
    if not (Bg > 0.0):
        raise ValueError(f"Bg must be > 0, got {Bg!r}")
    if not (Rsoi >= 0.0):
        raise ValueError(f"Rsoi must be >= 0, got {Rsoi!r}")
    if not (m >= 0.0):
        raise ValueError(f"m must be >= 0, got {m!r}")
    if m > 0.0:
        if Bgi is None:
            raise ValueError("Bgi is required when m > 0")
        if not (Bgi > 0.0):
            raise ValueError(f"Bgi must be > 0, got {Bgi!r}")
    if not (We >= 0.0):
        raise ValueError(f"We must be >= 0, got {We!r}")
    if not (Bw > 0.0):
        raise ValueError(f"Bw must be > 0, got {Bw!r}")
    if not (0.0 <= Swi < 1.0):
        raise ValueError(f"Swi must be in [0, 1), got {Swi!r}")
    if not (cw >= 0.0):
        raise ValueError(f"cw must be >= 0, got {cw!r}")
    if not (cf >= 0.0):
        raise ValueError(f"cf must be >= 0, got {cf!r}")
    if not (delta_p >= 0.0):
        raise ValueError(f"delta_p must be >= 0, got {delta_p!r}")

    # Eq. (2.7), RHS without Bw*Wp (the "hydrocarbon production" term)
    rhs_hc = Np * (Bt + (Rp - Rsoi) * Bg)
    if rhs_hc <= 0.0:
        raise ValueError(
            f"RHS_hc = {rhs_hc!r} <= 0; drive indices require positive "
            "hydrocarbon production."
        )

    # Gas-cap expansion term (Eq. 2.7)
    if m > 0.0:
        assert Bgi is not None
        expansion_gas = (m * Bti / Bgi) * (Bg - Bgi)
    else:
        expansion_gas = 0.0

    # Compressibility term (Eq. 2.7)
    if Swi < 1.0:
        comp_coef = (cw * Swi + cf) / (1.0 - Swi)
    else:
        comp_coef = 0.0  # unreachable: Swi < 1 validated above
    expansion_water = (1.0 + m) * Bti * comp_coef * delta_p

    # Oil expansion term (Eq. 2.7)
    expansion_oil = Bt - Bti

    denom = expansion_oil + expansion_gas + expansion_water
    if denom <= 0.0:
        raise ValueError(
            f"Material balance denominator = {denom!r} <= 0; "
            "inputs give no physical expansion despite production."
        )

    net_water = We - Bw * Wp
    n_est = (rhs_hc - net_water) / denom

    # Pirson drive indices (Eq. 2.11, p. 63). Compressibility is
    # neglected in the drive-index denominator per the book.
    ddi = n_est * expansion_oil / rhs_hc
    sdi = n_est * expansion_gas / rhs_hc
    wdi = net_water / rhs_hc
    index_sum = ddi + sdi + wdi

    return OilMaterialBalanceResult(
        n_estimated=n_est,
        ddi=ddi,
        sdi=sdi,
        wdi=wdi,
        index_sum=index_sum,
        rhs_hc_bbl=rhs_hc,
        net_water_influx_bbl=net_water,
        expansion_oil_bbl=expansion_oil,
        expansion_gas_bbl=expansion_gas,
        expansion_water_bbl=expansion_water,
        denom_bbl_stb=denom,
    )
