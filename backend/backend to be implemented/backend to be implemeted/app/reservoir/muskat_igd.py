"""Muskat internal gas drive (Craft Eqs. 9.27-9.38, pp. 362-365)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class MuskatPVT:
    p_psia: float
    Bo: float
    Bg: float
    Rso: float
    mu_o: float
    mu_g: float


@dataclass(frozen=True)
class MuskatRow:
    p_psia: float
    So: float
    Np_stb: float
    dSo_dp: float


@dataclass(frozen=True)
class MuskatResult:
    N_stb: float
    rows: tuple[MuskatRow, ...]


def _interp_rp(SL: float, table: list[tuple[float, float]]) -> float:
    if SL <= table[0][0]:
        return table[0][1]
    if SL >= table[-1][0]:
        return table[-1][1]
    for i in range(len(table) - 1):
        if table[i][0] <= SL <= table[i + 1][0]:
            f = (SL - table[i][0]) / (table[i + 1][0] - table[i][0])
            return table[i][1] + f * (table[i + 1][1] - table[i][1])
    return table[-1][1]


def muskat_igd(
    N_stb: float, Swi: float,
    pvt: list[MuskatPVT], rel_perm: list[tuple[float, float]],
) -> MuskatResult:
    """Muskat IGD prediction (Craft Eqs. 9.27-9.38).

    Args:
        N_stb: Initial oil in place, STB (> 0).
        Swi: Connate water, fraction [0, 1).
        pvt: Pressure grid from pi downward, >= 2 points.
        rel_perm: (SL, kg/ko) pairs, strictly increasing in SL.

    Returns:
        MuskatResult with one row per pressure step.

    Raises:
        ValueError: any input out of physical range.
    """
    if not (N_stb > 0.0):
        raise ValueError(f"N_stb must be > 0, got {N_stb!r}")
    if not (0.0 <= Swi < 1.0):
        raise ValueError(f"Swi must be in [0, 1), got {Swi!r}")
    if len(pvt) < 2:
        raise ValueError("pvt must have >= 2 points")
    for i, pt in enumerate(pvt):
        for nm, v in [("p", pt.p_psia), ("Bo", pt.Bo), ("Bg", pt.Bg),
                      ("mu_o", pt.mu_o), ("mu_g", pt.mu_g)]:
            if not (v > 0.0):
                raise ValueError(f"pvt[{i}].{nm} must be > 0")
        if i > 0 and pt.p_psia >= pvt[i - 1].p_psia:
            raise ValueError(f"pvt pressures must decrease at index {i}")
    if len(rel_perm) < 2:
        raise ValueError("rel_perm must have >= 2 points")

    Boi = pvt[0].Bo
    rows: list[MuskatRow] = []
    So = 1.0 - Swi
    Np_prev = 0.0

    for k in range(1, len(pvt)):
        p1, p2 = pvt[k - 1], pvt[k]
        dp = p1.p_psia - p2.p_psia
        # Finite-difference derivatives (backward over the step)
        dRso_dp = (p2.Rso - p1.Rso) / (p2.p_psia - p1.p_psia)
        dBo_dp = (p2.Bo - p1.Bo) / (p2.p_psia - p1.p_psia)
        dBg_dp = (p2.Bg - p1.Bg) / (p2.p_psia - p1.p_psia)
        # Evaluate at midpoint
        Bg_m = 0.5 * (p1.Bg + p2.Bg)
        Bo_m = 0.5 * (p1.Bo + p2.Bo)
        mu_o_m = 0.5 * (p1.mu_o + p2.mu_o)
        mu_g_m = 0.5 * (p1.mu_g + p2.mu_g)
        X = Bg_m / Bo_m * dRso_dp
        Y = 1.0 / Bo_m * (mu_o_m / mu_g_m) * dBo_dp
        Z = 1.0 / Bg_m * dBg_dp
        SL = So + Swi
        kg_ko = _interp_rp(SL, rel_perm)
        num = So * X + So * kg_ko * Y - (1.0 - So - Swi) * Z
        den = 1.0 + kg_ko * (mu_o_m / mu_g_m)
        dSo_dp = num / den if den > 0.0 else 0.0
        # Eq. (9.38): negative because So decreases as p decreases;
        # here dp > 0 (decrease), so So_new = So - dp * dSo_dp
        So_new = So - dp * dSo_dp
        # Convert to Np via Eq. (9.57)
        frac = 1.0 - (So_new / (1.0 - Swi)) * (Boi / p2.Bo)
        Np = frac * N_stb
        rows.append(MuskatRow(p_psia=p2.p_psia, So=So_new,
                              Np_stb=Np, dSo_dp=dSo_dp))
        So = So_new
        Np_prev = Np

    return MuskatResult(N_stb=N_stb, rows=tuple(rows))
