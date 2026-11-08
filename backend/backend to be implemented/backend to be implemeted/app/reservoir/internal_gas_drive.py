"""Internal gas drive (Tarner / Tracy form).

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 9, Sec. 3.3, pp. 360-375, Eqs. (9.40), (9.33), (9.51),
(9.53), (9.56), Example 9.1 (pp. 370-375).

Muskat (Eqs. 9.27-9.34) and Schilthuis (Eqs. 9.39-9.46) methods give
equivalent results (book p. 375) but Tarner-Tracy is the practical
form recommended by the book.
"""

from __future__ import annotations

from dataclasses import dataclass

# Iteration policy
R_ABS_TOL = 1.0        # SCF/STB
MAX_ITER = 50


@dataclass(frozen=True)
class PVTPoint:
    p_psia: float
    Bo_bbl_stb: float
    Bg_bbl_scf: float
    Rso_scf_stb: float
    mu_o_cp: float
    mu_g_cp: float


@dataclass(frozen=True)
class TarnerRow:
    p_psia: float
    Np_stb: float
    Gp_scf: float
    R_scf_stb: float
    SL: float
    kg_over_ko: float
    n_iter: int
    converged: bool


@dataclass(frozen=True)
class TarnerResult:
    N_stb: float
    rows: tuple[TarnerRow, ...]
    converged_all: bool


def _interp_kg_ko(SL: float, table: list[tuple[float, float]]) -> float:
    """Linear interpolation on monotone (SL, kg_ko) table."""
    if not table:
        raise ValueError("rel_perm table must be non-empty")
    if SL <= table[0][0]:
        # Out-of-range low SL: kg/ko ~ 0
        return table[0][1]
    if SL >= table[-1][0]:
        # Out-of-range high SL: extrapolate using the last segment
        s1, k1 = table[-2]
        s2, k2 = table[-1]
        slope = (k2 - k1) / (s2 - s1) if s2 != s1 else 0.0
        return k2 + slope * (SL - s2)
    for i in range(len(table) - 1):
        s1, k1 = table[i]
        s2, k2 = table[i + 1]
        if s1 <= SL <= s2:
            frac = (SL - s1) / (s2 - s1) if s2 != s1 else 0.0
            return k1 + frac * (k2 - k1)
    return table[-1][1]


def _tracy_terms(
    Bo: float, Bg: float, Rso: float, Boi: float,
    Rsoi: float, m: float, Bgi: float,
) -> tuple[float, float]:
    """Tracy Phi_n, Phi_g (Eq. 9.51)."""
    if Bgi <= 0.0:
        raise ValueError(f"Bgi must be > 0, got {Bgi!r}")
    D = (
        Bo - Boi
        + (Rsoi - Rso) * Bg
        + (m * Boi / Bgi) * (Bg - Bgi)
    )
    if D <= 0.0:
        raise ValueError(
            f"Tracy denominator D = {D!r} <= 0; check PVT inputs."
        )
    phi_n = (Bo - Rso * Bg) / D
    phi_g = Bg / D
    return phi_n, phi_g


def _instantaneous_R(
    Rso: float, kg_ko: float, mu_o: float, mu_g: float,
    Bo: float, Bg: float,
) -> float:
    """Instantaneous gas-oil ratio (Eq. 9.33)."""
    return Rso + kg_ko * (mu_o / mu_g) * (Bo / Bg)


