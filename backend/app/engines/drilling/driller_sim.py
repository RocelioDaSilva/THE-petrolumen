"""Driller's method and drilling operations simulation."""

from __future__ import annotations

import numpy as np
import pandas as pd


def simulate_driller_method(
    duration_hours: float = 24.0,
    dt_min: float = 1.0,
    initial_rop: float = 10.0,
    decay_constant_hours: float = 24.0,
) -> pd.DataFrame:
    """Simulate rate of penetration and cumulative measured depth over time.

    Args:
        duration_hours: Total simulation duration in hours
        dt_min: Time step interval in minutes
        initial_rop: Initial ROP in m/h
        decay_constant_hours: Exponential decay parameter in hours

    Returns:
        DataFrame with time_h, rop, and md columns
    """
    if duration_hours <= 0 or dt_min <= 0:
        raise ValueError("Duration and time step must be strictly positive.")
    if initial_rop < 0:
        raise ValueError("Initial ROP must be non-negative.")
    if decay_constant_hours <= 0:
        raise ValueError("Decay constant must be strictly positive.")

    steps = int(duration_hours * 60.0 / dt_min)
    times = np.arange(steps, dtype=float) * (dt_min / 60.0)
    rop = initial_rop * np.exp(-times / decay_constant_hours)
    md = np.cumsum(rop * (dt_min / 60.0))

    return pd.DataFrame({"time_h": times, "rop": rop, "md": md})
