"""Gas reservoir abandonment pressure (Craft p. 99-100, Fig 3.12)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class AbandonmentResult:
    G_scf: float
    Gp_at_abandonment_scf: float
    RF_at_abandonment: float
    pz_ratio: float
    method: str


def abandonment_gas(
    G_scf: float, pi_over_zi: float, pa_over_za: float,
    water_drive_Gpa_scf: float | None = None,
) -> AbandonmentResult:
    """Compute abandonment Gp and RF.

    Args:
        G_scf: Initial gas in place, SCF (> 0).
        pi_over_zi: Initial p/z, psia (> 0).
        pa_over_za: Abandonment p/z, psia (> 0, < pi_over_zi).
        water_drive_Gpa_scf: If supplied, use this as Gp at
            abandonment instead of the volumetric formula (for
            water-drive reservoirs; G_scf used only for RF
            denominator).

    Returns:
        AbandonmentResult.

    Raises:
        ValueError: any input out of physical range.
    """
    if not (G_scf > 0.0):
        raise ValueError(f"G_scf must be > 0, got {G_scf!r}")
    if not (pi_over_zi > 0.0):
        raise ValueError(f"pi_over_zi must be > 0, got {pi_over_zi!r}")
    if not (pa_over_za > 0.0):
        raise ValueError(f"pa_over_za must be > 0, got {pa_over_za!r}")
    if pa_over_za >= pi_over_zi:
        raise ValueError(
            f"pa/za ({pa_over_za!r}) must be < pi/zi ({pi_over_zi!r})"
        )
    pz_ratio = pa_over_za / pi_over_zi
    if water_drive_Gpa_scf is not None:
        if water_drive_Gpa_scf < 0.0:
            raise ValueError("water_drive_Gpa_scf must be >= 0")
        if water_drive_Gpa_scf > G_scf:
            raise ValueError("water_drive_Gpa_scf cannot exceed G")
        gpa = water_drive_Gpa_scf
        method = "water_drive_supplied"
    else:
        gpa = G_scf * (1.0 - pz_ratio)
        method = "volumetric"
    rf = gpa / G_scf
    return AbandonmentResult(
        G_scf=G_scf, Gp_at_abandonment_scf=gpa,
        RF_at_abandonment=rf, pz_ratio=pz_ratio, method=method,
    )
