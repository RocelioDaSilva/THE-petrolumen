"""Time-series anomaly and event detection engine."""

from __future__ import annotations

import numpy as np
import pandas as pd


def detect_zscore(
    df: pd.DataFrame,
    col: str,
    window: int = 50,
    thresh: float = 4.0,
) -> pd.Index:
    """Detect anomalies in time series column using rolling median and z-score.

    Args:
        df: Input DataFrame with time index
        col: Target column name
        window: Rolling window size
        thresh: Z-score threshold for anomaly flag

    Returns:
        Index of detected anomalies
    """
    roll = df[col].rolling(window, min_periods=1, center=True).median()
    roll_std = df[col].rolling(window, min_periods=1).std().replace(0, np.nan)
    z = (df[col] - roll) / roll_std
    return df.index[np.abs(z) > thresh]
