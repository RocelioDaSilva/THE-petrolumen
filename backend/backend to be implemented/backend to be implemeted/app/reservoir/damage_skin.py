"""Skin factor from altered-zone parameters (Craft Eq. 7.24 + 7.64)."""
from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class DamageSkinResult:
    S: float
    kind: str   # "damage", "stimulation", "undamaged"


def damage_skin(
    k_e_md: float, k_a_md: float, r_a_ft: float, r_w_ft: float,
) -> DamageSkinResult:
    """Return skin factor from altered-zone k_e, k_a, r_a, r_w.

    Args:
        k_e_md: Unaltered (outer) permeability, md (> 0).
        k_a_md: Altered (inner) permeability, md (> 0).
        r_a_ft: Altered-zone outer radius, ft (> r_w).
        r_w_ft: Wellbore radius, ft (> 0).

    Returns:
        DamageSkinResult with S and classification.

    Raises:
        ValueError: any input out of range or r_a <= r_w.
    """
    for n, v in [("k_e_md", k_e_md), ("k_a_md", k_a_md),
                 ("r_a_ft", r_a_ft), ("r_w_ft", r_w_ft)]:
        if not (v > 0.0):
            raise ValueError(f"{n} must be > 0, got {v!r}")
    if not (r_a_ft > r_w_ft):
        raise ValueError(
            f"r_a_ft ({r_a_ft!r}) must exceed r_w_ft ({r_w_ft!r})"
        )
    S = (k_e_md / k_a_md - 1.0) * math.log(r_a_ft / r_w_ft)
    if S > 0.1:
        kind = "damage"
    elif S < -0.1:
        kind = "stimulation"
    else:
        kind = "undamaged"
    return DamageSkinResult(S=S, kind=kind)
