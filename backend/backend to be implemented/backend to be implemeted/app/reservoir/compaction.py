"""Compaction porosity correction, Chin (2016) p. 45.

phi_actual(p) = phi_baseline * (1 + a*p), with a usually negative
for compaction (secondary compressibility).
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class CompactionResult:
    phi_actual: float
    delta_phi: float
    compaction_compressibility_per_psi: float


def compaction_porosity(
    phi_baseline: float, a_per_psi: float, p_psia: float,
) -> CompactionResult:
    """phi_actual(p) = phi_baseline * (1 + a*p) (Chin p. 45)."""
    if not (0.0 < phi_baseline < 1.0):
        raise ValueError(
            f"phi_baseline must be in (0, 1), got {phi_baseline!r}"
        )
    if not (p_psia > 0.0):
        raise ValueError(f"p_psia must be > 0, got {p_psia!r}")
    phi_actual = phi_baseline * (1.0 + a_per_psi * p_psia)
    if phi_actual <= 0.0:
        raise ValueError(
            f"phi_actual = {phi_actual!r} <= 0 at p={p_psia} psia "
            f"with a={a_per_psi} 1/psi; compaction model is in the "
            "non-physical regime."
        )
    delta_phi = phi_actual - phi_baseline
    return CompactionResult(
        phi_actual=phi_actual,
        delta_phi=delta_phi,
        compaction_compressibility_per_psi=-a_per_psi,
    )
