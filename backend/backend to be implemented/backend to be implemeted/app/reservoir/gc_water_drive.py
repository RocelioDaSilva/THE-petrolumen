"""Gas-condensate active water-drive recovery (Craft Eq. 4.4, p. 136)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class GCWaterDriveResult:
    recovery: float
    out_of_physical_range: bool


def gc_water_drive_recovery(
    Swi: float, Sgr: float, F_invaded: float,
) -> GCWaterDriveResult:
    """Return fractional recovery under active water drive.

    Args:
        Swi: Initial connate water, fraction [0, 1).
        Sgr: Residual gas saturation in water-invaded zone, [0, 1).
        F_invaded: Fraction of reservoir invaded by water at
            abandonment, [0, 1].

    Returns:
        GCWaterDriveResult.

    Raises:
        ValueError: any input out of physical range.
    """
    if not (0.0 <= Swi < 1.0):
        raise ValueError(f"Swi must be in [0, 1), got {Swi!r}")
    if not (0.0 <= Sgr < 1.0):
        raise ValueError(f"Sgr must be in [0, 1), got {Sgr!r}")
    if Swi + Sgr >= 1.0:
        raise ValueError(
            f"Swi + Sgr = {Swi + Sgr!r} must be < 1 "
            "(no hydrocarbon pore space)"
        )
    if not (0.0 <= F_invaded <= 1.0):
        raise ValueError(
            f"F_invaded must be in [0, 1], got {F_invaded!r}"
        )
    rec = (1.0 - Swi - Sgr) * F_invaded / (1.0 - Swi)
    return GCWaterDriveResult(
        recovery=rec,
        out_of_physical_range=not (0.0 <= rec <= 1.0),
    )
