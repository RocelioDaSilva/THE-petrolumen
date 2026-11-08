"""Productivity index and specific productivity index.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 7, Sec. 8, pp. 246-248,
Eqs. (7.52)-(7.56), Example 7.2 (pp. 256-258).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

J_COEFF = 0.00708         # same as Eq. 7.19
PSI_CONST = 0.75          # pseudosteady ln term offset


@dataclass(frozen=True)
class ProductivityIndexResult:
    J_stb_per_psi: float
    Js_stb_per_psi_ft: float | None
    injectivity_index: float | None
    productivity_ratio: float | None


def productivity_index_empirical(
    q_stb_d: float,
    p_avg_psia: float,
    p_wf_psia: float,
    h_ft: float | None = None,
    injection: bool = False,
) -> ProductivityIndexResult:
    """Empirical PI from a well test (Craft Eq. 7.52 / 7.53).

    Args:
        q_stb_d: Flow (or injection) rate, STB/day (>= 0).
        p_avg_psia: Average reservoir pressure, psia (> 0).
        p_wf_psia: Flowing bottomhole pressure, psia (> 0).
        h_ft: Net pay thickness, ft (> 0; optional, for Js).
        injection: If True, compute injectivity index I (Eq. 7.53)
            instead of productivity index J (Eq. 7.52).

    Returns:
        ProductivityIndexResult with J, optional Js.

    Raises:
        ValueError: any input out of range or no drawdown.
    """
    if not (q_stb_d >= 0.0):
        raise ValueError(f"q_stb_d must be >= 0, got {q_stb_d!r}")
    if not (p_avg_psia > 0.0):
        raise ValueError(f"p_avg_psia must be > 0, got {p_avg_psia!r}")
    if not (p_wf_psia > 0.0):
        raise ValueError(f"p_wf_psia must be > 0, got {p_wf_psia!r}")

    dp = p_avg_psia - p_wf_psia
    if injection:
        # I = q / (p_wf - p_avg)
        if not (p_wf_psia > p_avg_psia):
            raise ValueError(
                f"injection requires p_wf > p_avg, got "
                f"p_wf={p_wf_psia!r}, p_avg={p_avg_psia!r}"
            )
        I_val = q_stb_d / (p_wf_psia - p_avg_psia)
        return ProductivityIndexResult(
            J_stb_per_psi=0.0, Js_stb_per_psi_ft=None,
            injectivity_index=I_val, productivity_ratio=None,
        )

    if not (dp > 0.0):
        raise ValueError(
            f"drawdown p_avg - p_wf = {dp!r} <= 0; "
            "cannot compute PI"
        )
    J_val = q_stb_d / dp
    Js_val = J_val / h_ft if h_ft is not None else None
    if h_ft is not None and not (h_ft > 0.0):
        raise ValueError(f"h_ft must be > 0 if provided, got {h_ft!r}")
    return ProductivityIndexResult(
        J_stb_per_psi=J_val, Js_stb_per_psi_ft=Js_val,
        injectivity_index=None, productivity_ratio=None,
    )


def productivity_index_theoretical(
    k_md: float,
    h_ft: float,
    mu_cp: float,
    B_bbl_stb: float,
    r_e_ft: float,
    r_w_ft: float,
    S: float = 0.0,
) -> float:
    """Theoretical PI for pseudosteady radial flow with skin.

    Implements the J formula from Craft, Hawkins, Terry (1991), Ch. 7,
    Sec. 8, p. 248, based on Eq. (7.55): J = 0.00708*k*h / (mu*B*
    (ln(re/rw) - 0.75 + S)).

    Args:
        k_md: Permeability, md (> 0).
        h_ft: Net pay thickness, ft (> 0).
        mu_cp: Viscosity, cp (> 0).
        B_bbl_stb: FVF, bbl/STB (> 0).
        r_e_ft: Drainage radius, ft (> r_w).
        r_w_ft: Wellbore radius, ft (> 0).
        S: Skin factor (dimensionless; can be negative).

    Returns:
        J (STB/day/psi).

    Raises:
        ValueError: any input out of range, or denominator <= 0.
    """
    for name, v in [
        ("k_md", k_md), ("h_ft", h_ft), ("mu_cp", mu_cp),
        ("B_bbl_stb", B_bbl_stb), ("r_e_ft", r_e_ft), ("r_w_ft", r_w_ft),
    ]:
        if not (v > 0.0):
            raise ValueError(f"{name} must be > 0, got {v!r}")
    if not (r_e_ft > r_w_ft):
        raise ValueError(
            f"r_e_ft ({r_e_ft!r}) must exceed r_w_ft ({r_w_ft!r})"
        )
    denom = math.log(r_e_ft / r_w_ft) - PSI_CONST + S
    if denom <= 0.0:
        raise ValueError(
            f"ln(re/rw) - 0.75 + S = {denom!r} <= 0; PI would be negative "
            "or infinite; check skin and geometry."
        )
    return J_COEFF * k_md * h_ft / (mu_cp * B_bbl_stb * denom)


def productivity_ratio(
    J: float, J_std: float,
) -> float:
    """Productivity ratio (Eq. 7.56, p. 248).

    Args:
        J: PI of the well in its current condition, STB/day/psi (> 0).
        J_std: PI of the reference openhole well, STB/day/psi (> 0).

    Returns:
        Productivity ratio PR (dimensionless).

    Raises:
        ValueError: either PI <= 0.
    """
    if not (J > 0.0):
        raise ValueError(f"J must be > 0, got {J!r}")
    if not (J_std > 0.0):
        raise ValueError(f"J_std must be > 0, got {J_std!r}")
    return J / J_std
