"""Reservoir-fluid and pore-volume compressibility calculations.

Rock correlations follow Newman's correlations in Craft, Hawkins, and Terry
(1991), Eqs. 1.2-1.3. Gas compressibility follows Eq. 1.19 and differentiates
the isothermal Z-factor curve.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Literal

RockType = Literal["sandstone", "limestone"]

SANDSTONE_PHI_RANGE = (0.02, 0.23)
LIMESTONE_PHI_RANGE = (0.02, 0.33)

_RELATIVE_STEP = 1.0e-3
_MINIMUM_STEP_PSI = 0.5


@dataclass(frozen=True)
class GasCompressibilityResult:
    """Gas isothermal compressibility and its Z-factor derivative."""

    cg_psi_inv: float
    z_at_p: float
    dz_dp_psi_inv: float
    h_psi: float
    method: Literal["central", "forward"]


def formation_compressibility(
    phi: float,
    rock_type: RockType,
    strict: bool = False,
) -> float:
    """Return pore-volume compressibility ``cf`` in psi^-1.

    ``phi`` is porosity as a fraction. Setting ``strict`` enforces the
    correlation's published porosity interval for the selected lithology.
    """
    if isinstance(phi, bool) or not isinstance(phi, (int, float)):
        raise ValueError(f"phi must be numeric, got {type(phi).__name__}")
    phi = float(phi)
    if not math.isfinite(phi) or not 0.0 < phi < 1.0:
        raise ValueError(f"phi must be finite and in (0, 1), got {phi!r}")
    if not isinstance(strict, bool):
        raise ValueError(f"strict must be bool, got {type(strict).__name__}")

    if rock_type == "sandstone":
        phi_range = SANDSTONE_PHI_RANGE
        c1, multiplier, exponent = 97.3200e-6, 55.8721, 1.42859
    elif rock_type == "limestone":
        phi_range = LIMESTONE_PHI_RANGE
        c1, multiplier, exponent = 0.853531, 2.47664e6, 0.92990
    else:
        raise ValueError(
            "rock_type must be 'sandstone' or 'limestone', "
            f"got {rock_type!r}"
        )

    if strict and not phi_range[0] <= phi <= phi_range[1]:
        raise ValueError(
            f"{rock_type} phi={phi} outside book validity "
            f"[{phi_range[0]}, {phi_range[1]}]"
        )
    return c1 / math.pow(1.0 + multiplier * phi, exponent)


def gas_compressibility_from_z_curve(
    p_psia: float,
    z_func: Callable[[float], float],
    z_at_p: float | None = None,
    h_psi: float | None = None,
) -> GasCompressibilityResult:
    """Calculate isothermal gas compressibility ``cg = 1/p - (1/z) dz/dp``.

    A centered difference is used when the lower pressure sample remains
    positive; otherwise a forward difference is used. The caller must supply
    a Z-factor function at constant temperature and composition.
    """
    if not math.isfinite(p_psia) or p_psia <= 0:
        raise ValueError(f"p_psia must be a positive finite value, got {p_psia!r}")
    if not callable(z_func):
        raise ValueError("z_func must be callable")

    if h_psi is None:
        h = max(_RELATIVE_STEP * p_psia, _MINIMUM_STEP_PSI)
    else:
        if isinstance(h_psi, bool) or not isinstance(h_psi, (int, float)):
            raise ValueError("h_psi must be a positive finite number")
        h = float(h_psi)
        if not math.isfinite(h) or h <= 0:
            raise ValueError("h_psi must be a positive finite number")

    z = _positive_finite_z(
        z_at_p if z_at_p is not None else z_func(p_psia), "z at p"
    )
    if p_psia > h:
        z_plus = _positive_finite_z(z_func(p_psia + h), "z at p+h")
        z_minus = _positive_finite_z(z_func(p_psia - h), "z at p-h")
        dz_dp = (z_plus - z_minus) / (2.0 * h)
        method: Literal["central", "forward"] = "central"
    else:
        z_plus = _positive_finite_z(z_func(p_psia + h), "z at p+h")
        dz_dp = (z_plus - z) / h
        method = "forward"

    cg = 1.0 / p_psia - dz_dp / z
    if not math.isfinite(dz_dp) or not math.isfinite(cg):
        raise ValueError("Z-factor curve produced a non-finite compressibility")
    return GasCompressibilityResult(
        cg_psi_inv=cg,
        z_at_p=z,
        dz_dp_psi_inv=dz_dp,
        h_psi=h,
        method=method,
    )


def total_compressibility(
    *,
    cg_psi_inv: float,
    co_psi_inv: float,
    cw_psi_inv: float,
    cf_psi_inv: float,
    sg: float,
    so: float,
    sw: float,
) -> float:
    """Return ``ct = cg*Sg + co*So + cw*Sw + cf`` in psi^-1.

    Saturations must be non-negative and sum to one. Compressibilities are
    non-negative; ``cf`` is added as the pore-volume contribution specified
    by the cited total-compressibility relation.
    """
    values = {
        "cg_psi_inv": cg_psi_inv,
        "co_psi_inv": co_psi_inv,
        "cw_psi_inv": cw_psi_inv,
        "cf_psi_inv": cf_psi_inv,
        "sg": sg,
        "so": so,
        "sw": sw,
    }
    for name, value in values.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be numeric")
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")

    for name in ("cg_psi_inv", "co_psi_inv", "cw_psi_inv", "cf_psi_inv"):
        if values[name] < 0:
            raise ValueError(f"{name} must be non-negative")
    for name in ("sg", "so", "sw"):
        if not 0.0 <= values[name] <= 1.0:
            raise ValueError(f"{name} must be in [0, 1]")
    if not math.isclose(sg + so + sw, 1.0, rel_tol=0.0, abs_tol=1e-6):
        raise ValueError("sg, so, and sw must sum to 1")

    return cg_psi_inv * sg + co_psi_inv * so + cw_psi_inv * sw + cf_psi_inv


def _positive_finite_z(value: float, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a positive finite number")
    z = float(value)
    if not math.isfinite(z) or z <= 0:
        raise ValueError(f"{label} must be a positive finite number, got {z!r}")
    return z
