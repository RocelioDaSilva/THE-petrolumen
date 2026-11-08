"""Two-stage partial water-drive gas recovery (Craft p. 78-82)."""
from __future__ import annotations
from dataclasses import dataclass

CUFT_PER_ACFT = 43560.0


@dataclass(frozen=True)
class TwoStageResult:
    g_init_scf: float
    gp_stage1_scf: float
    gp_stage2_scf: float
    gp_total_scf: float
    rf_total_pct: float


def two_stage_gas_recovery(
    phi_frac: float, Swi: float, Sgr: float,
    Bgi: float, Bg_ps: float, Bga_500: float,
    Vb_ac_ft: float,
) -> TwoStageResult:
    """Two-stage gas recovery (Craft Eq. 3.9 then 3.13).

    Args:
        phi_frac: Porosity, fraction (0, 1).
        Swi: Connate water, fraction [0, 1).
        Sgr: Residual gas saturation in water-invaded zone, [0, 1).
        Bgi: Bg at pi, cu ft/SCF (> 0).
        Bg_ps: Bg at stabilization ps, cu ft/SCF (> Bgi).
        Bga_500: Bg at abandonment (end of stage 1 depletion), cu ft/SCF
            (>= Bg_ps).
        Vb_ac_ft: Bulk volume, ac-ft (> 0).

    Returns:
        TwoStageResult.
    """
    if not (0.0 < phi_frac < 1.0):
        raise ValueError(f"phi_frac must be in (0, 1), got {phi_frac!r}")
    if not (0.0 <= Swi < 1.0):
        raise ValueError(f"Swi must be in [0, 1), got {Swi!r}")
    if not (0.0 <= Sgr < 1.0):
        raise ValueError(f"Sgr must be in [0, 1), got {Sgr!r}")
    if Swi + Sgr >= 1.0:
        raise ValueError(f"Swi + Sgr must be < 1")
    for n, v in [("Bgi", Bgi), ("Bg_ps", Bg_ps), ("Bga_500", Bga_500)]:
        if not (v > 0.0):
            raise ValueError(f"{n} must be > 0, got {v!r}")
    if not (Bg_ps >= Bgi):
        raise ValueError(f"Bg_ps must be >= Bgi")
    if not (Vb_ac_ft > 0.0):
        raise ValueError(f"Vb_ac_ft must be > 0")

    V_HC = CUFT_PER_ACFT * phi_frac * (1.0 - Swi)
    g_init = V_HC / Bgi
    g_init_scf = g_init * Vb_ac_ft
    # Stage 1: depletion from pi to ps (Eq. 3.9)
    gp1_per_acft = V_HC * (1.0 / Bgi - 1.0 / Bg_ps)
    gp1_scf = gp1_per_acft * Vb_ac_ft
    # Stage 2: complete water drive at ps (Eq. 3.13 with Bgi -> Bg_ps)
    gp2_per_acft = CUFT_PER_ACFT * phi_frac * (1.0 - Swi - Sgr) / Bg_ps
    gp2_scf = gp2_per_acft * Vb_ac_ft
    gp_total = gp1_scf + gp2_scf
    rf_pct = 100.0 * gp_total / g_init_scf
    return TwoStageResult(
        g_init_scf=g_init_scf,
        gp_stage1_scf=gp1_scf,
        gp_stage2_scf=gp2_scf,
        gp_total_scf=gp_total,
        rf_total_pct=rf_pct,
    )
