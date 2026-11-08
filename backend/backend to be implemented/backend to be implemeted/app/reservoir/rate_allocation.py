"""Multilateral rate-allocation error diagnostic.

Source: Chin, W.C. (2016), Reservoir Engineering in Modern Oilfields,
Wiley, Ch. 2, pp. 32-33. Quantifies the "kh allocation" error.
"""
from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class RateAllocBlock:
    k_md: float
    h_ft: float
    S: float
    mu_cp: float
    B_bbl_stb: float
    r_e_ft: float
    r_w_ft: float
    p_avg_psia: float = 4000.0


@dataclass(frozen=True)
class RateAllocResult:
    q_alloc_stb_d: tuple[float, ...]
    p_w_psia: tuple[float, ...]
    dp_kh_error_psi: float
    error_fraction: float
    classification: str
    recommendation: str


def multilateral_rate_allocation_error(
    Q_stb_d: float,
    blocks: list[RateAllocBlock],
) -> RateAllocResult:
    """Quantify the error of the kh-allocation shortcut (Chin pp. 32-33)."""
    if not (Q_stb_d > 0.0):
        raise ValueError(f"Q_stb_d must be > 0, got {Q_stb_d!r}")
    if len(blocks) < 2:
        raise ValueError(
            f"at least 2 blocks required, got {len(blocks)}"
        )
    kh = []
    for i, b in enumerate(blocks):
        if not (b.k_md > 0.0):
            raise ValueError(f"blocks[{i}].k_md must be > 0")
        if not (b.h_ft > 0.0):
            raise ValueError(f"blocks[{i}].h_ft must be > 0")
        if not (b.mu_cp > 0.0):
            raise ValueError(f"blocks[{i}].mu_cp must be > 0")
        if not (b.B_bbl_stb > 0.0):
            raise ValueError(f"blocks[{i}].B_bbl_stb must be > 0")
        if not (b.r_e_ft > b.r_w_ft > 0.0):
            raise ValueError(
                f"blocks[{i}] requires r_e > r_w > 0"
            )
        if not (b.p_avg_psia > 0.0):
            raise ValueError(f"blocks[{i}].p_avg_psia must be > 0")
        kh.append(b.k_md * b.h_ft)

    sum_kh = sum(kh)
    q_alloc = tuple(Q_stb_d * k / sum_kh for k in kh)

    p_w = []
    dp_draw = []
    for i, b in enumerate(blocks):
        ln_re_rw = math.log(b.r_e_ft / b.r_w_ft) - 0.75 + b.S
        if not (ln_re_rw > 0.0):
            raise ValueError(
                f"blocks[{i}]: ln(r_e/r_w) - 0.75 + S = "
                f"{ln_re_rw!r} <= 0"
            )
        dp_i = (q_alloc[i] * b.mu_cp * b.B_bbl_stb
                / (0.00708 * b.k_md * b.h_ft)) * ln_re_rw
        p_w.append(b.p_avg_psia - dp_i)
        dp_draw.append(dp_i)

    dp_err = max(p_w) - min(p_w)
    mean_draw = sum(dp_draw) / len(dp_draw)
    frac = dp_err / mean_draw if mean_draw > 0 else float("inf")

    if frac < 0.05:
        cls = "acceptable"
        rec = ("kh-allocation pressure deviation is <5% of drawdown; "
               "shortcut is acceptable for this well.")
    elif frac < 0.20:
        cls = "suspect"
        rec = ("kh-allocation pressure deviation is 5-20%; kh shortcut "
               "should be cross-checked against a numerical simulator.")
    else:
        cls = "reject"
        rec = ("kh-allocation pressure deviation is >20%; use a "
               "numerical simulator (Chin p. 32: 'inherently incorrect "
               "and flawed').")

    return RateAllocResult(
        q_alloc_stb_d=q_alloc,
        p_w_psia=tuple(p_w),
        dp_kh_error_psi=dp_err,
        error_fraction=frac,
        classification=cls,
        recommendation=rec,
    )
