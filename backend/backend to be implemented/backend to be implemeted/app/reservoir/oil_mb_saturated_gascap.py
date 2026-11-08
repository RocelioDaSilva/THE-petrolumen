"""Saturated oil MB with gas cap and water drive.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 6, Sec. 2, pp. 186-191, Eqs. (6.1)-(6.2),
Example 6.1 (p. 187).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SaturatedOilMBResult:
    n_stb: float
    expansion_oil: float
    expansion_gas: float
    expansion_comp: float
    rhs_hc_bbl: float
    net_water_bbl: float
    denom_bbl_stb: float


def oil_mb_saturated_gascap(
    Np_stb: float,
    Rp: float,
    Bt: float,
    Bti: float,
    Bg: float,
    Rsoi: float,
    m: float = 0.0,
    Bgi: float | None = None,
    We: float = 0.0,
    Wp: float = 0.0,
    Bw: float = 1.0,
    Swi: float | None = None,
    cw: float = 0.0,
    cf: float = 0.0,
    delta_p: float = 0.0,
) -> SaturatedOilMBResult:
    """Saturated oil material balance (Craft Eq. 6.1 / 6.2).

    Implements Eq. (6.1) with optional compressibility term and Eq.
    (6.2) when compressibilities are zero. Requires Bg and Bgi in
    bbl/SCF (convert cu ft/SCF by dividing by 5.615).

    Args:
        Np_stb: Cumulative oil, STB (>= 0).
        Rp: Cumulative produced GOR, SCF/STB (>= 0).
        Bt: Two-phase FVF at p, bbl/STB (> 0).
        Bti: Two-phase FVF at pi, bbl/STB (> 0).
        Bg: Gas FVF at p, bbl/SCF (> 0).
        Rsoi: Initial solution GOR, SCF/STB (>= 0).
        m: Gas-cap / oil-zone ratio (>= 0; default 0).
        Bgi: Gas FVF at pi, bbl/SCF (> 0; required iff m > 0).
        We: Water influx, bbl (>= 0; default 0).
        Wp: Water produced, STB (>= 0; default 0).
        Bw: Water FVF, bbl/STB (> 0; default 1.0).
        Swi: Connate water saturation, fraction ([0, 1); default None
            means compressibility term = 0).
        cw: Water compressibility, psi^-1 (>= 0; default 0).
        cf: Formation compressibility, psi^-1 (>= 0; default 0).
        delta_p: Pressure drop pi - p, psi (>= 0; default 0).

    Returns:
        SaturatedOilMBResult with N and per-term decomposition.

    Raises:
        ValueError: any input out of physical range, m > 0 without Bgi,
            or denominator <= 0.
    """
    if not (Np_stb >= 0.0):
        raise ValueError(f"Np_stb must be >= 0, got {Np_stb!r}")
    if not (Rp >= 0.0):
        raise ValueError(f"Rp must be >= 0, got {Rp!r}")
    if not (Rsoi >= 0.0):
        raise ValueError(f"Rsoi must be >= 0, got {Rsoi!r}")
    if not (Bt > 0.0):
        raise ValueError(f"Bt must be > 0, got {Bt!r}")
    if not (Bti > 0.0):
        raise ValueError(f"Bti must be > 0, got {Bti!r}")
    if not (Bg > 0.0):
        raise ValueError(f"Bg must be > 0, got {Bg!r}")
    if not (m >= 0.0):
        raise ValueError(f"m must be >= 0, got {m!r}")
    if m > 0.0:
        if Bgi is None:
            raise ValueError("Bgi is required when m > 0")
        if not (Bgi > 0.0):
            raise ValueError(f"Bgi must be > 0, got {Bgi!r}")
    if not (We >= 0.0):
        raise ValueError(f"We must be >= 0, got {We!r}")
    if not (Wp >= 0.0):
        raise ValueError(f"Wp must be >= 0, got {Wp!r}")
    if not (Bw > 0.0):
        raise ValueError(f"Bw must be > 0, got {Bw!r}")
    if not (cw >= 0.0):
        raise ValueError(f"cw must be >= 0, got {cw!r}")
    if not (cf >= 0.0):
        raise ValueError(f"cf must be >= 0, got {cf!r}")
    if not (delta_p >= 0.0):
        raise ValueError(f"delta_p must be >= 0, got {delta_p!r}")
    if Swi is not None and not (0.0 <= Swi < 1.0):
        raise ValueError(f"Swi must be in [0, 1), got {Swi!r}")

    rhs_hc = Np_stb * (Bt + (Rp - Rsoi) * Bg)
    exp_oil = Bt - Bti
    if m > 0.0:
        assert Bgi is not None
        exp_gas = (m * Bti / Bgi) * (Bg - Bgi)
    else:
        exp_gas = 0.0
    if Swi is None or (cw == 0.0 and cf == 0.0) or delta_p == 0.0:
        exp_comp = 0.0
    else:
        exp_comp = (
            (1.0 + m) * Bti
            * ((cw * Swi + cf) / (1.0 - Swi))
            * delta_p
        )

    denom = exp_oil + exp_gas + exp_comp
    if denom <= 0.0:
        raise ValueError(
            f"MB denominator = {denom!r} <= 0; no physical solution "
            "(check Bt vs Bti and m/Bgi)."
        )

    net_water = We - Bw * Wp
    n_est = (rhs_hc - net_water) / denom

    return SaturatedOilMBResult(
        n_stb=n_est,
        expansion_oil=exp_oil,
        expansion_gas=exp_gas,
        expansion_comp=exp_comp,
        rhs_hc_bbl=rhs_hc,
        net_water_bbl=net_water,
        denom_bbl_stb=denom,
    )
