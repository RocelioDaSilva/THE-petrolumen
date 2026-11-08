"""Effective permeability in series and parallel.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 7, Sec. 4.4, pp. 223-226, Eqs. (7.12)-(7.14);
Sec. 4.9, pp. 229-230, Eq. (7.24).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class LayerPermResult:
    k_avg_md: float
    total_length_or_thickness: float
    total_capacity_md_ft: float | None


def _check_layer_list(name: str, values: list[float]) -> None:
    if len(values) == 0:
        raise ValueError(f"{name} list must be non-empty")
    for i, v in enumerate(values):
        if not (v > 0.0):
            raise ValueError(f"{name}[{i}] must be > 0, got {v!r}")


def linear_series(k_list: list[float], L_list: list[float]) -> LayerPermResult:
    """Series effective k (Eq. 7.12, p. 223).

    Args:
        k_list: Per-layer permeabilities, md (> 0).
        L_list: Per-layer lengths, ft (> 0); same length as k_list.

    Returns:
        LayerPermResult(k_avg_md, total_length_or_thickness,
        total_capacity_md_ft=None).

    Raises:
        ValueError: empty lists, length mismatch, or any value <= 0.
    """
    _check_layer_list("k_list", k_list)
    _check_layer_list("L_list", L_list)
    if len(k_list) != len(L_list):
        raise ValueError(
            f"k_list and L_list must have same length "
            f"({len(k_list)} vs {len(L_list)})"
        )
    total_L = sum(L_list)
    inv_sum = sum(L_i / k_i for k_i, L_i in zip(k_list, L_list))
    return LayerPermResult(
        k_avg_md=total_L / inv_sum,
        total_length_or_thickness=total_L,
        total_capacity_md_ft=None,
    )


def linear_parallel(
    k_list: list[float], h_list: list[float],
) -> LayerPermResult:
    """Parallel effective k, equal widths (Eq. 7.14, p. 224).

    Args:
        k_list: Per-layer permeabilities, md (> 0).
        h_list: Per-layer thicknesses, ft (> 0); same length as k_list.

    Returns:
        LayerPermResult with k_avg and total thickness / capacity.

    Raises:
        ValueError: empty lists, length mismatch, or any value <= 0.
    """
    _check_layer_list("k_list", k_list)
    _check_layer_list("h_list", h_list)
    if len(k_list) != len(h_list):
        raise ValueError(
            f"k_list and h_list must have same length "
            f"({len(k_list)} vs {len(h_list)})"
        )
    total_h = sum(h_list)
    capacity = sum(k_i * h_i for k_i, h_i in zip(k_list, h_list))
    return LayerPermResult(
        k_avg_md=capacity / total_h,
        total_length_or_thickness=total_h,
        total_capacity_md_ft=capacity,
    )


def radial_parallel(
    k_list: list[float], h_list: list[float],
) -> LayerPermResult:
    """Parallel radial effective k (p. 229). Same formula as linear_parallel.

    Args:
        k_list: Per-layer permeabilities, md (> 0).
        h_list: Per-layer thicknesses, ft (> 0).

    Returns:
        LayerPermResult.

    Raises:
        ValueError: empty lists, length mismatch, or any value <= 0.
    """
    return linear_parallel(k_list, h_list)


def radial_series(
    k_e: float, k_a: float, r_e: float, r_a: float, r_w: float,
) -> LayerPermResult:
    """Radial series effective k with altered inner zone (Eq. 7.24, p. 230).

    Args:
        k_e: Outer (unaltered) permeability, md (> 0).
        k_a: Inner (altered) permeability, md (> 0).
        r_e: Drainage radius, ft (> 0).
        r_a: Altered-zone outer radius, ft (> 0).
        r_w: Wellbore radius, ft (> 0).

    Returns:
        LayerPermResult with k_avg (effective k over the whole radial
        region) and total_length_or_thickness = ln(r_e/r_w) diagnostic.

    Raises:
        ValueError: any value <= 0, or radial ordering violated.
    """
    for name, v in [
        ("k_e", k_e), ("k_a", k_a), ("r_e", r_e),
        ("r_a", r_a), ("r_w", r_w),
    ]:
        if not (v > 0.0):
            raise ValueError(f"{name} must be > 0, got {v!r}")
    if not (r_e > r_a > r_w):
        raise ValueError(
            f"radial ordering requires r_e > r_a > r_w, got "
            f"r_e={r_e!r}, r_a={r_a!r}, r_w={r_w!r}"
        )
    ln_e_w = math.log(r_e / r_w)
    ln_e_a = math.log(r_e / r_a)
    ln_a_w = math.log(r_a / r_w)
    denom = k_a * ln_e_a + k_e * ln_a_w
    if denom <= 0.0:
        raise ValueError(
            f"denominator {denom!r} <= 0; check k_a, k_e positive"
        )
    k_avg = (k_e * k_a * ln_e_w) / denom
    return LayerPermResult(
        k_avg_md=k_avg,
        total_length_or_thickness=ln_e_w,
        total_capacity_md_ft=None,
    )
