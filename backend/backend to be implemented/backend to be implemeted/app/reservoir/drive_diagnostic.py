"""Drive-mechanism diagnostic from history (Craft p. 64)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

import numpy as np

from app.reservoir.oil_material_balance import oil_material_balance

TREND_STABLE = 0.05
MIN_POINTS = 3

Classification = Literal[
    "volumetric", "water_drive", "decreasing", "insufficient_data"
]


@dataclass(frozen=True)
class DiagnosticSnapshot:
    t_days: float
    Np_stb: float
    Rp_scf_stb: float
    Wp_stb: float
    Bt: float
    Bti: float
    Bg: float
    Rsoi: float
    m: float
    Bgi: float | None
    Swi: float
    cw_psi_inv: float
    cf_psi_inv: float
    delta_p_psi: float


@dataclass(frozen=True)
class DriveDiagnosticResult:
    classification: Classification
    trend_fraction: float
    N_per_point_stb: tuple[float, ...]
    ddi_per_point: tuple[float, ...]
    sdi_per_point: tuple[float, ...]
    r_squared: float


def drive_diagnostic(
    snapshots: list[DiagnosticSnapshot],
) -> DriveDiagnosticResult:
    """Classify reservoir drive mechanism from history (Craft p. 64).

    Runs the single-point material balance at each snapshot with
    We=0. A stable N_k series means volumetric; trending up means
    water drive; trending down means unusual (data quality or
    gas breakthrough).

    Args:
        snapshots: List of DiagnosticSnapshot, >= 3 points, times
            strictly increasing.

    Returns:
        DriveDiagnosticResult.

    Raises:
        ValueError: any input out of range.
    """
    if len(snapshots) < MIN_POINTS:
        raise ValueError(
            f"At least {MIN_POINTS} snapshots required, got {len(snapshots)}"
        )
    for k, s in enumerate(snapshots):
        if not (s.t_days >= 0.0):
            raise ValueError(f"snapshots[{k}].t_days must be >= 0")
        if k > 0 and s.t_days <= snapshots[k - 1].t_days:
            raise ValueError(
                f"snapshots times must strictly increase at index {k}"
            )

    N_list: list[float] = []
    ddi_list: list[float] = []
    sdi_list: list[float] = []
    for k, s in enumerate(snapshots):
        try:
            r = oil_material_balance(
                Np=s.Np_stb, Rp=s.Rp_scf_stb, Wp=s.Wp_stb,
                Bt=s.Bt, Bti=s.Bti, Bg=s.Bg, Rsoi=s.Rsoi,
                m=s.m, Bgi=s.Bgi, We=0.0, Bw=1.0,
                Swi=s.Swi, cw=s.cw_psi_inv, cf=s.cf_psi_inv,
                delta_p=s.delta_p_psi,
            )
        except ValueError as exc:
            raise ValueError(f"snapshot {k}: {exc}")
        N_list.append(r.n_estimated)
        ddi_list.append(r.ddi)
        sdi_list.append(r.sdi)

    N_arr = np.asarray(N_list, dtype=float)
    t_arr = np.asarray([s.t_days for s in snapshots], dtype=float)

    # Linear trend of N vs t
    A = np.column_stack([t_arr, np.ones_like(t_arr)])
    sol, *_ = np.linalg.lstsq(A, N_arr, rcond=None)
    slope = float(sol[0])
    intercept = float(sol[1])
    pred = slope * t_arr + intercept
    ss_res = float(np.sum((N_arr - pred) ** 2))
    ss_tot = float(np.sum((N_arr - float(np.mean(N_arr))) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0.0 else 1.0

    if ss_tot <= 0.0:
        return DriveDiagnosticResult(
            classification="insufficient_data",
            trend_fraction=0.0,
            N_per_point_stb=tuple(N_list),
            ddi_per_point=tuple(ddi_list),
            sdi_per_point=tuple(sdi_list),
            r_squared=r2,
        )

    N1 = N_list[0]
    if N1 <= 0.0:
        raise ValueError(
            f"First-point N = {N1!r} <= 0; cannot normalize trend"
        )
    span = t_arr[-1] - t_arr[0]
    trend_frac = (slope * span) / N1

    if abs(trend_frac) < TREND_STABLE:
        cls: Classification = "volumetric"
    elif trend_frac > 0.0:
        cls = "water_drive"
    else:
        cls = "decreasing"

    return DriveDiagnosticResult(
        classification=cls,
        trend_fraction=trend_frac,
        N_per_point_stb=tuple(N_list),
        ddi_per_point=tuple(ddi_list),
        sdi_per_point=tuple(sdi_list),
        r_squared=r2,
    )
