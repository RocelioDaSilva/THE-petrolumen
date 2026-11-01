"""Wellbore 3D directional trajectory engine."""

from __future__ import annotations

import pandas as pd

from app.utils.math_utils import min_curvature


def compute_trajectory_minimum_curvature(
    df: pd.DataFrame,
    md_col: str = "md",
    inc_col: str = "inc",
    azi_col: str = "azi",
) -> pd.DataFrame:
    """Compute x (East), y (North), z (TVD) coordinates from directional survey DataFrame.

    Args:
        df: Input DataFrame containing survey data
        md_col: Column name for measured depth
        inc_col: Column name for inclination (degrees)
        azi_col: Column name for azimuth (degrees)

    Returns:
        DataFrame with added x, y, and z columns
    """
    res = df.copy()
    md = res[md_col].to_numpy()
    inc = res[inc_col].to_numpy()
    azi = res[azi_col].to_numpy()

    x, y, z = min_curvature(md, inc, azi)
    res["x"] = x
    res["y"] = y
    res["z"] = z
    return res
