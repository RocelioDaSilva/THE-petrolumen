"""Well constraint swap consistency check (Chin 2016, Ch 3 Ex 3-5,
pp. 128-131).

Chin's diagnostic: if a well at (p1, q1) is switched to the opposite
constraint type and the corresponding constraint value is imposed,
the other quantity should recover its original value (within
numerical tolerance). This feature implements the analytical
equivalent using Feature 24's PI.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.reservoir.productivity_index import productivity_index_theoretical

CONSISTENCY_LO = 0.95
CONSISTENCY_HI = 1.05


@dataclass(frozen=True)
class SwapConsistencyResult:
    PI_stb_d_psi: float
    q2_predicted_stb_d: float
    p2_predicted_psia: float
    observed_ratio_q: float | None
    observed_ratio_p: float | None
    consistent: bool
    diagnostic: str


def constraint_swap_check(
    p1_psia: float,
    q1_stb_d: float,
    p_avg_psia: float,
    k_md: float, h_ft: float, mu_cp: float, B_bbl_stb: float,
    r_e_ft: float, r_w_ft: float, S: float,
    p2_psia: float | None = None,
    q2_stb_d: float | None = None,
) -> SwapConsistencyResult:
    """Consistency check for a well constraint swap.

    Uses the analytical pseudosteady PI (Feature 24) to predict the
    opposite constraint's value, and optionally compares to observed
    data.

    Args:
        p1_psia, q1_stb_d: Observed state, both > 0.
        p_avg_psia: Reservoir average pressure, psia (> max(p1, p2)).
        k_md, h_ft, mu_cp, B_bbl_stb: reservoir/fluid, > 0.
        r_e_ft, r_w_ft: radii, ft (r_e > r_w > 0).
        S: skin factor.
        p2_psia, q2_stb_d: Optional observed state to compare against.
            If both provided, the consistency ratio is computed. If
            only one, the other is predicted and the ratio is None.

    Returns:
        SwapConsistencyResult.

    Raises:
        ValueError: invalid inputs or nonsensical pressure drop.
    """
    if not (p1_psia > 0.0):
        raise ValueError(f"p1_psia must be > 0, got {p1_psia!r}")
    if not (q1_stb_d > 0.0):
        raise ValueError(f"q1_stb_d must be > 0, got {q1_stb_d!r}")
    if not (p_avg_psia > 0.0):
        raise ValueError(f"p_avg_psia must be > 0, got {p_avg_psia!r}")
    if p1_psia >= p_avg_psia:
        raise ValueError(
            f"p1 ({p1_psia!r}) must be < p_avg ({p_avg_psia!r})"
        )

    PI = productivity_index_theoretical(
        k_md=k_md, h_ft=h_ft, mu_cp=mu_cp, B_bbl_stb=B_bbl_stb,
        r_e_ft=r_e_ft, r_w_ft=r_w_ft, S=S,
    )

    # Predict q2 at p2, or p2 at q2
    if p2_psia is not None:
        if not (p2_psia > 0.0):
            raise ValueError(f"p2_psia must be > 0, got {p2_psia!r}")
        if p2_psia >= p_avg_psia:
            raise ValueError(
                f"p2 ({p2_psia!r}) must be < p_avg ({p_avg_psia!r})"
            )
        q2_predicted = PI * (p_avg_psia - p2_psia)
    else:
        q2_predicted = float("nan")

    if q2_stb_d is not None:
        if not (q2_stb_d > 0.0):
            raise ValueError(f"q2_stb_d must be > 0, got {q2_stb_d!r}")
        p2_predicted = p_avg_psia - q2_stb_d / PI
        if p2_predicted <= 0.0:
            raise ValueError(
                f"Predicted p2 = {p2_predicted!r} <= 0; check inputs."
            )
    else:
        p2_predicted = float("nan")

    # Ratios
    ratio_q: float | None = None
    if (p2_psia is not None) and (q2_stb_d is not None):
        ratio_q = q2_predicted / q2_stb_d
    ratio_p: float | None = None
    if (p2_psia is not None) and (q2_stb_d is not None):
        ratio_p = p2_predicted / p2_psia

    # Consistency
    consistent = False
    if ratio_q is not None:
        consistent = (CONSISTENCY_LO <= ratio_q <= CONSISTENCY_HI)
    if ratio_p is not None:
        consistent = consistent and (
            CONSISTENCY_LO <= ratio_p <= CONSISTENCY_HI
        )

    # Diagnostic string
    if ratio_q is None:
        diagnostic = (
            f"PI = {PI:.4f} STB/day/psi; q2_predicted = "
            f"{q2_predicted:.2f} STB/day; p2_predicted = "
            f"{p2_predicted:.2f} psia."
        )
    else:
        diagnostic = (
            f"PI = {PI:.4f} STB/day/psi; predicted/observed ratios: "
            f"q = {ratio_q:.4f}, p = {ratio_p:.4f}; "
            f"consistent = {consistent}."
        )

    return SwapConsistencyResult(
        PI_stb_d_psi=PI,
        q2_predicted_stb_d=q2_predicted,
        p2_predicted_psia=p2_predicted,
        observed_ratio_q=ratio_q,
        observed_ratio_p=ratio_p,
        consistent=consistent,
        diagnostic=diagnostic,
    )
