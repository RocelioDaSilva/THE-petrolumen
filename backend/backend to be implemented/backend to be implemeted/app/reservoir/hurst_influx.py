"""Hurst modified steady-state water influx (Craft p. 279)."""
from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class HurstResult:
    we_cumulative_bbl: float
    we_at_points_bbl: tuple[float, ...]


def hurst_cumulative_influx(
    c_prime: float, a_per_day: float, pi_psia: float,
    p_history: list[tuple[float, float]],
) -> HurstResult:
    """Cumulative Hurst influx (Craft p. 279).

    Args:
        c_prime: Hurst influx constant (> 0).
        a_per_day: Time-conversion constant (1/day, > 0).
        pi_psia: Initial pressure, psia (> 0).
        p_history: (t_days, p_psia) list, strictly increasing in t,
            >= 2 points.

    Returns:
        HurstResult.

    Raises:
        ValueError: invalid input.
    """
    if not (c_prime > 0.0):
        raise ValueError(f"c_prime must be > 0, got {c_prime!r}")
    if not (a_per_day > 0.0):
        raise ValueError(f"a_per_day must be > 0, got {a_per_day!r}")
    if not (pi_psia > 0.0):
        raise ValueError(f"pi_psia must be > 0, got {pi_psia!r}")
    if len(p_history) < 2:
        raise ValueError(f"p_history must have >= 2 points")
    for i, (t, p) in enumerate(p_history):
        if not (t >= 0.0):
            raise ValueError(f"p_history[{i}].t_days must be >= 0")
        if not (p > 0.0):
            raise ValueError(f"p_history[{i}].p_psia must be > 0")
        if i > 0 and not (t > p_history[i - 1][0]):
            raise ValueError(f"p_history times must strictly increase")

    cum = [0.0]
    W = 0.0
    for i in range(1, len(p_history)):
        t_prev, p_prev = p_history[i - 1]
        t_cur, p_cur = p_history[i]
        if t_cur <= 0.0:
            cum.append(W)
            continue
        at = a_per_day * t_cur
        if at <= 1.0:
            raise ValueError(
                f"a*t = {at!r} <= 1 at t = {t_cur!r}; log(at) undefined "
                "or negative. Check a_per_day."
            )
        # Trapezoid on dp/log(at) at endpoints
        if t_prev > 0.0:
            at_prev = a_per_day * t_prev
            if at_prev <= 1.0:
                raise ValueError(f"a*t_prev = {at_prev!r} <= 1")
            f_prev = (pi_psia - p_prev) / math.log(at_prev)
        else:
            f_prev = (pi_psia - p_prev) / math.log(at)
        f_cur = (pi_psia - p_cur) / math.log(at)
        W += c_prime * 0.5 * (f_prev + f_cur) * (t_cur - t_prev)
        cum.append(W)
    return HurstResult(
        we_cumulative_bbl=W, we_at_points_bbl=tuple(cum),
    )
