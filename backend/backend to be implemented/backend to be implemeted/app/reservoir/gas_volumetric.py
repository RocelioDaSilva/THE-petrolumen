"""Volumetric gas in place and unit recovery.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 3, Sec. 2-4, pp. 70-82, Eqs. (3.1), (3.7), (3.9)-(3.14),
Example 3.2 (p. 81).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# Eq. (3.1), p. 70: cu ft per acre-foot
CUFT_PER_ACFT = 43560.0

Mechanism = Literal["depletion", "partial_water_drive", "complete_water_drive"]


@dataclass(frozen=True)
class GasVolumetricResult:
    g_unit_scf_per_acft: float
    dg_unit_scf_per_acft: float
    recovery_factor_pct: float
    g_total_scf: float | None
    reserve_total_scf: float | None
    mechanism: Mechanism


def gas_volumetric(
    phi_frac: float,
    Swi: float,
    Bgi: float,
    Bga: float,
    mechanism: Mechanism,
    Sgr: float | None = None,
    Vb_ac_ft: float | None = None,
    A_acres: float | None = None,
    h_ft: float | None = None,
) -> GasVolumetricResult:
    """Volumetric gas in place and unit recovery (Craft Eqs. 3.1-3.14).

    Computes unit-basis gas in place (Eq. 3.7), unit-basis recovery by
    the selected mechanism (Eqs. 3.9/3.11/3.13), and the recovery
    factor (Eqs. 3.10/3.12/3.14). Optionally computes the total field
    gas in place and reserve from bulk volume Vb or A*h.

    Args:
        phi_frac: Average porosity, fraction (0, 1).
        Swi: Initial connate water, fraction [0, 1).
        Bgi: Initial gas FVF, cu ft/SCF (> 0).
        Bga: Gas FVF at abandonment, cu ft/SCF (> Bgi).
        mechanism: 'depletion', 'partial_water_drive', or
            'complete_water_drive'.
        Sgr: Residual gas saturation after water displacement,
            fraction [0, 1). Required for water-drive mechanisms;
            must satisfy Swi + Sgr < 1.
        Vb_ac_ft: Bulk reservoir volume, ac-ft (> 0). Optional.
        A_acres: Areal extent, acres (> 0). Optional; used with h_ft
            if Vb_ac_ft not provided.
        h_ft: Net thickness, ft (> 0). Optional.

    Returns:
        GasVolumetricResult with unit and total quantities.

    Raises:
        ValueError: any input out of physical range or mechanism
            inconsistent with provided saturations.
    """
    if not (0.0 < phi_frac < 1.0):
        raise ValueError(f"phi_frac must be in (0, 1), got {phi_frac!r}")
    if not (0.0 <= Swi < 1.0):
        raise ValueError(f"Swi must be in [0, 1), got {Swi!r}")
    if not (Bgi > 0.0):
        raise ValueError(f"Bgi must be > 0, got {Bgi!r}")
    if not (Bga > 0.0):
        raise ValueError(f"Bga must be > 0, got {Bga!r}")
    if not (Bga > Bgi):
        raise ValueError(
            f"Bga ({Bga!r}) must exceed Bgi ({Bgi!r}); "
            "otherwise no gas can be produced by expansion."
        )
    if mechanism not in ("depletion", "partial_water_drive",
                         "complete_water_drive"):
        raise ValueError(
            f"mechanism must be 'depletion', 'partial_water_drive', "
            f"or 'complete_water_drive', got {mechanism!r}"
        )
    if mechanism in ("partial_water_drive", "complete_water_drive"):
        if Sgr is None:
            raise ValueError(
                f"Sgr is required for mechanism={mechanism!r}"
            )
        if not (0.0 <= Sgr < 1.0):
            raise ValueError(f"Sgr must be in [0, 1), got {Sgr!r}")
        if Swi + Sgr >= 1.0:
            raise ValueError(
                f"Swi + Sgr = {Swi + Sgr!r} must be < 1 "
                "(hydrocarbon pore space is non-negative)"
            )

    # Eq. (3.7): unit-basis initial gas in place
    g_unit = CUFT_PER_ACFT * phi_frac * (1.0 - Swi) / Bgi

    # Unit recovery and RF per mechanism
    if mechanism == "depletion":
        # Eq. (3.9)
        dg_unit = (
            CUFT_PER_ACFT * phi_frac * (1.0 - Swi)
            * (1.0 / Bgi - 1.0 / Bga)
        )
        # Eq. (3.10)
        rf = 100.0 * (1.0 - Bgi / Bga)
    elif mechanism == "partial_water_drive":
        assert Sgr is not None  # validated above
        # Eq. (3.11)
        dg_unit = (
            CUFT_PER_ACFT * phi_frac
            * ((1.0 - Swi) / Bgi - Sgr / Bga)
        )
        # Eq. (3.12)
        base = (1.0 - Swi) / Bgi
        rf = 100.0 * ((base - Sgr / Bga) / base)
    else:  # complete_water_drive
        assert Sgr is not None
        # Eq. (3.13)
        dg_unit = (
            CUFT_PER_ACFT * phi_frac * (1.0 - Swi - Sgr) / Bgi
        )
        # Eq. (3.14)
        rf = 100.0 * (1.0 - Swi - Sgr) / (1.0 - Swi)

    # Optional total field quantities
    g_total: float | None = None
    reserve_total: float | None = None
    Vb = None
    if Vb_ac_ft is not None:
        if not (Vb_ac_ft > 0.0):
            raise ValueError(
                f"Vb_ac_ft must be > 0, got {Vb_ac_ft!r}"
            )
        Vb = Vb_ac_ft
    elif A_acres is not None and h_ft is not None:
        if not (A_acres > 0.0):
            raise ValueError(f"A_acres must be > 0, got {A_acres!r}")
        if not (h_ft > 0.0):
            raise ValueError(f"h_ft must be > 0, got {h_ft!r}")
        Vb = A_acres * h_ft
    if Vb is not None:
        g_total = g_unit * Vb
        reserve_total = dg_unit * Vb

    return GasVolumetricResult(
        g_unit_scf_per_acft=g_unit,
        dg_unit_scf_per_acft=dg_unit,
        recovery_factor_pct=rf,
        g_total_scf=g_total,
        reserve_total_scf=reserve_total,
        mechanism=mechanism,
    )
