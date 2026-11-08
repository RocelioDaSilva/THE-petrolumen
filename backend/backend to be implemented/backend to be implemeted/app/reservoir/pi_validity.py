"""PI validity diagnostic (Chin 2016 Ch 5, pp. 290-295).

Compares a simulated PI to the analytical radial-flow PI (Feature 24)
and flags whether the analytical formula is trustworthy for the given
well type. Chin argues (p. 291) that analytical PIs are "fudge factors"
and that modern well systems require numerical simulation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.reservoir.productivity_index import productivity_index_theoretical

WellType = Literal["vertical", "deviated", "horizontal", "multilateral"]

R_VALID_LO = 0.8
R_VALID_HI = 1.25
R_SIM_REQUIRED_LO = 0.2
R_SIM_REQUIRED_HI = 5.0


@dataclass(frozen=True)
class PIValidityResult:
    PI_analytical_stb_d_psi: float
    PI_simulated_stb_d_psi: float
    ratio: float
    classification: str
    recommendation: str


def pi_validity_check(
    PI_sim_stb_d_psi: float,
    k_md: float, h_ft: float, mu_cp: float, B_bbl_stb: float,
    r_e_ft: float, r_w_ft: float, S: float,
    well_type: WellType = "vertical",
    num_laterals: int = 0,
) -> PIValidityResult:
    """Compare analytical and simulated PIs; classify validity.

    Args:
        PI_sim_stb_d_psi: PI from history match or test, STB/day/psi
            (> 0).
        k_md, h_ft, mu_cp, B_bbl_stb: reservoir/fluid properties,
            each > 0.
        r_e_ft, r_w_ft: radii, ft (> 0; r_e > r_w).
        S: skin factor (dimensionless).
        well_type: 'vertical', 'deviated', 'horizontal', or
            'multilateral'.
        num_laterals: number of laterals for 'multilateral' wells
            (ignored otherwise; informational).

    Returns:
        PIValidityResult.

    Raises:
        ValueError: any input out of physical range.
    """
    if not (PI_sim_stb_d_psi > 0.0):
        raise ValueError(
            f"PI_sim must be > 0, got {PI_sim_stb_d_psi!r}"
        )
    if well_type not in (
        "vertical", "deviated", "horizontal", "multilateral"
    ):
        raise ValueError(
            f"well_type must be one of (vertical, deviated, horizontal, "
            f"multilateral), got {well_type!r}"
        )
    if num_laterals < 0:
        raise ValueError(
            f"num_laterals must be >= 0, got {num_laterals}"
        )

    PI_an = productivity_index_theoretical(
        k_md=k_md, h_ft=h_ft, mu_cp=mu_cp, B_bbl_stb=B_bbl_stb,
        r_e_ft=r_e_ft, r_w_ft=r_w_ft, S=S,
    )
    ratio = PI_sim_stb_d_psi / PI_an

    if well_type == "vertical":
        if R_VALID_LO <= ratio <= R_VALID_HI:
            classification = "analytical_valid"
            rec = (
                "Vertical well; simulated PI matches analytical formula "
                "within 25%. Use analytical PI (Feature 24) with confidence."
            )
        elif ratio < R_SIM_REQUIRED_LO or ratio > R_SIM_REQUIRED_HI:
            classification = "use_simulator"
            rec = (
                "Vertical well but analytical PI off by >5x; the well is "
                "not behaving as a radial-flow well (likely severe damage, "
                "partial penetration, or non-Darcy effects). Use a "
                "numerical simulator."
            )
        else:
            classification = "analytical_suspect"
            rec = (
                "Vertical well; analytical PI off by 25-500%. Investigate "
                "skin, partial penetration, or reservoir heterogeneity "
                "before booking reserves from the analytical formula."
            )
    else:
        # Chin Ch 5 p. 291: non-vertical wells cannot be trusted with
        # analytical PIs at all
        classification = "use_simulator"
        rec = (
            f"{well_type.capitalize()} well: Chin Ch 5 p. 291 explicitly "
            "argues that analytical PI formulas (including Joshi 1988, "
            "Borisov 1964, Giger-Reiss-Jourdan 1986) are unreliable for "
            "non-vertical wells. Use a numerical simulator (Chin's "
            "Multisim or equivalent) for reserves booking."
        )

    return PIValidityResult(
        PI_analytical_stb_d_psi=PI_an,
        PI_simulated_stb_d_psi=PI_sim_stb_d_psi,
        ratio=ratio,
        classification=classification,
        recommendation=rec,
    )
