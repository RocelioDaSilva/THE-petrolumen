"""Pressure-transient analysis (PTA) — Horner, MDH, Bourdet derivative, flow regimes.

Consolidated from the legacy prototype
``legacy_archive/reservoir_engineering/well_testing/well_test.py`` and the
absorbed ``WellTesting`` class in :mod:`app.engines.reservoir.reservoir_engineering`.

The legacy and first-absorbed versions were incomplete (no net-pay ``h`` term,
sign-convention errors, no derivative). This module is a clean, stateless,
unit-documented reimplementation using field units throughout.

Field units (consistent with the rest of ``app/engines/reservoir``):

* ``t`` — hours
* ``p`` — psia
* ``q`` — STB/day
* ``mu`` — cp
* ``ct`` — 1/psi
* ``phi`` — fraction
* ``rw`` — ft
* ``h`` — ft
* ``B`` — rb/STB
* ``k`` — mD
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

__all__ = [
    "FlowRegimes",
    "bourdet_derivative",
    "identify_flow_regimes",
    "analyze_drawdown",
    "analyze_buildup",
    "horner_time",
]


def _series(time, pressure) -> tuple[np.ndarray, np.ndarray]:
    """Validate and coerce a time/pressure series. Fails loudly on bad input."""
    t = np.asarray(time, dtype=float)
    p = np.asarray(pressure, dtype=float)
    if t.ndim != 1 or p.ndim != 1:
        raise ValueError("time and pressure must be one-dimensional arrays")
    if t.size != p.size or t.size < 3:
        raise ValueError("time and pressure must have equal length with >= 3 points")
    if np.any(~np.isfinite(t)) or np.any(~np.isfinite(p)):
        raise ValueError("time and pressure must be finite")
    if np.any(t <= 0):
        raise ValueError("time must be strictly positive (hours)")
    if not np.all(np.diff(t) > 0):
        raise ValueError("time must be strictly increasing")
    return t, p


def horner_time(tp: float, dt: np.ndarray) -> np.ndarray:
    """Horner (superposition) time ``(tp + dt) / dt``."""
    if not math.isfinite(tp) or tp <= 0:
        raise ValueError("tp (producing time, hours) must be positive and finite")
    dt = np.asarray(dt, dtype=float)
    if np.any(dt <= 0):
        raise ValueError("dt (shut-in time, hours) must be positive")
    return (tp + dt) / dt


def bourdet_derivative(time: np.ndarray, pressure: np.ndarray, L: float = 0.0) -> np.ndarray:
    """Compute the Bourdet log-derivative ``dP / d(ln t)``.

    Uses the standard 3-point weighted formula; when ``L`` is supplied, the
    derivative is smoothed over a window of ``±L`` (in log-cycles, e.g. 0.2).

    Returns ``NaN`` for the endpoints where the derivative is undefined.
    """
    t, p = _series(time, pressure)
    lt = np.log(t)
    n = t.size
    d = np.full(n, np.nan)

    for i in range(1, n - 1):
        # Weighted average of the forward and backward slopes on the log-time
        # axis (Bourdet's method for non-uniformly spaced data).
        dxm = lt[i] - lt[i - 1]
        dxp = lt[i + 1] - lt[i]
        forward = (p[i + 1] - p[i]) / dxp
        backward = (p[i] - p[i - 1]) / dxm
        d[i] = (dxm * forward + dxp * backward) / (dxm + dxp)

    if L > 0:
        smoothed = np.full(n, np.nan)
        for i in range(n):
            lo = np.searchsorted(lt, lt[i] - L)
            hi = np.searchsorted(lt, lt[i] + L)
            window = d[lo:hi]
            if window.size:
                smoothed[i] = np.nanmean(window)
        d = smoothed

    return d


@dataclass
class FlowRegimes:
    """Time windows (hours) identified from the pressure derivative."""

    radial: tuple[float, float] | None = None
    wellbore_storage: tuple[float, float] | None = None
    boundary: tuple[float, float] | None = None
    radial_slope: float | None = None
    radial_std: float | None = None
    notes: list[str] = field(default_factory=list)


def identify_flow_regimes(time: np.ndarray, derivative: np.ndarray) -> FlowRegimes:
    """Heuristically classify flow regimes from a Bourdet derivative curve.

    * ``radial`` — the flattest contiguous segment (|derivative| nearly constant).
    * ``wellbore_storage`` — early-time unit-slope (rising) segment.
    * ``boundary`` — late-time departure (rising = closed, falling = depletion).

    This is a diagnostic aid; it identifies the radial window used by the
    semilog straight-line methods, not a physical inversion.
    """
    t, _ = _series(time, time)  # validate monotonicity/positivity
    d = np.asarray(derivative, dtype=float)
    if d.size != t.size:
        raise ValueError("derivative must have the same length as time")
    finite = np.isfinite(d)
    regimes = FlowRegimes()
    if not np.any(finite):
        regimes.notes.append("no finite derivative points")
        return regimes

    idx = np.flatnonzero(finite)
    # Rolling standard deviation of the derivative over a ~0.5 log-cycle window.
    lt = np.log(t)
    rolling_std = np.full(d.size, np.nan)
    for i in idx:
        lo = np.searchsorted(lt, lt[i] - 0.5)
        hi = np.searchsorted(lt, lt[i] + 0.5)
        seg = d[lo:hi]
        rolling_std[i] = np.nanstd(seg) if seg.size >= 3 else np.nan

    valid = np.isfinite(rolling_std)
    if not np.any(valid):
        regimes.notes.append("insufficient points for a stable window")
        return regimes

    # Radial flow: lowest-variance contiguous region.
    best_i = int(np.nanargmin(rolling_std))
    best_std = rolling_std[best_i]
    radial_mask = np.zeros(d.size, dtype=bool)
    radial_mask[best_i] = True
    for direction in (-1, 1):
        j = best_i + direction
        while 0 <= j < d.size and np.isfinite(rolling_std[j]) and rolling_std[j] <= 2.0 * best_std:
            radial_mask[j] = True
            j += direction
    r_idx = np.flatnonzero(radial_mask)
    regimes.radial = (float(t[r_idx[0]]), float(t[r_idx[-1]]))
    regimes.radial_slope = float(np.nanmean(d[radial_mask]))
    regimes.radial_std = float(best_std)

    # Early-time unit-slope storage: derivative rising before radial window.
    pre = np.flatnonzero(np.isfinite(d) & (np.arange(d.size) < r_idx[0]))
    if pre.size >= 2 and np.nanmean(np.diff(d[pre])) > 0:
        regimes.wellbore_storage = (float(t[pre[0]]), float(t[pre[-1]]))

    # Late-time boundary: derivative departing from the radial plateau.
    post = np.flatnonzero(np.isfinite(d) & (np.arange(d.size) > r_idx[-1]))
    if post.size >= 3:
        departure = np.abs(d[post] - regimes.radial_slope) > 2.0 * best_std
        if np.any(departure):
            b_idx = post[np.flatnonzero(departure)]
            regimes.boundary = (float(t[b_idx[0]]), float(t[b_idx[-1]]))

    return regimes


def _semilog(x: np.ndarray, y: np.ndarray, mask: np.ndarray | None = None):
    """Linear regression of ``y`` against ``log10(x)``."""
    lx = np.log10(x)
    if mask is None:
        mask = np.ones(x.size, dtype=bool)
    return float(np.polyfit(lx[mask], y[mask], 1)[0]), float(np.polyfit(lx[mask], y[mask], 1)[1])


@dataclass
class DrawdownResult:
    permeability_md: float
    skin: float
    slope_psi_per_cycle: float
    intercept_psi: float
    p1hr_psi: float
    radius_of_investigation_ft: float
    regimes: FlowRegimes


def analyze_drawdown(
    time: np.ndarray,
    pressure: np.ndarray,
    rate: float,
    viscosity: float,
    total_compressibility: float,
    porosity: float,
    wellbore_radius: float,
    initial_pressure: float,
    net_pay: float,
    formation_volume_factor: float = 1.0,
    derivative_smoothing: float = 0.0,
) -> DrawdownResult:
    """Infinite-acting radial-flow drawdown analysis (semilog method).

    ``pressure`` is flowing bottom-hole pressure; ``rate`` is the constant
    rate (STB/day); ``initial_pressure`` is the pressure before drawdown
    (psia). Recover permeability and skin from the semilog straight line
    ``p_wf = m * log10(t) + b`` using field-unit equations.
    """
    t, p = _series(time, pressure)
    for name, v in {
        "rate": rate,
        "viscosity": viscosity,
        "total_compressibility": total_compressibility,
        "porosity": porosity,
        "wellbore_radius": wellbore_radius,
        "initial_pressure": initial_pressure,
        "formation_volume_factor": formation_volume_factor,
        "net_pay": net_pay,
    }.items():
        if not math.isfinite(v) or v <= 0:
            raise ValueError(f"{name} must be a positive finite value")

    derivative = bourdet_derivative(t, p, derivative_smoothing)
    regimes = identify_flow_regimes(t, derivative)

    # Fit the semilog line over the radial-flow window when detected.
    mask = None
    if regimes.radial is not None:
        mask = (t >= regimes.radial[0]) & (t <= regimes.radial[1])
    slope, intercept = _semilog(t, p, mask)

    m = abs(slope)  # psi/cycle
    k = 162.6 * rate * formation_volume_factor * viscosity / (m * net_pay)

    # p1hr from the fitted straight line.
    p1hr = intercept  # log10(1 hr) == 0

    skin = 1.1513 * (
        (initial_pressure - p1hr) / m
        - math.log10(k / (porosity * viscosity * total_compressibility * wellbore_radius ** 2))
        + 3.2275
    )

    r_inv = math.sqrt(0.00105 * k * t[-1] / (porosity * viscosity * total_compressibility))

    return DrawdownResult(
        permeability_md=round(k, 3),
        skin=round(skin, 3),
        slope_psi_per_cycle=round(slope, 4),
        intercept_psi=round(intercept, 3),
        p1hr_psi=round(p1hr, 3),
        radius_of_investigation_ft=round(r_inv, 1),
        regimes=regimes,
    )


@dataclass
class BuildupResult:
    permeability_md: float
    skin: float
    slope_psi_per_cycle: float
    p_star_psi: float
    p1hr_psi: float
    regimes: FlowRegimes


def analyze_buildup(
    time: np.ndarray,
    pressure: np.ndarray,
    rate: float,
    viscosity: float,
    total_compressibility: float,
    porosity: float,
    wellbore_radius: float,
    producing_time: float,
    p_wf_at_shutin: float,
    net_pay: float,
    formation_volume_factor: float = 1.0,
    derivative_smoothing: float = 0.0,
) -> BuildupResult:
    """Horner buildup analysis.

    ``time`` is shut-in time ``Δt`` (hours); ``pressure`` is the shut-in
    pressure ``p_ws`` (psia); ``producing_time`` is ``tp`` (hours) prior to
    shut-in; ``p_wf_at_shutin`` is the flowing pressure immediately before
    shut-in (psia). Recover permeability and skin from the Horner line.
    """
    dt, p = _series(time, pressure)
    for name, v in {
        "rate": rate,
        "viscosity": viscosity,
        "total_compressibility": total_compressibility,
        "porosity": porosity,
        "wellbore_radius": wellbore_radius,
        "producing_time": producing_time,
        "p_wf_at_shutin": p_wf_at_shutin,
        "formation_volume_factor": formation_volume_factor,
        "net_pay": net_pay,
    }.items():
        if not math.isfinite(v) or v <= 0:
            raise ValueError(f"{name} must be a positive finite value")

    htime = horner_time(producing_time, dt)
    # Horner time decreases as shut-in time grows; work on an ascending axis.
    order = np.argsort(htime)
    htime_sorted = htime[order]
    p_sorted = p[order]
    derivative = bourdet_derivative(htime_sorted, p_sorted, derivative_smoothing)
    regimes = identify_flow_regimes(htime_sorted, derivative)

    mask = None
    if regimes.radial is not None:
        mask = (htime_sorted >= regimes.radial[0]) & (htime_sorted <= regimes.radial[1])
    slope, intercept = _semilog(htime_sorted, p_sorted, mask)

    m = abs(slope)  # psi/cycle (Horner slope is negative for buildup)
    k = 162.6 * rate * formation_volume_factor * viscosity / (m * net_pay)

    # p* is the extrapolation to infinite shut-in (Horner time -> 1, log10 -> 0).
    p_star = intercept
    # p1hr is the pressure at dt = 1 hr, i.e. Horner time (tp + 1)/1.
    p1hr = slope * math.log10(producing_time + 1.0) + intercept

    skin = 1.1513 * (
        (p1hr - p_wf_at_shutin) / m
        - math.log10(k / (porosity * viscosity * total_compressibility * wellbore_radius ** 2))
        + 3.2275
    )

    return BuildupResult(
        permeability_md=round(k, 3),
        skin=round(skin, 3),
        slope_psi_per_cycle=round(slope, 4),
        p_star_psi=round(p_star, 3),
        p1hr_psi=round(p1hr, 3),
        regimes=regimes,
    )
