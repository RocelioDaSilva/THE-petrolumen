"""Steady-state radial flow, liquid and gas.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 7, Sec. 4.6-4.8, pp. 226-229,
Eqs. (7.19), (7.20), (7.21), (7.22).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

C_INC = 0.00708         # Eq. (7.19), (7.20)
C_GAS_LP = 0.01988      # Eq. (7.21)
C_GAS_HP = 0.03976      # Eq. (7.22)

Form = Literal[
    "incompressible",
    "slightly_compressible",
    "gas_low_p",
    "gas_high_p",
]


@dataclass(frozen=True)
class RadialFlowResult:
    q: float
    form: Form
    ln_re_over_rw: float


def _check_common(
    k: float, h: float, p_e: float, p_w: float,
    r_e: float, r_w: float,
) -> float:
    if not (k > 0.0):
        raise ValueError(f"k must be > 0, got {k!r}")
    if not (h > 0.0):
        raise ValueError(f"h must be > 0, got {h!r}")
    if not (p_e > p_w):
        raise ValueError(
            f"p_e ({p_e!r}) must exceed p_w ({p_w!r}) for forward flow"
        )
    if not (p_w > 0.0):
        raise ValueError(f"p_w must be > 0, got {p_w!r}")
    if not (r_w > 0.0):
        raise ValueError(f"r_w must be > 0, got {r_w!r}")
    if not (r_e > r_w):
        raise ValueError(
            f"r_e ({r_e!r}) must exceed r_w ({r_w!r})"
        )
    return math.log(r_e / r_w)


def radial_flow_incompressible(
    k: float, h: float, p_e: float, p_w: float,
    mu: float, B: float, r_e: float, r_w: float,
) -> RadialFlowResult:
    """Incompressible radial flow (Eq. 7.19, p. 227). STB/day."""
    ln_r = _check_common(k, h, p_e, p_w, r_e, r_w)
    if not (mu > 0.0):
        raise ValueError(f"mu must be > 0, got {mu!r}")
    if not (B > 0.0):
        raise ValueError(f"B must be > 0, got {B!r}")
    q = C_INC * k * h * (p_e - p_w) / (mu * B * ln_r)
    return RadialFlowResult(q=q, form="incompressible", ln_re_over_rw=ln_r)


def radial_flow_slightly_compressible(
    k: float, h: float, p_e: float, p_w: float, pR: float,
    mu: float, c: float, r_e: float, r_w: float,
) -> RadialFlowResult:
    """Slightly compressible radial flow (Eq. 7.20, p. 228)."""
    ln_r = _check_common(k, h, p_e, p_w, r_e, r_w)
    if not (mu > 0.0):
        raise ValueError(f"mu must be > 0, got {mu!r}")
    if not (c > 0.0):
        raise ValueError(f"c must be > 0, got {c!r}")
    if not (pR > 0.0):
        raise ValueError(f"pR must be > 0, got {pR!r}")
    arg_num = 1.0 + c * (pR - p_w)
    arg_den = 1.0 + c * (pR - p_e)
    if arg_num <= 0.0 or arg_den <= 0.0:
        raise ValueError(
            f"log argument non-positive (num={arg_num!r}, den={arg_den!r})"
        )
    q = (
        C_INC * k * h / (mu * c * ln_r)
        * math.log(arg_num / arg_den)
    )
    return RadialFlowResult(
        q=q, form="slightly_compressible", ln_re_over_rw=ln_r,
    )


def radial_flow_gas_low_p(
    k: float, h: float, p_e: float, p_w: float,
    T_sc: float, p_sc: float, T: float, z: float, mu: float,
    r_e: float, r_w: float,
) -> RadialFlowResult:
    """Gas radial flow, low pressure (Eq. 7.21, p. 228). SCF/day."""
    ln_r = _check_common(k, h, p_e, p_w, r_e, r_w)
    if not (T_sc > 0.0):
        raise ValueError(f"T_sc must be > 0, got {T_sc!r}")
    if not (p_sc > 0.0):
        raise ValueError(f"p_sc must be > 0, got {p_sc!r}")
    if not (T > 0.0):
        raise ValueError(f"T must be > 0, got {T!r}")
    if not (z > 0.0):
        raise ValueError(f"z must be > 0, got {z!r}")
    if not (mu > 0.0):
        raise ValueError(f"mu must be > 0, got {mu!r}")
    q = (
        C_GAS_LP * T_sc * k * h * (p_e * p_e - p_w * p_w)
        / (p_sc * T * (mu * z) * ln_r)
    )
    return RadialFlowResult(q=q, form="gas_low_p", ln_re_over_rw=ln_r)


def radial_flow_gas_high_p(
    k: float, h: float, p_e: float, p_w: float,
    T_sc: float, p_sc: float, T: float, mu_z_over_p: float,
    r_e: float, r_w: float,
) -> RadialFlowResult:
    """Gas radial flow, high pressure (Eq. 7.22, p. 228). SCF/day."""
    ln_r = _check_common(k, h, p_e, p_w, r_e, r_w)
    if not (T_sc > 0.0):
        raise ValueError(f"T_sc must be > 0, got {T_sc!r}")
    if not (p_sc > 0.0):
        raise ValueError(f"p_sc must be > 0, got {p_sc!r}")
    if not (T > 0.0):
        raise ValueError(f"T must be > 0, got {T!r}")
    if not (mu_z_over_p > 0.0):
        raise ValueError(
            f"mu_z_over_p must be > 0, got {mu_z_over_p!r}"
        )
    q = (
        C_GAS_HP * k * h * T_sc * (p_e - p_w)
        / (p_sc * T * mu_z_over_p * ln_r)
    )
    return RadialFlowResult(q=q, form="gas_high_p", ln_re_over_rw=ln_r)
