"""Gas-condensate volumetric depletion performance.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 4, Sec. 3, pp. 118-127, Example 4.3, Tables 4.4-4.6.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SCF_PER_LBMOL = 379.4       # SCF/lbmol at 14.7 psia, 60 F
LB_PER_GAL = 8.337          # lb/gal (water reference)
LBMOL_PER_MSCF = 0.3794     # 1000 SCF / 379.4 SCF/lbmol / 1000
CUFT_PER_ACFT = 43560.0
R_PRIME = 10.73
GAL_PER_BBL = 42.0
K_1000 = 1000.0

RECOVERABLE_COMPS = ("C4", "C5", "C6", "C7plus")


@dataclass(frozen=True)
class GCDepletionIncrement:
    p_end_psia: float
    V_produced_cc: float
    z: float
    comp: dict[str, float]


@dataclass(frozen=True)
class GCDepletionRow:
    p_end_psia: float
    dV_reservoir_cuft_per_acft: float
    dGp_mmscf_per_acft: float
    dResidue_mmscf_per_acft: float
    dLiquid_bbl_per_acft: float
    gor_scf_per_bbl: float
    cum_Gp_mmscf_per_acft: float
    cum_residue_mmscf_per_acft: float
    cum_liquid_bbl_per_acft: float
    gross_gas_recovery_pct: float
    residue_recovery_pct: float
    liquid_recovery_pct: float


@dataclass(frozen=True)
class GCDepletionResult:
    g_initial_mmscf_per_acft: float
    rows: tuple[GCDepletionRow, ...]
    liquid_initial_bbl_per_acft: float
    late_time_zero_liquid: bool


def _gal_per_mscf(mw: float, sg: float) -> float:
    """gal/MSCF from component MW and specific gravity."""
    return mw / (LBMOL_PER_MSCF * LB_PER_GAL * sg)


def gas_condensate_depletion(
    pi_psia: float,
    T_F: float,
    phi_frac: float,
    Swi_frac: float,
    z_initial: float,
    cell_volume_cc: float,
    increments: list[GCDepletionIncrement],
    initial_comp: dict[str, float],
    mw_per_comp: dict[str, float],
    sg_per_comp: dict[str, float],
    rec_C4: float = 0.25,
    rec_C5: float = 0.50,
    rec_C6: float = 0.75,
    rec_C7plus: float = 1.00,
) -> GCDepletionResult:
    """Volumetric depletion performance from PVT cell data.

    Implements the step-by-step calculation of Craft, Hawkins, Terry
    (1991), Ch. 4, Sec. 3, pp. 118-127 (Example 4.3). Each increment
    consumes produced gas volume, PVT-cell z-factor, and produced-gas
    composition; the routine accumulates per-increment volumes,
    recoveries, and GOR.

    Args:
        pi_psia: Initial pressure (dew point), psia (>0).
        T_F: Reservoir temperature, deg F (> -459.67).
        phi_frac: Porosity, fraction (0,1).
        Swi_frac: Connate water, fraction [0,1).
        z_initial: z-factor at pi and T (>0).
        cell_volume_cc: Initial PVT cell volume, cu cm (>0).
        increments: list of GCDepletionIncrement, non-empty;
            pressures must be strictly decreasing.
        initial_comp: initial reservoir fluid comp (dict);
            sums to 1.0 within 1e-3.
        mw_per_comp: dict of component MW (g/mol or lbm/lbmol).
        sg_per_comp: dict of component SG (water=1).
        rec_C4, rec_C5, rec_C6, rec_C7plus: recovery fractions.

    Returns:
        GCDepletionResult.

    Raises:
        ValueError: invalid input, non-decreasing pressures, initial
            composition not summing to 1, or missing component data.
    """
    # Validations
    if not (pi_psia > 0.0):
        raise ValueError(f"pi_psia must be > 0, got {pi_psia!r}")
    if not (T_F > -459.67):
        raise ValueError(f"T_F must be > -459.67, got {T_F!r}")
    if not (0.0 < phi_frac < 1.0):
        raise ValueError(f"phi_frac must be in (0,1), got {phi_frac!r}")
    if not (0.0 <= Swi_frac < 1.0):
        raise ValueError(f"Swi_frac must be in [0,1), got {Swi_frac!r}")
    if not (z_initial > 0.0):
        raise ValueError(f"z_initial must be > 0, got {z_initial!r}")
    if not (cell_volume_cc > 0.0):
        raise ValueError(
            f"cell_volume_cc must be > 0, got {cell_volume_cc!r}"
        )
    if not increments:
        raise ValueError("increments list must be non-empty")

    for k, inc in enumerate(increments):
        if not (inc.p_end_psia > 0.0):
            raise ValueError(
                f"increments[{k}].p_end_psia must be > 0"
            )
        if not (inc.V_produced_cc > 0.0):
            raise ValueError(
                f"increments[{k}].V_produced_cc must be > 0"
            )
        if not (inc.z > 0.0):
            raise ValueError(f"increments[{k}].z must be > 0")
        if k > 0 and not (inc.p_end_psia < increments[k - 1].p_end_psia):
            raise ValueError(
                f"increments[{k}].p_end_psia = {inc.p_end_psia!r} "
                f"not strictly below increments[{k-1}].p_end_psia"
            )

    total_comp = sum(initial_comp.values())
    if not (abs(total_comp - 1.0) <= 1e-3):
        raise ValueError(
            f"initial_comp sums to {total_comp!r}, expected 1.0 (1e-3)"
        )

    for key in RECOVERABLE_COMPS:
        if key not in mw_per_comp:
            raise ValueError(f"mw_per_comp missing key {key!r}")
        if key not in sg_per_comp:
            raise ValueError(f"sg_per_comp missing key {key!r}")
        if not (mw_per_comp[key] > 0.0):
            raise ValueError(f"mw_per_comp[{key!r}] must be > 0")
        if not (0.0 < sg_per_comp[key] < 2.0):
            raise ValueError(f"sg_per_comp[{key!r}] must be in (0,2)")

    for r_name, r_val in [
        ("rec_C4", rec_C4), ("rec_C5", rec_C5),
        ("rec_C6", rec_C6), ("rec_C7plus", rec_C7plus),
    ]:
        if not (0.0 <= r_val <= 1.0):
            raise ValueError(f"{r_name} must be in [0,1], got {r_val!r}")

    T_R = T_F + 459.67
    V_HC = CUFT_PER_ACFT * phi_frac * (1.0 - Swi_frac)

    g_initial = (
        SCF_PER_LBMOL * pi_psia * V_HC
        / (K_1000 * z_initial * R_PRIME * T_R)
    )

    rec_map = {
        "C4": rec_C4, "C5": rec_C5, "C6": rec_C6, "C7plus": rec_C7plus,
    }
    gal_per_comp = {
        k: _gal_per_mscf(mw_per_comp[k], sg_per_comp[k])
        for k in RECOVERABLE_COMPS
    }

    # Initial recoverable liquid per MSCF of gross gas
    gal_per_mscf_initial = sum(
        rec_map[k] * initial_comp.get(k, 0.0) * gal_per_comp[k]
        for k in RECOVERABLE_COMPS
    )
    liquid_initial = gal_per_mscf_initial * g_initial / GAL_PER_BBL

    rows: list[GCDepletionRow] = []
    cum_Gp = 0.0
    cum_residue = 0.0
    cum_liquid = 0.0
    late_time_zero_liquid = False

    for inc in increments:
        dV_res = V_HC * inc.V_produced_cc / cell_volume_cc
        dGp = (
            SCF_PER_LBMOL * inc.p_end_psia * dV_res
            / (K_1000 * inc.z * R_PRIME * T_R)
        )
        f_L = sum(
            rec_map[k] * inc.comp.get(k, 0.0)
            for k in RECOVERABLE_COMPS
        )
        gal_per_mscf_inc = sum(
            rec_map[k] * inc.comp.get(k, 0.0) * gal_per_comp[k]
            for k in RECOVERABLE_COMPS
        )
        dGal = dGp * gal_per_mscf_inc
        dLiquid = dGal / GAL_PER_BBL
        dResidue = (1.0 - f_L) * dGp

        if dLiquid < 1.0e-12:
            gor = float("inf")
            late_time_zero_liquid = True
        else:
            gor = dResidue * K_1000 / dLiquid

        cum_Gp += dGp
        cum_residue += dResidue
        cum_liquid += dLiquid

        gross_pct = 100.0 * cum_Gp / g_initial
        residue_pct = (
            100.0 * cum_residue / (g_initial * (1.0 - _initial_fl(
                initial_comp, rec_map)))
        )
        liquid_pct = (
            100.0 * cum_liquid / liquid_initial
            if liquid_initial > 0.0 else 0.0
        )

        rows.append(GCDepletionRow(
            p_end_psia=inc.p_end_psia,
            dV_reservoir_cuft_per_acft=dV_res,
            dGp_mmscf_per_acft=dGp,
            dResidue_mmscf_per_acft=dResidue,
            dLiquid_bbl_per_acft=dLiquid,
            gor_scf_per_bbl=gor,
            cum_Gp_mmscf_per_acft=cum_Gp,
            cum_residue_mmscf_per_acft=cum_residue,
            cum_liquid_bbl_per_acft=cum_liquid,
            gross_gas_recovery_pct=gross_pct,
            residue_recovery_pct=residue_pct,
            liquid_recovery_pct=liquid_pct,
        ))

    return GCDepletionResult(
        g_initial_mmscf_per_acft=g_initial,
        rows=tuple(rows),
        liquid_initial_bbl_per_acft=liquid_initial,
        late_time_zero_liquid=late_time_zero_liquid,
    )


def _initial_fl(
    initial_comp: dict[str, float], rec_map: dict[str, float]
) -> float:
    return sum(rec_map[k] * initial_comp.get(k, 0.0)
               for k in RECOVERABLE_COMPS)
