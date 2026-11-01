"""Rate of Penetration (ROP) prediction and physics engine.

Combines machine-learning regression with standard analytical petroleum equations
sourced from Carter, Lyons & Lapeyrouse (5th Ed., 2023), Chapter 7.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split


def rop_mud_effects(rop1_ft_hr: float, mw1_ppg: float, mw2_ppg: float) -> float:
    """Calculate ROP change resulting from mud weight alteration.

    Equation:
        ROP2 = ROP1 * (MW1 / MW2)^2

    Parameters:
        rop1_ft_hr: Baseline rate of penetration (ft/hr).
        mw1_ppg: Original mud weight (ppg).
        mw2_ppg: New mud weight (ppg).

    Returns:
        Adjusted rate of penetration (ft/hr).

    Raises:
        ValueError: If mud weights are non-positive.
    """
    if rop1_ft_hr < 0:
        raise ValueError(f"Baseline ROP must be non-negative, got {rop1_ft_hr}")
    if mw1_ppg <= 0 or mw2_ppg <= 0:
        raise ValueError("Mud weights must be strictly positive.")
    return round(rop1_ft_hr * ((mw1_ppg / mw2_ppg) ** 2), 2)


def cuttings_concentration(
    rop_ft_hr: float,
    bit_diameter_in: float,
    flow_rate_gpm: float,
) -> float:
    """Calculate volumetric cuttings concentration in the drilling annulus.

    Equations:
        q_cuttings (bbl/min) = (ROP * Bit_Diameter^2) / (1471 * 60)
        q_mud (bbl/min) = Flow_Rate / 42
        Ca (%) = (q_cuttings / (q_cuttings + q_mud)) * 100

    Parameters:
        rop_ft_hr: Drilling rate of penetration (ft/hr).
        bit_diameter_in: Bit diameter (inches).
        flow_rate_gpm: Annular mud pump circulation rate (gal/min).

    Returns:
        Annular cuttings concentration percentage (%).

    Raises:
        ValueError: If parameters are negative or zero pump rate with non-zero ROP.
    """
    if rop_ft_hr < 0 or bit_diameter_in <= 0 or flow_rate_gpm < 0:
        raise ValueError("Invalid negative drilling geometry or flow rate.")

    q_cuttings_bbl_min = (rop_ft_hr * (bit_diameter_in ** 2)) / (1471.0 * 60.0)
    q_mud_bbl_min = flow_rate_gpm / 42.0

    total_flow = q_cuttings_bbl_min + q_mud_bbl_min
    if total_flow <= 0:
        return 0.0

    ca = (q_cuttings_bbl_min / total_flow) * 100.0
    return round(ca, 2)


def d_exponent(
    rop_ft_hr: float,
    rpm: float,
    wob_klbs: float,
    bit_diameter_in: float,
    mw_actual_ppg: float = 9.0,
    mw_normal_ppg: float = 9.0,
) -> tuple[float, float]:
    """Calculate Jordan and Shirley d-exponent and corrected d-exponent (dc).

    Equations:
        d = log10(ROP / (60 * RPM)) / log10(12 * WOB / (1000 * Bit_Diameter))
        dc = d * (MW_normal / MW_actual)

    Parameters:
        rop_ft_hr: Rate of penetration (ft/hr).
        rpm: Rotary table speed (RPM).
        wob_klbs: Weight on bit (thousand lbs / klbs).
        bit_diameter_in: Bit diameter (inches).
        mw_actual_ppg: Actual circulating mud weight (ppg).
        mw_normal_ppg: Normal formation pore pressure equivalent gradient (ppg, default 9.0).

    Returns:
        tuple containing (d_exp, d_exp_corrected).

    Raises:
        ValueError: If input variables lead to undefined logarithms or division by zero.
    """
    if rop_ft_hr <= 0 or rpm <= 0 or wob_klbs <= 0 or bit_diameter_in <= 0:
        raise ValueError("Drilling parameters (ROP, RPM, WOB, Bit Diameter) must be strictly positive.")
    if mw_actual_ppg <= 0:
        raise ValueError("Actual mud weight must be positive.")

    ratio_wob = (12.0 * wob_klbs) / (1000.0 * bit_diameter_in)
    if ratio_wob <= 0:
        raise ValueError("Invalid non-positive WOB/diameter ratio.")
    if abs(ratio_wob - 1.0) < 1e-12:
        raise ValueError("Denominator in d-exponent evaluated to zero (log10(1) = 0).")

    num = math.log10(rop_ft_hr / (60.0 * rpm))
    denom = math.log10(ratio_wob)

    if denom == 0:
        raise ValueError("Denominator in d-exponent evaluated to zero.")

    d = num / denom
    dc = d * (mw_normal_ppg / mw_actual_ppg)
    return round(d, 4), round(dc, 4)


def train_rop_model(
    df: pd.DataFrame,
    features: Sequence[str] | None = None,
    target_col: str = "ROP",
    test_size: float = 0.2,
    random_state: int = 42,
    n_estimators: int = 100,
) -> tuple[Any, dict[str, float], np.ndarray]:
    """Train a machine-learning regressor for ROP forecasting.

    Utilizes XGBoost if installed; otherwise falls back gracefully to
    RandomForestRegressor from scikit-learn.

    Parameters:
        df: Input drilling DataFrame.
        features: Feature columns (default: ['WOB', 'RPM', 'torque', 'mud_weight']).
        target_col: Drilling target column (default: 'ROP').
        test_size: Ratio reserved for testing (0.0 to 1.0).
        random_state: Reproducibility seed.
        n_estimators: Number of boosting trees or forest estimators.

    Returns:
        tuple containing:
            - Trained regressor model.
            - Metrics dictionary with 'rmse' and 'mae'.
            - Test prediction array.

    Raises:
        ValueError: If required columns are missing or DataFrame is empty.
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    if features is None:
        features = ["WOB", "RPM", "torque", "mud_weight"]

    missing = [f for f in features if f not in df.columns]
    if missing:
        raise ValueError(f"Missing required features: {missing}")

    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found.")

    x_features = df[list(features)].ffill().bfill()
    y_target = df[target_col].ffill().bfill()

    if len(df) < 5:
        x_train, x_test, y_train, y_test = x_features, x_features, y_target, y_target
    else:
        x_train, x_test, y_train, y_test = train_test_split(
            x_features, y_target, test_size=test_size, random_state=random_state
        )

    try:
        from xgboost import XGBRegressor  # type: ignore

        model = XGBRegressor(n_estimators=n_estimators, random_state=random_state)
    except ImportError:
        model = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state)

    model.fit(x_train, y_train)
    preds = model.predict(x_test)

    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    mae = float(mean_absolute_error(y_test, preds))

    return model, {"rmse": round(rmse, 4), "mae": round(mae, 4)}, preds


def predict_rop(
    model: Any,
    df: pd.DataFrame,
    features: Sequence[str] | None = None,
) -> np.ndarray:
    """Generate ROP predictions for new drilling parameters.

    Parameters:
        model: Trained ROP regressor model.
        df: Input DataFrame with drilling sensor attributes.
        features: Features to extract.

    Returns:
        1D numpy array of predicted ROP values.
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    if features is None:
        features = ["WOB", "RPM", "torque", "mud_weight"]

    missing = [f for f in features if f not in df.columns]
    if missing:
        raise ValueError(f"Missing required features: {missing}")

    x_features = df[list(features)].ffill().bfill()
    return np.asarray(model.predict(x_features))
