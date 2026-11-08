"""Fractional flow and Buckley-Leverett frontal advance.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 9, Sec. 2.2, pp. 337-347 and Sec. 3.1, pp. 347-354,
Eqs. (9.3), (9.5)-(9.6), (9.15)-(9.17), Table 9.1.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Eq. (9.15), p. 349: bbl per cu ft
BBL_PER_CUFT = 5.615


@dataclass(frozen=True)
class FracFlowPoint:
    Sw: float
    ko_over_kw: float
    fw: float
    dfw_dSw: float


@dataclass(frozen=True)
class BuckleyLeverettResult:
    points: tuple[FracFlowPoint, ...]
    # Only populated in frontal_advance mode:
    x_by_Sw_by_time: tuple[tuple[float, ...], ...]
    times_days: tuple[float, ...]


def _ko_over_kw(Sw: float, a: float, b: float) -> float:
    """Eq. (9.3): ko/kw = a * exp(-b*Sw)."""
    return a * math.exp(-b * Sw)


def _fw_from_Sw(Sw: float, mu_w: float, mu_o: float,
                a: float, b: float) -> tuple[float, float, float]:
    """Return (ko_over_kw, fw, dfw_dSw) via Eqs. 9.6 and 9.17."""
    ko_kw = _ko_over_kw(Sw, a, b)
    mu_ratio = mu_w / mu_o
    g = mu_ratio * ko_kw
    fw = 1.0 / (1.0 + g)
    # Eq. (9.17): dfw/dSw = mu_ratio * b * ko_kw / (1 + mu_ratio*ko_kw)^2
    dfw_dSw = mu_ratio * b * ko_kw / ((1.0 + g) ** 2)
    return ko_kw, fw, dfw_dSw


def _validate_common(
    mu_w: float, mu_o: float, a: float, b: float,
) -> None:
    if not (mu_w > 0.0):
        raise ValueError(f"mu_w must be > 0, got {mu_w!r}")
    if not (mu_o > 0.0):
        raise ValueError(f"mu_o must be > 0, got {mu_o!r}")
    if not (a > 0.0):
        raise ValueError(f"a must be > 0, got {a!r}")
    if not (b > 0.0):
        raise ValueError(f"b must be > 0, got {b!r}")


def buckley_leverett_single(
    Sw: float, mu_w: float, mu_o: float, a: float, b: float,
) -> BuckleyLeverettResult:
    """Single-point fw and derivative at given Sw (Eqs. 9.3, 9.6, 9.17).

    Args:
        Sw: Water saturation, fraction (0, 1).
        mu_w: Water viscosity, cp (> 0).
        mu_o: Oil viscosity, cp (> 0).
        a: Eq. (9.3) intercept, dimensionless (> 0).
        b: Eq. (9.3) slope, 1/fraction (> 0).

    Returns:
        BuckleyLeverettResult with one point.

    Raises:
        ValueError: any input out of physical range.
    """
    _validate_common(mu_w, mu_o, a, b)
    if not (0.0 < Sw < 1.0):
        raise ValueError(f"Sw must be in (0, 1), got {Sw!r}")

    ko_kw, fw, dfw = _fw_from_Sw(Sw, mu_w, mu_o, a, b)
    pt = FracFlowPoint(Sw=Sw, ko_over_kw=ko_kw, fw=fw, dfw_dSw=dfw)
    return BuckleyLeverettResult(
        points=(pt,),
        x_by_Sw_by_time=(),
        times_days=(),
    )


def buckley_leverett_advance(
    Sw_list: list[float],
    mu_w: float, mu_o: float, a: float, b: float,
    qi_bbl_d: float, phi: float, Ac_ft2: float,
    times_days: list[float],
) -> BuckleyLeverettResult:
    """Frontal advance of each saturation plane over time (Eq. 9.15).

    For each Sw in Sw_list and each t in times_days, computes
    x(Sw, t) = (5.615*qi/(phi*Ac)) * t * dfw_dSw(Sw).

    Args:
        Sw_list: Water saturations (each in (0, 1)), any order.
        mu_w, mu_o: Viscosities (cp, > 0).
        a, b: Eq. (9.3) fit parameters (> 0).
        qi_bbl_d: Total reservoir-barrel throughput rate, bbl/day (> 0).
        phi: Porosity, fraction (0, 1).
        Ac_ft2: Cross-sectional area, ft^2 (> 0).
        times_days: List of observation times, days (each >= 0).

    Returns:
        BuckleyLeverettResult with points (one per Sw), x_by_Sw_by_time
        (indexed as x_by_Sw_by_time[Sw_index][time_index]), and times.

    Raises:
        ValueError: any input out of range, or empty lists.
    """
    _validate_common(mu_w, mu_o, a, b)
    if len(Sw_list) == 0:
        raise ValueError("Sw_list must be non-empty")
    if len(times_days) == 0:
        raise ValueError("times_days must be non-empty")
    if not (qi_bbl_d > 0.0):
        raise ValueError(f"qi_bbl_d must be > 0, got {qi_bbl_d!r}")
    if not (0.0 < phi < 1.0):
        raise ValueError(f"phi must be in (0, 1), got {phi!r}")
    if not (Ac_ft2 > 0.0):
        raise ValueError(f"Ac_ft2 must be > 0, got {Ac_ft2!r}")
    for i, t in enumerate(times_days):
        if not (t >= 0.0):
            raise ValueError(
                f"times_days[{i}] must be >= 0, got {t!r}"
            )

    coef = BBL_PER_CUFT * qi_bbl_d / (phi * Ac_ft2)   # ft per day per unit dSw

    points: list[FracFlowPoint] = []
    for i, Sw in enumerate(Sw_list):
        if not (0.0 < Sw < 1.0):
            raise ValueError(
                f"Sw_list[{i}] must be in (0, 1), got {Sw!r}"
            )
        ko_kw, fw, dfw = _fw_from_Sw(Sw, mu_w, mu_o, a, b)
        points.append(FracFlowPoint(
            Sw=Sw, ko_over_kw=ko_kw, fw=fw, dfw_dSw=dfw,
        ))

    x_by_row: list[tuple[float, ...]] = []
    for pt in points:
        row = tuple(coef * t * pt.dfw_dSw for t in times_days)
        x_by_row.append(row)

    return BuckleyLeverettResult(
        points=tuple(points),
        x_by_Sw_by_time=tuple(x_by_row),
        times_days=tuple(times_days),
    )
