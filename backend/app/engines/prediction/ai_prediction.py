import numpy as np
import pandas as pd
from typing import List, Optional, Tuple, Dict  # noqa: F401 (Dict is used)
import logging
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.svm import SVR
from xgboost import XGBRegressor
from sklearn.metrics import r2_score, mean_squared_error
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import joblib
from pathlib import Path


class AIPrediction:
    """Classe para predição usando modelos de IA."""

    def __init__(self):
        self.logger = self._setup_logger()
        self.models = {}
        self.scaler = StandardScaler()
        self.best_model = None
        self.feature_importance = None
        self.feature_columns = []  # Initialize feature_columns

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("AIPrediction")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        if not logger.hasHandlers():  # Avoid adding multiple handlers
            logger.addHandler(handler)
        return logger

    def prepare_data(
        self,
        data: pd.DataFrame,
        target_column: str,
        feature_columns: List[str],
        test_size: float = 0.2,
    ) -> Tuple:
        """
        Prepara dados para treinamento.

        Args:
            data: DataFrame com dados
            target_column: Coluna alvo
            feature_columns: Lista de colunas de features
            test_size: Proporção de dados de teste

        Returns:
            Tuple com dados preparados
        """
        if not all(col in data.columns for col in feature_columns):
            missing_cols = [col for col in feature_columns if col not in data.columns]
            raise ValueError(f"Missing feature columns in data: {missing_cols}")
        if target_column not in data.columns:
            raise ValueError(f"Target column '{target_column}' not found in data.")

        X = data[feature_columns]
        y = data[target_column]

        self.feature_columns = feature_columns  # Store feature columns

        # Normaliza features
        X_scaled = self.scaler.fit_transform(X)

        # Divide em treino e teste
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=42
        )

        return X_train, X_test, y_train, y_test

    def train_models(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
    ):
        """
        Treina modelos de IA.

        Args:
            X_train: Features de treino
            y_train: Target de treino
            X_test: Features de teste
            y_test: Target de teste
        """
        # Define parâmetros para Grid Search
        svr_params = {
            "kernel": ["rbf", "linear"],
            "C": [0.1, 1, 10],
            "epsilon": [0.1, 0.2, 0.3],
        }

        xgb_params = {
            "n_estimators": [100, 200],
            "max_depth": [3, 5, 7],
            "learning_rate": [0.01, 0.1],
        }

        # Treina SVR
        self.logger.info("Training SVR model...")
        svr = SVR()
        svr_grid = GridSearchCV(svr, svr_params, cv=5, scoring="r2")
        svr_grid.fit(X_train, y_train)

        self.models["svr"] = {
            "model": svr_grid.best_estimator_,
            "params": svr_grid.best_params_,
            "score": svr_grid.best_score_,
        }
        self.logger.info(
            f"SVR trained. Best params: {svr_grid.best_params_}, Best score: {svr_grid.best_score_:.4f}"
        )

        # Treina XGBoost
        self.logger.info("Training XGBoost model...")
        xgb = XGBRegressor(random_state=42)  # Added random_state for reproducibility
        xgb_grid = GridSearchCV(xgb, xgb_params, cv=5, scoring="r2")
        xgb_grid.fit(X_train, y_train)

        self.models["xgb"] = {
            "model": xgb_grid.best_estimator_,
            "params": xgb_grid.best_params_,
            "score": xgb_grid.best_score_,
        }
        self.logger.info(
            f"XGBoost trained. Best params: {xgb_grid.best_params_}, Best score: {xgb_grid.best_score_:.4f}"
        )

        # Avalia modelos
        active_models = {}
        for name, model_info in self.models.items():
            y_pred = model_info["model"].predict(X_test)
            r2 = r2_score(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))

            model_info.update(
                {
                    "test_r2": r2,
                    "test_rmse": rmse,
                    "predictions": y_pred,  # Storing predictions on X_test for potential plotting
                }
            )
            active_models[name] = model_info
            self.logger.info(
                f"Model {name} evaluated. Test R2: {r2:.4f}, Test RMSE: {rmse:.4f}"
            )

        # Seleciona melhor modelo based on test_r2
        if active_models:
            best_model_item = max(active_models.items(), key=lambda x: x[1]["test_r2"])
            self.best_model = best_model_item[0]
            self.logger.info(
                f"Best model selected: {self.best_model} with Test R2: {best_model_item[1]['test_r2']:.4f}"
            )
        else:
            self.logger.warning("No models were trained or evaluated successfully.")
            self.best_model = None

        # Calcula importância das features (XGBoost)
        if "xgb" in self.models and hasattr(
            self.models["xgb"]["model"], "feature_importances_"
        ):
            if not self.feature_columns:
                self.logger.warning(
                    "Feature columns not set, cannot calculate feature importance names."
                )
                self.feature_importance = None
            else:
                self.feature_importance = pd.DataFrame(
                    {
                        "feature": self.feature_columns,
                        "importance": self.models["xgb"]["model"].feature_importances_,
                    }
                ).sort_values("importance", ascending=False)
                self.logger.info("Feature importance calculated for XGBoost model.")
        else:
            self.feature_importance = None

    def predict(
        self,
        X: pd.DataFrame,  # Changed to DataFrame to use feature_columns
        model_name: Optional[str] = None,
    ) -> np.ndarray:
        """
        Faz previsões.

        Args:
            X: DataFrame com Features
            model_name: Nome do modelo (opcional)

        Returns:
            Array com previsões
        """
        if not self.feature_columns:
            raise ValueError("Feature columns not set. Train or load a model first.")

        # Ensure X has the correct feature columns in the correct order
        try:
            X_ordered = X[self.feature_columns]
        except KeyError as e:
            raise ValueError(
                f"Input data missing required feature columns: {e}. Expected: {self.feature_columns}"
            )

        if model_name:
            if model_name not in self.models:
                raise ValueError(f"Modelo {model_name} não encontrado")
            model_to_use = self.models[model_name]["model"]
            self.logger.info(f"Predicting with specified model: {model_name}")
        else:
            if not self.best_model or self.best_model not in self.models:
                raise ValueError(
                    "Nenhum modelo treinado ou melhor modelo não disponível"
                )
            model_to_use = self.models[self.best_model]["model"]
            self.logger.info(f"Predicting with best model: {self.best_model}")

        X_scaled = self.scaler.transform(X_ordered)  # Use the stored scaler
        return model_to_use.predict(X_scaled)

    def plot_predictions(
        self,
        y_test: np.ndarray,  # X_test is not needed if predictions are stored
        model_name: Optional[str] = None,
        save_path: Optional[str] = None,
    ) -> go.Figure:
        """
        Plota resultados das previsões.

        Args:
            y_test: Target de teste
            model_name: Specific model to plot, or all if None.
            save_path: Caminho para salvar figura

        Returns:
            Figura do Plotly
        """
        fig = make_subplots(
            rows=2, cols=1, subplot_titles=("Previsões vs Real", "Resíduos")
        )

        # Dados reais
        fig.add_trace(
            go.Scatter(
                x=np.arange(len(y_test)),
                y=y_test,
                mode="markers",
                name="Real",
                marker=dict(color="black"),
            ),
            row=1,
            col=1,
        )

        models_to_plot = []
        if model_name:
            if model_name in self.models and "predictions" in self.models[model_name]:
                models_to_plot.append((model_name, self.models[model_name]))
            else:
                self.logger.warning(
                    f"Model {model_name} or its predictions not found for plotting."
                )
        else:  # Plot all models that have predictions
            for name, model_info in self.models.items():
                if "predictions" in model_info:
                    models_to_plot.append((name, model_info))

        if not models_to_plot:
            self.logger.warning("No model predictions available to plot.")
            return fig  # Return empty fig if nothing to plot

        for name, model_info in models_to_plot:
            y_pred = model_info["predictions"]
            test_r2 = model_info.get("test_r2", float("nan"))  # Use .get for safety

            fig.add_trace(
                go.Scatter(
                    x=np.arange(len(y_pred)),
                    y=y_pred,
                    mode="lines",
                    name=f"{name.upper()} (R²={test_r2:.3f})",
                ),
                row=1,
                col=1,
            )

            # Resíduos
            residuals = y_test - y_pred
            fig.add_trace(
                go.Scatter(
                    x=np.arange(len(residuals)),
                    y=residuals,
                    mode="markers",
                    name=f"Resíduos {name.upper()}",
                ),
                row=2,
                col=1,
            )

        fig.update_layout(
            title_text="Resultados da Predição",
            xaxis_title_text="Amostra",
            yaxis_title_text="Valor",
            xaxis2_title_text="Amostra",
            yaxis2_title_text="Resíduo",
            legend_title_text="Modelos",
        )

        if save_path:
            try:
                fig.write_image(save_path)
                self.logger.info(f"Prediction plot saved to {save_path}")
            except Exception as e:
                self.logger.error(f"Failed to save prediction plot: {e}")

        return fig

    def plot_feature_importance(
        self, save_path: Optional[str] = None
    ) -> Optional[go.Figure]:
        """
        Plota importância das features (if available, e.g. for XGBoost).

        Args:
            save_path: Caminho para salvar figura

        Returns:
            Figura do Plotly or None if no importance data
        """
        if self.feature_importance is None or self.feature_importance.empty:
            self.logger.warning("Importância das features não calculada ou vazia.")
            return None

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=self.feature_importance["importance"],
                y=self.feature_importance["feature"],
                orientation="h",
            )
        )

        fig.update_layout(
            title_text="Importância das Features (XGBoost)",
            xaxis_title_text="Importância",
            yaxis_title_text="Feature",
            yaxis=dict(autorange="reversed"),  # Show most important at top
        )

        if save_path:
            try:
                fig.write_image(save_path)
                self.logger.info(f"Feature importance plot saved to {save_path}")
            except Exception as e:
                self.logger.error(f"Failed to save feature importance plot: {e}")

        return fig

    def save_model(self, path: str, model_name: Optional[str] = None):
        """
        Salva modelo treinado.

        Args:
            path: Caminho para salvar modelo (directory if model_name is provided, else full file path)
            model_name: Nome do modelo a ser salvo (se None, salva o best_model)
        """
        model_to_save_name = (
            model_name if model_name and model_name in self.models else self.best_model
        )

        if not model_to_save_name or model_to_save_name not in self.models:
            raise ValueError(
                f"Modelo '{model_to_save_name}' não treinado ou não encontrado."
            )

        model_info = self.models[model_to_save_name]

        model_path = Path(path)
        if model_path.is_dir() or (
            model_name is not None and not model_path.suffix
        ):  # if path is dir or no suffix with model_name
            model_path = model_path / f"{model_to_save_name}_model.joblib"

        model_path.parent.mkdir(parents=True, exist_ok=True)

        data_to_save = {
            "model": model_info["model"],
            "scaler": self.scaler,  # Scaler is common for all models trained with this instance
            "feature_columns": self.feature_columns,  # Feature columns are also common
            "params": model_info.get("params", {}),  # Model specific params
            "model_name": model_to_save_name,
        }

        try:
            joblib.dump(data_to_save, model_path)
            self.logger.info(f"Modelo '{model_to_save_name}' salvo em {model_path}")
        except Exception as e:
            self.logger.error(f"Erro ao salvar modelo '{model_to_save_name}': {e}")
            raise

    def load_model(self, path: str) -> str:
        """
        Carrega modelo salvo. The loaded model becomes the 'best_model' for this instance.

        Args:
            path: Caminho do modelo (.joblib file)

        Returns:
            Nome do modelo carregado.
        """
        model_path = Path(path)
        if not model_path.exists() or not model_path.is_file():
            raise FileNotFoundError(f"Arquivo de modelo não encontrado em {model_path}")

        try:
            saved_data = joblib.load(model_path)
        except Exception as e:
            self.logger.error(f"Erro ao carregar modelo de {model_path}: {e}")
            raise

        loaded_model_name = saved_data.get(
            "model_name", "loaded_model"
        )  # Get name or default

        self.models[loaded_model_name] = {
            "model": saved_data["model"],
            "params": saved_data.get("params", {}),
            # Scores (r2, rmse) are not saved, would be re-evaluated if needed
        }

        self.scaler = saved_data["scaler"]
        self.feature_columns = saved_data["feature_columns"]
        self.best_model = (
            loaded_model_name  # Assume loaded model is the one we want to use
        )

        self.logger.info(
            f"Modelo '{loaded_model_name}' carregado de {model_path}. Feature columns: {self.feature_columns}"
        )
        return loaded_model_name