def tarner_gas_drive(
    N_stb: float,
    Swi: float,
    pvt: list[PVTPoint],
    rel_perm: list[tuple[float, float]],
    m: float = 0.0,
) -> TarnerResult:
    """Tarner / Tracy internal gas drive prediction.

    Steps through pressure from pvt[0].p_psia (highest, at or above
    bubble point) downward to pvt[-1].p_psia. At each step iterates
    on the instantaneous R until convergence (Eqs. 9.51, 9.53, 9.56).

    Args:
        N_stb: Initial oil in place, STB (> 0).
        Swi: Initial water saturation, fraction (0, 1).
        pvt: List of PVTPoint from pi downward; strictly decreasing
            p_psia, length >= 2.
        rel_perm: List of (SL, kg_ko) pairs, SL in [0, 1],
            sorted ascending.
        m: Initial gas-cap / oil-zone ratio (>= 0; default 0 for
            pure internal gas drive).

    Returns:
        TarnerResult with one row per pressure step beyond the first.

    Raises:
        ValueError: any input out of range, or an iteration failed
            to converge within MAX_ITER.
    """
    if not (N_stb > 0.0):
        raise ValueError(f"N_stb must be > 0, got {N_stb!r}")
    if not (0.0 <= Swi < 1.0):
        raise ValueError(f"Swi must be in [0, 1), got {Swi!r}")
    if not (m >= 0.0):
        raise ValueError(f"m must be >= 0, got {m!r}")
    if len(pvt) < 2:
        raise ValueError(f"pvt must have >= 2 points, got {len(pvt)}")
    for i, pt in enumerate(pvt):
        for name, v in [
            ("Bo", pt.Bo_bbl_stb), ("Bg", pt.Bg_bbl_scf),
            ("Rso", pt.Rso_scf_stb), ("mu_o", pt.mu_o_cp),
            ("mu_g", pt.mu_g_cp), ("p", pt.p_psia),
        ]:
            if not (v > 0.0 if name != "Rso" else v >= 0.0):
                raise ValueError(f"pvt[{i}].{name} out of range: {v!r}")
        if i > 0 and pt.p_psia >= pvt[i - 1].p_psia:
            raise ValueError(
                f"pvt pressures must strictly decrease; index {i}: "
                f"{pt.p_psia!r} >= {pvt[i - 1].p_psia!r}"
            )
    if len(rel_perm) < 2:
        raise ValueError("rel_perm must have >= 2 (SL, kg_ko) points")
    for i in range(1, len(rel_perm)):
        if rel_perm[i][0] <= rel_perm[i - 1][0]:
            raise ValueError(
                f"rel_perm SL must be strictly increasing at {i}"
            )
        if rel_perm[i][1] < 0.0:
            raise ValueError(
                f"rel_perm[{i}].kg_ko must be >= 0, got "
                f"{rel_perm[i][1]!r}"
            )

    Boi = pvt[0].Bo_bbl_stb
    Rsoi = pvt[0].Rso_scf_stb
    Bgi = pvt[0].Bg_bbl_scf

    Np_prev = 0.0
    Gp_prev = 0.0
    R_prev = Rsoi
    rows: list[TarnerRow] = []
    converged_all = True

    for k in range(1, len(pvt)):
        pt = pvt[k]
        phi_n, phi_g = _tracy_terms(
            Bo=pt.Bo_bbl_stb, Bg=pt.Bg_bbl_scf,
            Rso=pt.Rso_scf_stb, Boi=Boi, Rsoi=Rsoi, m=m, Bgi=Bgi,
        )

        # Initial guess: Rso at this pressure (no free gas flow)
        R_j = pt.Rso_scf_stb
        converged = False
        n_iter = 0
        Np_j = Np_prev
        SL_j = Swi
        kg_ko_j = 0.0
        for n_iter in range(1, MAX_ITER + 1):
            R_ave = 0.5 * (R_prev + R_j)
            # Eq. (9.56)
            num = N_stb - Np_prev * phi_n - Gp_prev * phi_g
            den = phi_n + phi_g * R_ave
            if den <= 0.0:
                raise ValueError(
                    f"step {k} iter {n_iter}: denominator {den!r} <= 0"
                )
            dNp = num / den
            Np_j = Np_prev + dNp
            if not (0.0 <= Np_j <= N_stb * (1.0 + 1e-6)):
                raise ValueError(
                    f"step {k} iter {n_iter}: Np={Np_j!r} out of range"
                )
            # Eq. (9.40)
            SL_j = Swi + (1.0 - Swi) * (1.0 - Np_j / N_stb) * (
                pt.Bo_bbl_stb / Boi
            )
            kg_ko_j = _interp_kg_ko(SL_j, rel_perm)
            # Eq. (9.33)
            R_calc = _instantaneous_R(
                Rso=pt.Rso_scf_stb, kg_ko=kg_ko_j,
                mu_o=pt.mu_o_cp, mu_g=pt.mu_g_cp,
                Bo=pt.Bo_bbl_stb, Bg=pt.Bg_bbl_scf,
            )
            if abs(R_calc - R_j) < R_ABS_TOL:
                R_j = R_calc
                converged = True
                break
            R_j = R_calc
        if not converged:
            converged_all = False
            raise ValueError(
                f"Tarner step {k} (p={pt.p_psia}): failed to converge "
                f"in {MAX_ITER} iterations; last R_j={R_j:.3f}, "
                f"R_calc={R_calc:.3f}, |dR|={abs(R_calc-R_j):.3f}"
            )

        R_ave = 0.5 * (R_prev + R_j)
        Gp_j = Gp_prev + R_ave * (Np_j - Np_prev)

        rows.append(TarnerRow(
            p_psia=pt.p_psia, Np_stb=Np_j, Gp_scf=Gp_j,
            R_scf_stb=R_j, SL=SL_j, kg_over_ko=kg_ko_j,
            n_iter=n_iter, converged=True,
        ))
        Np_prev = Np_j
        Gp_prev = Gp_j
        R_prev = R_j

    return TarnerResult(
        N_stb=N_stb, rows=tuple(rows), converged_all=converged_all,
    )
