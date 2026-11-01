"""Mathematical and geometric utilities for petroleum engineering."""

from __future__ import annotations

import numpy as np


def deg2rad(d: float | np.ndarray) -> float | np.ndarray:
    """Convert degrees to radians."""
    return d * np.pi / 180.0


def min_curvature(
    md: list[float] | np.ndarray,
    inc: list[float] | np.ndarray,
    azi: list[float] | np.ndarray,
) -> tuple[list[float], list[float], list[float]]:
    """Compute 3D wellbore trajectory coordinates (North/East/TVD) using Minimum Curvature Method.

    Args:
        md: Measured Depth list/array
        inc: Inclination in degrees
        azi: Azimuth in degrees

    Returns:
        (x, y, z) lists representing East (dx), North (dy), and TVD (dz)
    """
    x = [0.0]
    y = [0.0]
    z = [0.0]

    for i in range(1, len(md)):
        md1, md0 = float(md[i]), float(md[i - 1])
        inc1, inc0 = deg2rad(float(inc[i])), deg2rad(float(inc[i - 1]))
        azi1, azi0 = deg2rad(float(azi[i])), deg2rad(float(azi[i - 1]))
        d_md = md1 - md0

        cos_dogleg = np.cos(inc0) * np.cos(inc1) + np.sin(inc0) * np.sin(inc1) * np.cos(azi1 - azi0)
        cos_dogleg = np.clip(cos_dogleg, -1.0, 1.0)
        theta = float(np.arccos(cos_dogleg))

        if abs(theta) < 1e-6:
            rf = 1.0
        else:
            rf = 2.0 / theta * np.tan(theta / 2.0)

        dx = d_md / 2.0 * (np.sin(inc0) * np.sin(azi0) + np.sin(inc1) * np.sin(azi1)) * rf
        dy = d_md / 2.0 * (np.sin(inc0) * np.cos(azi0) + np.sin(inc1) * np.cos(azi1)) * rf
        dz = d_md / 2.0 * (np.cos(inc0) + np.cos(inc1)) * rf

        x.append(x[-1] + float(dx))
        y.append(y[-1] + float(dy))
        z.append(z[-1] + float(dz))

    return x, y, z
