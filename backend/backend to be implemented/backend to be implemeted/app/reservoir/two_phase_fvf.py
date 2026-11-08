"""Two-phase formation volume factor (Craft Eq. 1.28, p. 35)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class TwoPhaseFVFResult:
    Bt_bbl_stb: float
    free_gas_term_bbl_stb: float
    Rso_gt_Rsoi: bool


def two_phase_fvf(
    Bo_bbl_stb: float, Bg_bbl_scf: float,
    Rsoi_scf_stb: float, Rso_scf_stb: float,
) -> TwoPhaseFVFResult:
    """Return Bt = Bo + Bg(Rsoi - Rso) per Eq. (1.28).

    Args:
        Bo_bbl_stb: Oil FVF, bbl/STB (> 0).
        Bg_bbl_scf: Gas FVF, bbl/SCF (> 0).
        Rsoi_scf_stb: Initial solution GOR, SCF/STB (>= 0).
        Rso_scf_stb: Current solution GOR, SCF/STB (>= 0).

    Returns:
        TwoPhaseFVFResult.

    Raises:
        ValueError: any input out of physical range.
    """
    if not (Bo_bbl_stb > 0.0):
        raise ValueError(f"Bo must be > 0, got {Bo_bbl_stb!r}")
    if not (Bg_bbl_scf > 0.0):
        raise ValueError(f"Bg must be > 0, got {Bg_bbl_scf!r}")
    if not (Rsoi_scf_stb >= 0.0):
        raise ValueError(f"Rsoi must be >= 0, got {Rsoi_scf_stb!r}")
    if not (Rso_scf_stb >= 0.0):
        raise ValueError(f"Rso must be >= 0, got {Rso_scf_stb!r}")

    fg_term = Bg_bbl_scf * (Rsoi_scf_stb - Rso_scf_stb)
    return TwoPhaseFVFResult(
        Bt_bbl_stb=Bo_bbl_stb + fg_term,
        free_gas_term_bbl_stb=fg_term,
        Rso_gt_Rsoi=(Rso_scf_stb > Rsoi_scf_stb),
    )
