import xgboost as xgb
import joblib
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score


class AIPredictor:
    pass


class AIPrediction:
    def __init__(self, models_dir: str = "trained_ai_models"):
        self.models_dir = models_dir
        self.models = {}
        self.best_model = None
        self.feature_columns = []

    def prepare_data(self, df, target, features):
        self.feature_columns = features
        X = df[features]
        y = df[target]
        return train_test_split(X, y, test_size=0.2, random_state=42)

    def train_models(self, X_train, y_train, X_test, y_test):
        model = xgb.XGBRegressor(n_estimators=100)
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        self.best_model = "xgboost"
        self.models["xgboost"] = {
            "model": model,
            "test_r2": r2_score(y_test, preds),
            "test_rmse": np.sqrt(mean_squared_error(y_test, preds)),
        }

    def predict(self, df, model_name=None):
        name = model_name or self.best_model
        return self.models[name]["model"].predict(df[self.feature_columns])

    def save_model(self, path, model_name=None):
        name = model_name or self.best_model
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.models[name], path)

    def load_model(self, path):
        data = joblib.load(path)
        name = os.path.basename(path).replace(".joblib", "")
        self.models[name] = data
        self.best_model = name
        self.feature_columns = data.get("features", [])
        return name

    def __init__(self, model_dir: str = "trained_ai_models"):
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        self.model = None

    def train_xgboost(self, df: pd.DataFrame, target: str, features: List[str]) -> Dict:
        X = df[features]
        y = df[target]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5)
        self.model.fit(X_train, y_train)

        preds = self.model.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        r2 = r2_score(y_test, preds)

        return {"rmse": float(rmse), "r2": float(r2)}

    def save_model(self, model_name: str):
        if self.model:
            joblib.dump(
                self.model, os.path.join(self.model_dir, f"{model_name}.joblib")
            )

    def load_model(self, model_name: str):
        self.model = joblib.load(os.path.join(self.model_dir, f"{model_name}.joblib"))

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.model:
            return self.model.predict(X)
        return np.array([])
