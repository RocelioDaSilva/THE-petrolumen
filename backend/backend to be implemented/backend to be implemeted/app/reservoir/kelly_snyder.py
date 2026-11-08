"""Kelly-Snyder immobile-gas depletion (Craft Eqs. 5.10, 5.16)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class KSPoint:
    p_psia: float
    Bo_bbl_stb: float
    Bt_bbl_stb: float
    Bg_bbl_scf: float
    Rso_scf_stb: float


@dataclass(frozen=True)
class KSRow:
    p_psia: float
    Np_stb: float
    Sg: float
    Np_over_N: float


@dataclass(frozen=True)
class KellySnyderResult:
    N_stb: float
    rows: tuple[KSRow, ...]
    stopped_at_critical: bool


def kelly_snyder(
    N_stb: float, Swi: float, Sgc: float, pvt: list[KSPoint],
) -> KellySnyderResult:
    """Kelly-Snyder immobile-gas prediction (Craft Eqs. 5.10, 5.16).

    Args:
        N_stb: Initial oil in place, STB (> 0).
        Swi: Connate water, fraction [0, 1).
        Sgc: Critical gas saturation, fraction (0, 1).
        pvt: Pressure grid from pb downward; >= 2 points; each with
            Bo, Bt, Bg, Rso.

    Returns:
        KellySnyderResult with one row per step until Sg >= Sgc.

    Raises:
        ValueError: any input out of physical range.
    """
    if not (N_stb > 0.0):
        raise ValueError(f"N_stb must be > 0, got {N_stb!r}")
    if not (0.0 <= Swi < 1.0):
        raise ValueError(f"Swi must be in [0, 1), got {Swi!r}")
    if not (0.0 < Sgc < 1.0):
        raise ValueError(f"Sgc must be in (0, 1), got {Sgc!r}")
    if len(pvt) < 2:
        raise ValueError(f"pvt must have >= 2 points, got {len(pvt)}")
    for i, pt in enumerate(pvt):
        for name, v in [
            ("p", pt.p_psia), ("Bo", pt.Bo_bbl_stb), ("Bt", pt.Bt_bbl_stb),
            ("Bg", pt.Bg_bbl_scf),
        ]:
            if not (v > 0.0):
                raise ValueError(f"pvt[{i}].{name} must be > 0: {v!r}")
        if not (pt.Rso_scf_stb >= 0.0):
            raise ValueError(f"pvt[{i}].Rso must be >= 0")
        if i > 0 and pt.p_psia >= pvt[i - 1].p_psia:
            raise ValueError(
                f"pvt pressures must strictly decrease at index {i}"
            )

    Bti = pvt[0].Bt_bbl_stb
    Rsoi = pvt[0].Rso_scf_stb
    Bti_bo = pvt[0].Bo_bbl_stb

    rows: list[KSRow] = []
    stopped = False
    for k in range(1, len(pvt)):
        pt = pvt[k]
        Rp = pt.Rso_scf_stb            # immobile-gas assumption
        tp = pt.Bt_bbl_stb + (Rp - Rsoi) * pt.Bg_bbl_scf
        dNp_over_N = (pt.Bt_bbl_stb - Bti) / tp if tp > 0.0 else 0.0
        Np = dNp_over_N * N_stb
        SL = Swi + (1.0 - Swi) * (1.0 - dNp_over_N) * (
            pt.Bo_bbl_stb / Bti_bo
        )
        Sg = 1.0 - SL
        rows.append(KSRow(p_psia=pt.p_psia, Np_stb=Np,
                          Sg=Sg, Np_over_N=dNp_over_N))
        if Sg >= Sgc:
            stopped = True
            break
    return KellySnyderResult(
        N_stb=N_stb, rows=tuple(rows), stopped_at_critical=stopped,
    )
