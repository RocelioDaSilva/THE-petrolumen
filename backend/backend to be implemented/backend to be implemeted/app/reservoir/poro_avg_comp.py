"""Porosity-averaged rock-fluid compressibility.

Source: Chin, W.C. (2016), Reservoir Engineering in Modern Oilfields,
Wiley, Ch. 3, p. 65: c_eff = phi*c_fluid + (1-phi)*c_rock.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PoroAvgCompResult:
    c_eff_psi_inv: float
    fluid_fraction: float
    rock_fraction: float


def poro_avg_compressibility(
    phi: float, c_fluid_psi_inv: float, c_rock_psi_inv: float,
) -> PoroAvgCompResult:
    """c_eff = phi*c_fluid + (1-phi)*c_rock (Chin p. 65)."""
    if not (0.0 < phi < 1.0):
        raise ValueError(f"phi must be in (0, 1), got {phi!r}")
    if not (c_fluid_psi_inv >= 0.0):
        raise ValueError(
            f"c_fluid_psi_inv must be >= 0, got {c_fluid_psi_inv!r}"
        )
    if not (c_rock_psi_inv >= 0.0):
        raise ValueError(
            f"c_rock_psi_inv must be >= 0, got {c_rock_psi_inv!r}"
        )
    c_fluid_part = phi * c_fluid_psi_inv
    c_rock_part = (1.0 - phi) * c_rock_psi_inv
    c_eff = c_fluid_part + c_rock_part
    return PoroAvgCompResult(
        c_eff_psi_inv=c_eff,
        fluid_fraction=c_fluid_part / c_eff if c_eff > 0 else 0.0,
        rock_fraction=c_rock_part / c_eff if c_eff > 0 else 0.0,
    )
