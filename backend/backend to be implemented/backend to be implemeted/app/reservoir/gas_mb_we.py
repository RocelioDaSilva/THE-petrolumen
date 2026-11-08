"""Water influx and residual Sg from gas MB (Craft Ex. 3.4, pp. 87-88)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class GasMBWeResult:
    G_scf: float
    We_cuft: float
    Sw_invaded: float
    Sgr_invaded: float
    out_of_physical_range: bool


def gas_mb_we(
    Vb_cuft: float, phi: float, Swi: float,
    Bgi: float, Bgf: float,
    Gp_scf: float, Wp_bbl: float, Bw: float,
    Vb_invaded_cuft: float,
) -> GasMBWeResult:
    """We and Sgr from gas MB + water-volumes (Craft Ex. 3.4).

    Args:
        Vb_cuft: Total bulk volume, cu ft (> 0).
        phi: Porosity, fraction (0, 1).
        Swi: Initial water saturation, [0, 1).
        Bgi: Initial gas FVF, cu ft/SCF (> 0).
        Bgf: Current gas FVF, cu ft/SCF (> Bgi).
        Gp_scf: Cumulative gas production, SCF (>= 0).
        Wp_bbl: Cumulative water production, bbl (>= 0).
        Bw: Water FVF, bbl/STB (> 0).
        Vb_invaded_cuft: Bulk volume invaded by water, cu ft (> 0).

    Returns:
        GasMBWeResult.

    Raises:
        ValueError: any input out of range or We < 0.
    """
    for n, v in [("Vb_cuft", Vb_cuft), ("phi", phi), ("Bgi", Bgi),
                 ("Bgf", Bgf), ("Bw", Bw), ("Vb_invaded_cuft", Vb_invaded_cuft)]:
        if not (v > 0.0):
            raise ValueError(f"{n} must be > 0, got {v!r}")
    if not (0.0 <= Swi < 1.0):
        raise ValueError(f"Swi must be in [0, 1), got {Swi!r}")
    if not (Bgf > Bgi):
        raise ValueError("Bgf must exceed Bgi")
    if Gp_scf < 0.0:
        raise ValueError("Gp_scf must be >= 0")
    if Wp_bbl < 0.0:
        raise ValueError("Wp_bbl must be >= 0")

    Vp_total = Vb_cuft * phi * (1.0 - Swi)
    G = Vp_total / Bgi
    # Eq. (3.15) rearranged
    We_cuft = Gp_scf * Bgf + Wp_bbl * 5.615 * Bw - G * (Bgf - Bgi)
    if We_cuft < 0.0:
        raise ValueError(
            f"Computed We = {We_cuft!r} cu ft < 0; check G, Bgi, Bgf, "
            "Gp, Wp."
        )
    Vp_inv = Vb_invaded_cuft * phi
    V_w_initial = Vb_cuft * phi * Swi
    Sw = (V_w_initial + We_cuft - Wp_bbl * 5.615 * Bw) / Vp_inv
    Sgr = 1.0 - Sw
    return GasMBWeResult(
        G_scf=G, We_cuft=We_cuft,
        Sw_invaded=Sw, Sgr_invaded=Sgr,
        out_of_physical_range=not (0.0 <= Sw <= 1.0),
    )
