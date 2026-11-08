"""Schilthuis internal gas drive via secant iteration (Craft Eqs. 9.41-9.47)."""
from __future__ import annotations
from dataclasses import dataclass

from app.reservoir.muskat_igd import MuskatPVT, _interp_rp

TOL = 1.0e-4
MAX_ITER = 30


@dataclass(frozen=True)
class SchilthuisRow:
    p_psia: float
    Np_stb: float
    S_L: float
    R_scf_stb: float
    n_iter: int


@dataclass(frozen=True)
class SchilthuisResult:
    N_stb: float
    rows: tuple[SchilthuisRow, ...]


def _f_val(Np_over_N, p_prev, p_cur, Boi, Rsoi):
    """Eq. (9.41) LHS-1. Np_over_N is the guess for cumulative."""
    Bt = p_cur.Bo + (p_cur.Rso - Rsoi) * 0.0  # placeholder; see caller
    return 0.0


def schilthuis_igd(
    N_stb: float, Swi: float,
    pvt: list[MuskatPVT], rel_perm: list[tuple[float, float]],
) -> SchilthuisResult:
    """Schilthuis IGD via secant iteration (Craft Eqs. 9.41-9.47).

    Args:
        N_stb: Initial oil in place, STB (> 0).
        Swi: Connate water, fraction [0, 1).
        pvt: Pressure grid from pi downward, >= 2 points.
        rel_perm: (SL, kg/ko) pairs, strictly increasing in SL.

    Returns:
        SchilthuisResult.

    Raises:
        ValueError: invalid input or non-convergence.
    """
    if not (N_stb > 0.0):
        raise ValueError(f"N_stb must be > 0, got {N_stb!r}")
    if not (0.0 <= Swi < 1.0):
        raise ValueError(f"Swi must be in [0, 1), got {Swi!r}")
    if len(pvt) < 2:
        raise ValueError("pvt must have >= 2 points")

    Boi = pvt[0].Bo
    Rsoi = pvt[0].Rso

    rows: list[SchilthuisRow] = []
    Np_prev = 0.0
    Rp_prev = Rsoi

    for k in range(1, len(pvt)):
        p_cur = pvt[k]

        def f_of_x(x: float) -> float:
            """Eq. (9.41) residual at trial cumulative x."""
            Np = x * N_stb
            SL = Swi + (1.0 - Swi) * (1.0 - x) * (p_cur.Bo / Boi)
            kg_ko = _interp_rp(SL, rel_perm)
            R_inst = p_cur.Rso + kg_ko * (p_cur.mu_o / p_cur.mu_g) * (
                p_cur.Bo / p_cur.Bg
            )
            # Rp for this trial: weighted average of past and current
            if Np <= 0.0:
                Rp = Rsoi
            else:
                Rp = (Np_prev * Rp_prev + (Np - Np_prev) * R_inst) / Np
            tp = p_cur.Bo + p_cur.Bg * (Rp - Rsoi)
            num = x * tp
            den = p_cur.Bo - Boi + p_cur.Bg * (Rsoi - p_cur.Rso)
            if den <= 0.0:
                return 1.0e6
            return num / den - 1.0

        # Seed with two guesses; use previous fraction as first
        x_prev = (Np_prev / N_stb) if Np_prev > 0.0 else 0.01
        x_cur = x_prev * 1.5 if x_prev > 0.0 else 0.02
        f_prev = f_of_x(x_prev)
        f_cur = f_of_x(x_cur)
        converged = False
        n_iter = 0
        x_new = x_cur
        for n_iter in range(1, MAX_ITER + 1):
            if abs(f_cur - f_prev) < 1.0e-14:
                break
            x_new = x_cur - f_cur * (x_cur - x_prev) / (f_cur - f_prev)
            f_new = f_of_x(x_new)
            if abs(f_new) < TOL:
                converged = True
                break
            x_prev, f_prev = x_cur, f_cur
            x_cur, f_cur = x_new, f_new
        if not converged:
            raise ValueError(
                f"Schilthuis step {k} failed to converge in {MAX_ITER} "
                f"iterations; |f|={abs(f_cur):.3e}"
            )

        # Recompute derived quantities at converged x
        Np = x_new * N_stb
        SL = Swi + (1.0 - Swi) * (1.0 - x_new) * (p_cur.Bo / Boi)
        kg_ko = _interp_rp(SL, rel_perm)
        R_inst = p_cur.Rso + kg_ko * (p_cur.mu_o / p_cur.mu_g) * (
            p_cur.Bo / p_cur.Bg
        )
        if Np > 0.0:
            Rp_new = (Np_prev * Rp_prev + (Np - Np_prev) * R_inst) / Np
        else:
            Rp_new = Rsoi

        rows.append(SchilthuisRow(
            p_psia=p_cur.p_psia, Np_stb=Np, S_L=SL,
            R_scf_stb=R_inst, n_iter=n_iter,
        ))
        Np_prev = Np
        Rp_prev = Rp_new

    return SchilthuisResult(N_stb=N_stb, rows=tuple(rows))
