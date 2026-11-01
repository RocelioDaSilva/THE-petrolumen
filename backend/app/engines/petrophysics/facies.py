"""Facies classification engine using machine learning for well log interpretation."""

from __future__ import annotations

from typing import Any, Sequence
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split


def train_facies_classifier(
    df: pd.DataFrame,
    features: Sequence[str] | None = None,
    target_col: str = "facies",
    test_size: float = 0.2,
    random_state: int = 42,
    n_estimators: int = 200,
) -> tuple[RandomForestClassifier, dict[str, Any], np.ndarray]:
    """Train a Random Forest classifier for facies classification from well log curves.

    Parameters:
        df: Input DataFrame containing log curves and facies labels.
        features: List of feature column names to use. Default is
                  ['gamma', 'resistivity', 'density', 'porosity'].
        target_col: Column name containing facies class labels.
        test_size: Ratio of data reserved for evaluation testing (0.0 to 1.0).
        random_state: Random state seed for reproducibility.
        n_estimators: Number of decision trees in the random forest.

    Returns:
        tuple containing:
            - Trained RandomForestClassifier instance.
            - Classification evaluation metrics dictionary.
            - Predictions array on the test set.

    Raises:
        ValueError: If required columns are missing or if DataFrame is empty.
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    if features is None:
        features = ["gamma", "resistivity", "density", "porosity"]

    missing_features = [f for f in features if f not in df.columns]
    if missing_features:
        raise ValueError(f"Missing required feature columns: {missing_features}")

    if target_col not in df.columns:
        raise ValueError(f"Missing target column: '{target_col}'")

    if not (0.0 < test_size < 1.0) and len(df) > 1:
        raise ValueError("test_size must be between 0.0 and 1.0.")

    # Impute missing values with column median
    x_features = df[list(features)].copy()
    for col in features:
        median_val = x_features[col].median()
        if pd.isna(median_val):
            median_val = 0.0
        x_features[col] = x_features[col].fillna(median_val)

    y_target = df[target_col]

    if len(df) < 5:
        # Small dataset fallback: train on full dataset
        x_train, x_test, y_train, y_test = x_features, x_features, y_target, y_target
    else:
        x_train, x_test, y_train, y_test = train_test_split(
            x_features, y_target, test_size=test_size, random_state=random_state
        )

    clf = RandomForestClassifier(n_estimators=n_estimators, random_state=random_state)
    clf.fit(x_train, y_train)

    preds = clf.predict(x_test)
    report = classification_report(y_test, preds, output_dict=True, zero_division=0)

    return clf, report, preds


def predict_facies(
    clf: RandomForestClassifier,
    df: pd.DataFrame,
    features: Sequence[str] | None = None,
) -> np.ndarray:
    """Predict facies classifications for new log data using a trained model.

    Parameters:
        clf: Trained classifier model.
        df: Input DataFrame containing log curves.
        features: Feature column names corresponding to training features.

    Returns:
        1D numpy array of predicted facies class labels.

    Raises:
        ValueError: If DataFrame is empty or required features are missing.
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    if features is None:
        features = ["gamma", "resistivity", "density", "porosity"]

    missing_features = [f for f in features if f not in df.columns]
    if missing_features:
        raise ValueError(f"Missing required feature columns: {missing_features}")

    x_features = df[list(features)].copy()
    for col in features:
        median_val = x_features[col].median()
        if pd.isna(median_val):
            median_val = 0.0
        x_features[col] = x_features[col].fillna(median_val)

    return clf.predict(x_features)
