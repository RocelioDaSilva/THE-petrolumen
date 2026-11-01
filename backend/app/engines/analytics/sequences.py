"""Time-series sequence transformations and normalization routines for predictive modeling."""

from __future__ import annotations

from typing import Sequence
import numpy as np
import pandas as pd


def normalize_timeseries(
    series: Sequence[float] | np.ndarray | pd.Series,
    fill_method: str = "ffill",
) -> tuple[np.ndarray, float, float]:
    """Normalize time-series data to standard zero-mean and unit-variance.

    z = (x - mean) / std

    Parameters:
        series: 1D array-like time series data.
        fill_method: Imputation method for NaNs ('ffill' or 'mean').

    Returns:
        tuple containing:
            - Normalized 1D numpy array.
            - Mean of the original series.
            - Standard deviation of the original series.

    Raises:
        ValueError: If input series is empty or cannot be converted.
    """
    arr = np.asarray(series, dtype=np.float64)
    if arr.size == 0:
        raise ValueError("Input series cannot be empty.")

    # Handle NaNs
    if np.isnan(arr).any():
        s = pd.Series(arr)
        if fill_method == "ffill":
            arr = s.ffill().bfill().to_numpy()
        else:
            arr = s.fillna(s.mean()).to_numpy()

    mean_val = float(np.mean(arr))
    std_val = float(np.std(arr))

    if std_val == 0.0 or np.isnan(std_val):
        normalized = np.zeros_like(arr)
        std_val = 1.0
    else:
        normalized = (arr - mean_val) / std_val

    return normalized, mean_val, std_val


def create_sequences(
    arr: Sequence[float] | np.ndarray,
    window: int = 12,
    horizon: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate sliding window input-target sequences for time-series forecasting.

    Given sequence [x_0, x_1, ..., x_{N-1}], extracts pairs of:
        X[i] = [x_i, x_{i+1}, ..., x_{i+window-1}]
        y[i] = x_{i+window+horizon-1}

    Parameters:
        arr: 1D or 2D array-like sequence of values.
        window: Historical window size (number of time steps).
        horizon: Forecasting step ahead (default 1).

    Returns:
        tuple containing:
            - X: 2D numpy array of shape (N - window - horizon + 1, window)
            - y: 1D numpy array of targets of length (N - window - horizon + 1)

    Raises:
        ValueError: If window is non-positive or larger than array length.
    """
    data = np.asarray(arr)
    if data.ndim == 0 or len(data) == 0:
        raise ValueError("Array must not be empty.")

    if window <= 0:
        raise ValueError(f"Window size must be positive, got {window}.")

    if horizon <= 0:
        raise ValueError(f"Horizon must be positive, got {horizon}.")

    total_required = window + horizon - 1
    n_samples = len(data) - total_required

    if n_samples <= 0:
        raise ValueError(
            f"Array length ({len(data)}) must be strictly greater than window + horizon - 1 ({total_required})."
        )

    x_list = []
    y_list = []
    for i in range(n_samples):
        x_list.append(data[i : i + window])
        y_list.append(data[i + window + horizon - 1])

    return np.array(x_list), np.array(y_list)
