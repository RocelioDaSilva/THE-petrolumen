"""Undersaturated oil MB below bubble point.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 5, Sec. 3, pp. 153-157, Eqs. (5.6)-(5.11); Sec. 6, p. 173,
Eq. (5.29). Example 5.1 (pp. 156-157).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OilMBBelowPbResult:
    n_stb: float
    rf_fraction: float
    tp_coef: float
    denom_bbl_stb: float


def _validate_below_pb_inputs(
    Np_stb: float, Rp: float, Rsoi: float,
    Bt: float, Bti: float, Bg: float,
) -> None:
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
    if Bt < Bti - 1e-12:
        raise ValueError(
            f"Bt = {Bt!r} < Bti = {Bti!r}; oil FVF cannot shrink below "
            "initial in an undersaturated reservoir."
        )
    if not (Bg > 0.0):
        raise ValueError(f"Bg must be > 0, got {Bg!r}")


def oil_mb_below_pb_volumetric(
    Np_stb: float,
    Rp: float,
    Rsoi: float,
    Bt: float,
    Bti: float,
    Bg: float,
) -> OilMBBelowPbResult:
    """Undersaturated oil MB below bubble point, volumetric (Eq. 5.10).

    Implements Eqs. (5.10)-(5.11) from Craft, Hawkins, Terry (1991),
    Ch. 5, Sec. 3, pp. 153-157. Volumetric only: no water influx, no
    compressibilities.

    Args:
        Np_stb: Cumulative oil produced, STB (>= 0).
        Rp: Cumulative produced GOR, SCF/STB (>= 0).
        Rsoi: Initial solution GOR, SCF/STB (>= 0).
        Bt: Two-phase FVF at current p, bbl/STB (> 0).
        Bti: Initial two-phase FVF, bbl/STB (> 0).
        Bg: Gas FVF at current p, bbl/SCF (> 0).

    Returns:
        OilMBBelowPbResult.

    Raises:
        ValueError: any input out of range, Bt < Bti, or
            two-phase coefficient <= 0.
    """
    _validate_below_pb_inputs(Np_stb, Rp, Rsoi, Bt, Bti, Bg)

    tp = Bt + (Rp - Rsoi) * Bg
    if tp <= 0.0:
        raise ValueError(
            f"Two-phase production coefficient tp = {tp!r} <= 0; "
            "R_p is below R_soi with no compensating Bt growth."
        )

    denom = Bt - Bti
    if denom <= 0.0:
        raise ValueError(
            f"Denominator Bt - Bti = {denom!r} <= 0; no physical solution."
        )

    n_est = Np_stb * tp / denom
    rf = denom / tp

    return OilMBBelowPbResult(
        n_stb=n_est, rf_fraction=rf,
        tp_coef=tp, denom_bbl_stb=denom,
    )


def oil_mb_below_pb_general(
    Np_stb: float,
    Rp: float,
    Rsoi: float,
    Bt: float,
    Bti: float,
    Bg: float,
    Swi: float,
    cw: float,
    cf: float,
    delta_p: float,
    We: float = 0.0,
    Wp: float = 0.0,
    Bw: float = 1.0,
) -> OilMBBelowPbResult:
    """Undersaturated oil MB below bubble point, with comps (Eq. 5.29).

    Implements Eq. (5.29) from Craft, Hawkins, Terry (1991), Ch. 5,
    Sec. 6, p. 173. Includes connate-water and formation compressibilities
    and water influx.

    Args:
        (as volumetric) plus:
        Swi: Connate water saturation, fraction [0, 1).
        cw: Water compressibility, psi^-1 (>= 0).
        cf: Formation compressibility, psi^-1 (>= 0).
        delta_p: Pressure drop pi - p, psi (>= 0).
        We: Water influx, bbl (>= 0; default 0).
        Wp: Water produced, STB (>= 0; default 0).
        Bw: Water FVF, bbl/STB (> 0; default 1.0).

    Returns:
        OilMBBelowPbResult.

    Raises:
        ValueError: any input out of range, or denominator <= 0.
    """
    _validate_below_pb_inputs(Np_stb, Rp, Rsoi, Bt, Bti, Bg)
    if not (0.0 <= Swi < 1.0):
        raise ValueError(f"Swi must be in [0, 1), got {Swi!r}")
    if not (cw >= 0.0):
        raise ValueError(f"cw must be >= 0, got {cw!r}")
    if not (cf >= 0.0):
        raise ValueError(f"cf must be >= 0, got {cf!r}")
    if not (delta_p >= 0.0):
        raise ValueError(f"delta_p must be >= 0, got {delta_p!r}")
    if not (We >= 0.0):
        raise ValueError(f"We must be >= 0, got {We!r}")
    if not (Wp >= 0.0):
        raise ValueError(f"Wp must be >= 0, got {Wp!r}")
    if not (Bw > 0.0):
        raise ValueError(f"Bw must be > 0, got {Bw!r}")

    tp = Bt + (Rp - Rsoi) * Bg
    if tp <= 0.0:
        raise ValueError(
            f"Two-phase production coefficient tp = {tp!r} <= 0."
        )

    comp_coef = (cw * Swi + cf) / (1.0 - Swi)
    compression_term = Bti * comp_coef * delta_p
    denom = (Bt - Bti) + compression_term
    if denom <= 0.0:
        raise ValueError(
            f"MB denominator = {denom!r} <= 0; no physical solution."
        )

    numerator = Np_stb * tp - We + Bw * Wp
    n_est = numerator / denom
    rf = Np_stb / n_est if n_est > 0.0 else 0.0

    return OilMBBelowPbResult(
        n_stb=n_est, rf_fraction=rf,
        tp_coef=tp, denom_bbl_stb=denom,
    )
