"""Lean-gas cycling recovery efficiency (Craft p. 135)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class CyclingRecoveryResult:
    E_total: float
    sens_E_d: float
    sens_E_a: float
    sens_E_s: float


def cycling_recovery(
    E_d: float, E_a: float, E_s: float,
) -> CyclingRecoveryResult:
    """Total cycling recovery = E_d * E_a * E_s (Craft p. 135).

    Args:
        E_d: Microscopic displacement efficiency, [0, 1].
        E_a: Areal sweep efficiency, [0, 1].
        E_s: Permeability-stratification factor, [0, 1].

    Returns:
        CyclingRecoveryResult with total and per-factor sensitivities.

    Raises:
        ValueError: any input outside [0, 1].
    """
    for n, v in [("E_d", E_d), ("E_a", E_a), ("E_s", E_s)]:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"{n} must be in [0, 1], got {v!r}")
    E = E_d * E_a * E_s
    return CyclingRecoveryResult(
        E_total=E,
        sens_E_d=E_a * E_s,
        sens_E_a=E_d * E_s,
        sens_E_s=E_d * E_a,
    )
