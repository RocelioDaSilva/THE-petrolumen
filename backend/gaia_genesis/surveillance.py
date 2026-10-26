import pandas as pd
import numpy as np


def calculate_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates GOR, WOR, and Water Cut from production data.
    """
    if "oil_rate" in df.columns and "gas_rate" in df.columns:
        df["gor"] = df["gas_rate"] / df["oil_rate"].replace(0, np.nan)
    if "oil_rate" in df.columns and "water_rate" in df.columns:
        df["wor"] = df["water_rate"] / df["oil_rate"].replace(0, np.nan)
        df["water_cut"] = df["water_rate"] / (
            df["oil_rate"] + df["water_rate"]
        ).replace(0, np.nan)
    return df


def detect_anomalies(
    series: pd.Series, window: int = 7, threshold: float = 2.0
) -> pd.Series:
    """
    Detects anomalies using rolling Z-score.
    """
    rolling_mean = series.rolling(window=window).mean()
    rolling_std = series.rolling(window=window).std()
    z_score = (series - rolling_mean) / rolling_std
    return np.abs(z_score) > threshold
