"""Anisotropy-weighted effective permeability (Chin 2016 Ch 2, p. 46).

Combines horizontal (arithmetic) and vertical (harmonic) averages into
a single (kh_eff, kv_eff, kappa = kv/kh) triple for anisotropic radial
flow, pseudosteady, or aquifer models.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnisotropyWeightedResult:
    kh_eff_md: float
    kv_eff_md: float
    kappa: float
    total_h_ft: float
    per_layer_kh_contribution: tuple[float, ...]
    per_layer_kv_resistance: tuple[float, ...]


def anisotropy_weighted_permeability(
    layers: list[tuple[float, float, float]],
) -> AnisotropyWeightedResult:
    """Anisotropy-weighted (kh, kv, kappa) for a layered reservoir.

    Args:
        layers: List of (k_h_md, k_v_md, h_ft), each > 0.

    Returns:
        AnisotropyWeightedResult.

    Raises:
        ValueError: empty list or any value <= 0.
    """
    if len(layers) == 0:
        raise ValueError("layers list must be non-empty")
    kh_contrib: list[float] = []
    kv_resist: list[float] = []
    for i, (kh, kv, h) in enumerate(layers):
        if not (kh > 0.0):
            raise ValueError(
                f"layers[{i}].kh_md must be > 0, got {kh!r}"
            )
        if not (kv > 0.0):
            raise ValueError(
                f"layers[{i}].kv_md must be > 0, got {kv!r}"
            )
        if not (h > 0.0):
            raise ValueError(
                f"layers[{i}].h_ft must be > 0, got {h!r}"
            )
        kh_contrib.append(kh * h)
        kv_resist.append(h / kv)

    total_h = sum(h for (_, _, h) in layers)
    if total_h <= 0.0:
        raise ValueError("total thickness must be > 0")

    kh_eff = sum(kh_contrib) / total_h
    kv_eff = total_h / sum(kv_resist)
    kappa = kv_eff / kh_eff

    return AnisotropyWeightedResult(
        kh_eff_md=kh_eff,
        kv_eff_md=kv_eff,
        kappa=kappa,
        total_h_ft=total_h,
        per_layer_kh_contribution=tuple(kh_contrib),
        per_layer_kv_resistance=tuple(kv_resist),
    )
