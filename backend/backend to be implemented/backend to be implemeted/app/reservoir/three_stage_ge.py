"""Three-stage separator total gas production (Craft Eq. 3.23-3.24)."""
from __future__ import annotations
from dataclasses import dataclass

from app.reservoir.gas_equivalent import gas_equivalent


@dataclass(frozen=True)
class ThreeStageGEResult:
    Gp_total_scf: float
    GE_scf_per_bbl: float
    Gp_from_condensate_scf: float
    two_stage: bool


def three_stage_total_gp(
    Gps_scf: float, Gss_scf: float, Gst_scf: float,
    Np_stb: float,
    gamma_o: float | None = None,
    M_wo: float | None = None,
    oil_api: float | None = None,
    two_stage: bool = False,
) -> ThreeStageGEResult:
    """Total gas production via Eq. (3.23) or (3.24).

    Args:
        Gps_scf, Gss_scf, Gst_scf: separator/stock-tank gas, SCF (>= 0).
        Np_stb: Condensate production, STB (>= 0).
        gamma_o, M_wo, oil_api: identity of stock-tank oil (supply at
            least one).
        two_stage: If True, use Eq. (3.24), dropping Gss.

    Returns:
        ThreeStageGEResult.
    """
    for nm, v in [("Gps", Gps_scf), ("Gss", Gss_scf), ("Gst", Gst_scf)]:
        if v < 0.0:
            raise ValueError(f"{nm}_scf must be >= 0, got {v!r}")
    if Np_stb < 0.0:
        raise ValueError(f"Np_stb must be >= 0, got {Np_stb!r}")

    ge_result = gas_equivalent(
        Np_stb=Np_stb, gamma_o=gamma_o, M_wo=M_wo, oil_api=oil_api,
    )
    ge = ge_result.ge_scf_per_bbl
    gp_cond = ge * Np_stb
    if two_stage:
        Gp = Gps_scf + Gst_scf + gp_cond
    else:
        Gp = Gps_scf + Gss_scf + Gst_scf + gp_cond
    return ThreeStageGEResult(
        Gp_total_scf=Gp,
        GE_scf_per_bbl=ge,
        Gp_from_condensate_scf=gp_cond,
        two_stage=two_stage,
    )
