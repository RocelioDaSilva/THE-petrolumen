"""Undersaturated oil MB above bubble point, with compressibilities.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 5, Sec. 6, pp. 170-176, Eqs. (5.21)-(5.28),
Example 5.3 (p. 172).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OilMBAbovePbResult:
    n_stb: float
    ce_psi_inv: float | None
    compression_term_bbl_stb: float
    denom_bbl_stb: float


def effective_compressibility(
    So: float, Swi: float, co: float, cw: float, cf: float,
) -> float:
    """Effective fluid compressibility ce (Eq. 5.26, p. 171).

    Args:
        So: Oil saturation, fraction [0, 1).
        Swi: Connate water saturation, fraction [0, 1).
        co: Oil isothermal compressibility, psi^-1 (>= 0).
        cw: Water isothermal compressibility, psi^-1 (>= 0).
        cf: Formation compressibility, psi^-1 (>= 0).

    Returns:
        Effective compressibility ce, psi^-1.

    Raises:
        ValueError: any saturation out of range, So+Swi > 1, or any
            compressibility negative.
    """
    if not (0.0 <= So < 1.0):
        raise ValueError(f"So must be in [0, 1), got {So!r}")
    if not (0.0 <= Swi < 1.0):
        raise ValueError(f"Swi must be in [0, 1), got {Swi!r}")
    if So + Swi > 1.0 + 1e-9:
        raise ValueError(
            f"So + Swi = {So + Swi!r} exceeds 1.0 (physically invalid)"
        )
    if not (co >= 0.0):
        raise ValueError(f"co must be >= 0, got {co!r}")
    if not (cw >= 0.0):
        raise ValueError(f"cw must be >= 0, got {cw!r}")
    if not (cf >= 0.0):
        raise ValueError(f"cf must be >= 0, got {cf!r}")
    return (co * So + cw * Swi + cf) / (1.0 - Swi)


def oil_mb_above_pb(
    Np_stb: float,
    Bt: float,
    Bti: float,
    Swi: float,
    cw: float,
    cf: float,
    delta_p: float,
    We: float = 0.0,
    Wp: float = 0.0,
    Bw: float = 1.0,
    co: float | None = None,
    So: float | None = None,
) -> OilMBAbovePbResult:
    """Undersaturated oil material balance above bubble point.

    Implements Eq. (5.22) from Craft, Hawkins, Terry (1991), Ch. 5,
    Sec. 6, pp. 170-176, with optional ce from Eq. (5.26). Requires
    Bt >= Bti (above bubble point).

    Args:
        Np_stb: Cumulative oil produced, STB (>= 0).
        Bt: Two-phase FVF at current p, bbl/STB (> 0; = Bo above pb).
        Bti: Initial two-phase FVF, bbl/STB (> 0).
        Swi: Connate water saturation, fraction [0, 1).
        cw: Water compressibility, psi^-1 (>= 0).
        cf: Formation compressibility, psi^-1 (>= 0).
        delta_p: Pressure drop pi - p, psi (>= 0).
        We: Water influx, bbl (>= 0; default 0).
        Wp: Water produced, STB (>= 0; default 0).
        Bw: Water FVF, bbl/STB (> 0; default 1.0).
        co: Optional oil compressibility, psi^-1 (>= 0). If provided
            with So, returns ce in the result.
        So: Optional oil saturation, fraction [0, 1). Required iff
            co is provided.

    Returns:
        OilMBAbovePbResult(n_stb, ce_psi_inv, compression_term_bbl_stb,
        denom_bbl_stb).

    Raises:
        ValueError: any input out of range, Bt < Bti (wrong feature),
            or denominator <= 0.
    """
    if not (Np_stb >= 0.0):
        raise ValueError(f"Np_stb must be >= 0, got {Np_stb!r}")
    if not (Bt > 0.0):
        raise ValueError(f"Bt must be > 0, got {Bt!r}")
    if not (Bti > 0.0):
        raise ValueError(f"Bti must be > 0, got {Bti!r}")
    if Bt < Bti - 1e-12:
        raise ValueError(
            f"Bt = {Bt!r} < Bti = {Bti!r}; reservoir is below bubble "
            "point. Use Feature 18 (oil_mb_below_pb_general) instead."
        )
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
    if (co is None) != (So is None):
        raise ValueError(
            "Provide both co and So, or neither (for ce diagnostic)"
        )

    # Eq. (5.22): numerator and denominator
    numerator = Np_stb * Bt - We + Bw * Wp
    comp_coef = (cw * Swi + cf) / (1.0 - Swi)
    compression_term = Bti * comp_coef * delta_p
    denom = (Bt - Bti) + compression_term

    if denom <= 0.0:
        raise ValueError(
            f"MB denominator = {denom!r} <= 0; Bt - Bti and compressibility "
            "expansion are both non-positive, no physical solution exists."
        )

    n_est = numerator / denom

    ce_val: float | None = None
    if co is not None and So is not None:
        ce_val = effective_compressibility(So, Swi, co, cw, cf)

    return OilMBAbovePbResult(
        n_stb=n_est,
        ce_psi_inv=ce_val,
        compression_term_bbl_stb=compression_term,
        denom_bbl_stb=denom,
    )
