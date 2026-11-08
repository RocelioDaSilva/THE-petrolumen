"""Depth of damage from skin (Craft Eq. 7.24 + 7.64, Ex. 7.3)."""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Literal

Method = Literal["radius", "permeability"]


@dataclass(frozen=True)
class DamageDepthResult:
    method: Method
    r_a_ft: float
    r_a_over_rw: float
    k_a_md: float
    k_e_md: float
    S: float
    remediation: str


def damage_radius_from_skin(
    S: float, k_e_md: float, k_a_md: float, r_w_ft: float,
) -> DamageDepthResult:
    """Invert Feature 58 for r_a given S, k_e, k_a, r_w."""
    if not (k_e_md > 0.0):
        raise ValueError(f"k_e_md must be > 0, got {k_e_md!r}")
    if not (k_a_md > 0.0):
        raise ValueError(f"k_a_md must be > 0, got {k_a_md!r}")
    if not (r_w_ft > 0.0):
        raise ValueError(f"r_w_ft must be > 0, got {r_w_ft!r}")
    if S < 0.0:
        raise ValueError(
            f"S={S!r} < 0 (stimulation); use damage_permeability_from_skin"
        )
    ratio = k_e_md / k_a_md
    if ratio <= 1.0 + 1e-12:
        if S > 1e-6:
            raise ValueError(
                f"k_e/k_a={ratio!r} <= 1 but S={S!r} > 0; inconsistent"
            )
        r_a = r_w_ft
    else:
        r_a = r_w_ft * math.exp(S / (ratio - 1.0))
    ra_rw = r_a / r_w_ft
    if ra_rw < 2.0:
        remediation = "ream or reperforate (shallow)"
    elif ra_rw < 5.0:
        remediation = "reperforate or acidize"
    elif ra_rw < 10.0:
        remediation = "fracture or matrix acidize"
    else:
        remediation = "fracture (deep damage)"
    return DamageDepthResult(
        method="radius", r_a_ft=r_a, r_a_over_rw=ra_rw,
        k_a_md=k_a_md, k_e_md=k_e_md, S=S, remediation=remediation,
    )


def damage_permeability_from_skin(
    S: float, k_e_md: float, r_a_ft: float, r_w_ft: float,
) -> DamageDepthResult:
    """Invert Feature 58 for k_a given S, k_e, r_a, r_w."""
    if not (k_e_md > 0.0):
        raise ValueError(f"k_e_md must be > 0, got {k_e_md!r}")
    if not (r_a_ft > r_w_ft):
        raise ValueError(f"r_a_ft must exceed r_w_ft")
    if not (r_w_ft > 0.0):
        raise ValueError(f"r_w_ft must be > 0, got {r_w_ft!r}")
    ln_ra_rw = math.log(r_a_ft / r_w_ft)
    denom = 1.0 + S / ln_ra_rw
    if denom <= 0.0:
        raise ValueError(
            f"1 + S/ln(ra/rw) = {denom!r} <= 0; check S, r_a, r_w"
        )
    k_a = k_e_md / denom
    ra_rw = r_a_ft / r_w_ft
    if ra_rw < 2.0:
        remediation = "ream or reperforate (shallow)"
    elif ra_rw < 5.0:
        remediation = "reperforate or acidize"
    elif ra_rw < 10.0:
        remediation = "fracture or matrix acidize"
    else:
        remediation = "fracture (deep damage)"
    return DamageDepthResult(
        method="permeability", r_a_ft=r_a_ft, r_a_over_rw=ra_rw,
        k_a_md=k_a, k_e_md=k_e_md, S=S, remediation=remediation,
    )
