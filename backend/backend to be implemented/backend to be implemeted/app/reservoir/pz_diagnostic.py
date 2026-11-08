"""p/z straight-line diagnostic (Craft Fig. 3.12, pp. 100-101)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

import numpy as np

Classification = Literal["volumetric", "partial_water_drive",
                         "complete_water_drive"]


@dataclass(frozen=True)
class PZDiagnosticResult:
    linear_r2: float
    quadratic_r2: float
    quadratic_ratio: float
    classification: Classification
    b_linear: float
    c_quadratic: float


def pz_diagnostic(points: list[tuple[float, float]]) -> PZDiagnosticResult:
    """Classify p/z straightness (Craft Fig. 3.12).

    Args:
        points: (p/z, Gp) tuples, sorted by Gp, >= 4.

    Returns:
        PZDiagnosticResult.

    Raises:
        ValueError: fewer than 4 points, non-finite, or b_linear = 0.
    """
    if len(points) < 4:
        raise ValueError(f"at least 4 points required, got {len(points)}")
    for i, (pz, gp) in enumerate(points):
        if not (np.isfinite(pz) and np.isfinite(gp)):
            raise ValueError(f"points[{i}] non-finite")
        if gp < 0.0:
            raise ValueError(f"points[{i}].Gp must be >= 0")
    Gp = np.array([p[1] for p in points], dtype=float)
    pz = np.array([p[0] for p in points], dtype=float)
    order = np.argsort(Gp)
    Gp, pz = Gp[order], pz[order]
    if np.any(np.diff(Gp) <= 0.0):
        raise ValueError("Gp values must be distinct")

    # Linear fit
    Alin = np.column_stack([Gp, np.ones_like(Gp)])
    sol_lin, *_ = np.linalg.lstsq(Alin, pz, rcond=None)
    b, a = float(sol_lin[0]), float(sol_lin[1])
    pred_lin = a + b * Gp
    ss_res = float(np.sum((pz - pred_lin) ** 2))
    ss_tot = float(np.sum((pz - float(np.mean(pz))) ** 2))
    r2_lin = 1.0 - ss_res / ss_tot if ss_tot > 0.0 else 1.0

    # Quadratic fit
    Aq = np.column_stack([Gp ** 2, Gp, np.ones_like(Gp)])
    sol_q, *_ = np.linalg.lstsq(Aq, pz, rcond=None)
    c, b_q, a_q = float(sol_q[0]), float(sol_q[1]), float(sol_q[2])
    pred_q = a_q + b_q * Gp + c * Gp ** 2
    ss_res_q = float(np.sum((pz - pred_q) ** 2))
    r2_q = 1.0 - ss_res_q / ss_tot if ss_tot > 0.0 else 1.0

    if abs(b) < 1e-30:
        raise ValueError(f"b_linear={b!r} near zero; cannot classify")
    lam = abs(c) * Gp[-1] / abs(b)

    if r2_lin >= 0.995 and lam < 0.05:
        cls: Classification = "volumetric"
    elif lam >= 0.25:
        cls = "complete_water_drive"
    else:
        cls = "partial_water_drive"

    return PZDiagnosticResult(
        linear_r2=r2_lin, quadratic_r2=r2_q,
        quadratic_ratio=lam, classification=cls,
        b_linear=b, c_quadratic=c,
    )
