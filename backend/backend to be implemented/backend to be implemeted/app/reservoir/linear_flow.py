"""Steady-state linear flow, liquid and gas.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 7, Sec. 4.1-4.3, pp. 218-223,
Eqs. (7.7), (7.9), (7.10), (7.11).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

C_INC = 0.001127        # Eq. (7.7), (7.9)
C_GAS_LP = 0.003164     # Eq. (7.10)
C_GAS_HP = 0.006328     # Eq. (7.11)

Form = Literal[
    "incompressible",
    "slightly_compressible",
    "gas_low_p",
    "gas_high_p",
]


@dataclass(frozen=True)
class LinearFlowResult:
    q: float
    form: Form


def _check_common(k: float, Ac: float, L: float, mu: float,
                  p1: float, p2: float) -> None:
    if not (k > 0.0):
        raise ValueError(f"k must be > 0, got {k!r}")
    if not (Ac > 0.0):
        raise ValueError(f"Ac must be > 0, got {Ac!r}")
    if not (L > 0.0):
        raise ValueError(f"L must be > 0, got {L!r}")
    if not (mu > 0.0):
        raise ValueError(f"mu must be > 0, got {mu!r}")
    if not (p1 > p2):
        raise ValueError(
            f"p1 ({p1!r}) must exceed p2 ({p2!r}) for forward flow"
        )
    if not (p2 > 0.0):
        raise ValueError(f"p2 must be > 0, got {p2!r}")


def linear_flow_incompressible(
    k: float, Ac: float, p1: float, p2: float,
    B: float, mu: float, L: float,
) -> LinearFlowResult:
    """Incompressible linear flow (Eq. 7.7, p. 219). Returns STB/day."""
    _check_common(k, Ac, L, mu, p1, p2)
    if not (B > 0.0):
        raise ValueError(f"B must be > 0, got {B!r}")
    q = C_INC * k * Ac * (p1 - p2) / (B * mu * L)
    return LinearFlowResult(q=q, form="incompressible")


def linear_flow_slightly_compressible(
    k: float, Ac: float, p1: float, p2: float, pR: float,
    c: float, mu: float, L: float,
) -> LinearFlowResult:
    """Slightly compressible linear flow (Eq. 7.9, p. 220). Returns
    flow rate at reference pressure pR."""
    _check_common(k, Ac, L, mu, p1, p2)
    if not (c > 0.0):
        raise ValueError(f"c must be > 0, got {c!r}")
    if not (pR > 0.0):
        raise ValueError(f"pR must be > 0, got {pR!r}")
    arg_num = 1.0 + c * (pR - p2)
    arg_den = 1.0 + c * (pR - p1)
    if arg_num <= 0.0 or arg_den <= 0.0:
        raise ValueError(
            f"log argument non-positive (num={arg_num!r}, den={arg_den!r}); "
            "check c and reference pressure"
        )
    q = (
        C_INC * k * Ac / (mu * L * c)
        * math.log(arg_num / arg_den)
    )
    return LinearFlowResult(q=q, form="slightly_compressible")


def linear_flow_gas_low_p(
    k: float, Ac: float, p1: float, p2: float,
    T_sc: float, p_sc: float, T: float, z: float, mu: float, L: float,
) -> LinearFlowResult:
    """Gas linear flow, low pressure (Eq. 7.10, p. 221). Returns SCF/day."""
    _check_common(k, Ac, L, mu, p1, p2)
    if not (T_sc > 0.0):
        raise ValueError(f"T_sc must be > 0, got {T_sc!r}")
    if not (p_sc > 0.0):
        raise ValueError(f"p_sc must be > 0, got {p_sc!r}")
    if not (T > 0.0):
        raise ValueError(f"T must be > 0, got {T!r}")
    if not (z > 0.0):
        raise ValueError(f"z must be > 0, got {z!r}")
    q = (
        C_GAS_LP * T_sc * Ac * k * (p1 * p1 - p2 * p2)
        / (p_sc * T * z * mu * L)
    )
    return LinearFlowResult(q=q, form="gas_low_p")


def linear_flow_gas_high_p(
    k: float, Ac: float, p1: float, p2: float,
    T_sc: float, p_sc: float, T: float, mu_z_over_p: float, L: float,
) -> LinearFlowResult:
    """Gas linear flow, high pressure (Eq. 7.11, p. 222). Returns SCF/day.

    ``mu_z_over_p`` is (mu*z/p) evaluated at average pressure, cp/psia.
    """
    _check_common(k, Ac, L, 1.0, p1, p2)
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
        C_GAS_HP * k * T_sc * Ac * (p1 - p2)
        / (p_sc * T * mu_z_over_p)
    )
    return LinearFlowResult(q=q, form="gas_high_p")
