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

    def prepare_data(self, df: pd.DataFrame, target: str, features: List[str]):
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
            "test_r2": float(r2_score(y_test, preds)),
            "test_rmse": float(np.sqrt(mean_squared_error(y_test, preds))),
        }

    def predict(self, df: pd.DataFrame, model_name: Optional[str] = None) -> np.ndarray:
        name = model_name or self.best_model
        if not name or name not in self.models:
            raise ValueError(f"Model '{name}' not found.")
        return self.models[name]["model"].predict(df[self.feature_columns])

    def save_model(self, path: str, model_name: Optional[str] = None):
        name = model_name or self.best_model
        if not name or name not in self.models:
            raise FileNotFoundError(f"Model '{name}' not found.")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        model_data = {
            "model": self.models[name]["model"],
            "features": self.feature_columns,
            "test_r2": self.models[name].get("test_r2"),
            "test_rmse": self.models[name].get("test_rmse"),
        }
        joblib.dump(model_data, path)

    def load_model(self, path: str) -> str:
        data = joblib.load(path)
        name = os.path.basename(path).replace(".joblib", "")
        if isinstance(data, dict) and "model" in data:
            self.models[name] = data
            self.feature_columns = data.get("features", [])
        else:
            self.models[name] = {"model": data}
            self.feature_columns = []
        self.best_model = name
        return name
