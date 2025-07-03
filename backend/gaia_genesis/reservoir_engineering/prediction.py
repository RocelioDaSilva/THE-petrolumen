from typing import List, Any, Tuple, Dict
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib # For saving/loading models
import os

import logging
logger = logging.getLogger(__name__)

class AIPrediction:
    def __init__(self):
        self.trained_models: Dict[str, Any] = {}

    def prepare_data(self, data: pd.DataFrame, target_column: str,
                     feature_columns: List[str], test_size: float = 0.2,
                     random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Preprocesses data for AI model training. Returns X_train, X_test, y_train, y_test."""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Input data must be a pandas DataFrame.")
        if target_column not in data.columns:
            raise ValueError(f"Target column '{target_column}' not found in DataFrame.")
        for col in feature_columns:
            if col not in data.columns:
                raise ValueError(f"Feature column '{col}' not found in DataFrame.")

        X = data[feature_columns]
        y = data[target_column]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
        logger.info(f"Data prepared: X_train shape {X_train.shape}, X_test shape {X_test.shape}")
        return X_train, X_test, y_train, y_test

    def train_models(self, X_train: pd.DataFrame, y_train: pd.Series) -> Dict[str, Any]:
        """Trains AI models (e.g., Linear Regression as a placeholder). Returns trained models."""
        if X_train.empty or y_train.empty:
            logger.error("Training data (X_train or y_train) is empty.")
            return {}

        self.trained_models = {} # Clear any previous models

        # --- Linear Regression ---
        try:
            lr_model = LinearRegression()
            lr_model.fit(X_train, y_train)
            self.trained_models['linear_regression'] = lr_model
            logger.info("Linear Regression model trained successfully.")
        except Exception as e:
            logger.exception(f"Error training Linear Regression model: {e}")

        # --- Support Vector Regressor (SVR) ---
        try:
            svr_model = SVR()
            # Basic GridSearchCV for SVR
            param_grid_svr = {'C': [0.1, 1, 10], 'gamma': ['scale', 'auto']}
            grid_search_svr = GridSearchCV(SVR(), param_grid_svr, cv=2, n_jobs=-1) # cv=2 for speed in example
            grid_search_svr.fit(X_train, y_train)
            self.trained_models['svr'] = grid_search_svr.best_estimator_
            logger.info(f"SVR model trained successfully with best params: {grid_search_svr.best_params_}")
        except Exception as e:
            logger.exception(f"Error training SVR model: {e}")

        # --- Random Forest Regressor ---
        try:
            rf_model = RandomForestRegressor(random_state=42, n_jobs=-1)
            # Basic GridSearchCV for Random Forest
            param_grid_rf = {'n_estimators': [50, 100], 'max_depth': [None, 5, 10]} # Reduced grid for speed
            grid_search_rf = GridSearchCV(RandomForestRegressor(random_state=42, n_jobs=-1), param_grid_rf, cv=2)
            grid_search_rf.fit(X_train, y_train)
            self.trained_models['random_forest'] = grid_search_rf.best_estimator_
            logger.info(f"Random Forest Regressor model trained successfully with best params: {grid_search_rf.best_params_}")
        except Exception as e:
            logger.exception(f"Error training Random Forest Regressor model: {e}")

        if not self.trained_models:
            logger.error("No models were trained successfully.")
            return {}

        return self.trained_models

    def predict(self, X_test: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Makes predictions using trained models."""
        if not self.trained_models:
            logger.warning("No models trained yet. Call train_models first.")
            return {}
        if X_test.empty:
            logger.error("Test data (X_test) is empty.")
            return {}

        predictions: Dict[str, np.ndarray] = {}
        for model_name, model in self.trained_models.items():
            try:
                preds = model.predict(X_test)
                predictions[model_name] = preds
                logger.info(f"Predictions made using {model_name}.")
            except Exception as e:
                logger.exception(f"Error making predictions with {model_name}: {e}") # Changed to logger.exception
        return predictions

    def plot_predictions(self, y_test: pd.Series, predictions: Dict[str, np.ndarray]) -> str:
        """Generates plots of actual vs. predicted values."""
        if y_test.empty:
            return "y_test data is empty. Cannot plot."
        if not predictions:
            return "No predictions available to plot."

        # Placeholder for plotting logic (e.g., using Matplotlib or Plotly)
        # For each model in predictions:
        #   plt.figure()
        #   plt.scatter(y_test, predictions[model_name], alpha=0.5)
        #   plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'k--', lw=2) # Diagonal line
        #   plt.xlabel("Actual Values")
        #   plt.ylabel("Predicted Values")
        #   plt.title(f"Actual vs. Predicted - {model_name}")
        #   plt.show()

        plot_messages = []
        for model_name in predictions.keys():
            plot_messages.append(f"Plot for actual vs. predicted values for {model_name} would be generated here.")
        logger.info("Placeholder: Plot predictions called.")
        return "\n".join(plot_messages)


    def save_model(self, model_name: str, model_path: str) -> str:
        """Saves a trained AI model."""
        if model_name not in self.trained_models:
            logger.error(f"Model '{model_name}' not found in trained models for saving.")
            return f"Error: Model '{model_name}' not found."

        model = self.trained_models[model_name]
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            joblib.dump(model, model_path)
            logger.info(f"Model '{model_name}' saved to {model_path}")
            return f"Model '{model_name}' saved successfully to {model_path}"
        except Exception as e:
            logger.exception(f"Error saving model {model_name} to {model_path}: {e}")
            return f"Error saving model {model_name}: {str(e)}"

    def load_model(self, model_name: str, model_path: str) -> bool:
        """Loads a trained AI model and adds it to trained_models."""
        try:
            if not os.path.exists(model_path):
                logger.error(f"Model file not found at {model_path} for loading '{model_name}'.")
                return False
            model = joblib.load(model_path)
            self.trained_models[model_name] = model
            logger.info(f"Model '{model_name}' loaded successfully from {model_path}")
            return True
        except Exception as e:
            logger.exception(f"Error loading model {model_name} from {model_path}: {e}")
            return False

    # _hyperparameter_tuning method is removed as tuning is now integrated into train_models via GridSearchCV.

    def _evaluate_performance(self, y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
        """Evaluates the performance of a model."""
        if y_true.empty or len(y_pred) == 0:
            logger.warning("Cannot evaluate performance with empty true values or predictions.")
            return {}
        if len(y_true) != len(y_pred):
            logger.error("Length of y_true and y_pred must be the same for evaluation.")
            return {}

        try:
            mse = mean_squared_error(y_true, y_pred)
            rmse = np.sqrt(mse)
            r2 = r2_score(y_true, y_pred)
            metrics = {'mse': mse, 'rmse': rmse, 'r2': r2}
            logger.info(f"Model performance: MSE={mse:.4f}, RMSE={rmse:.4f}, R2={r2:.4f}")
            return metrics
        except Exception as e:
            logger.exception(f"Error during performance evaluation: {e}") # Changed to logger.exception
            return {}

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    ai_predictor = AIPrediction()

    # Create sample data
    data = pd.DataFrame({
        'feature1': np.random.rand(100),
        'feature2': np.random.rand(100) * 10,
        'target': 2 * np.random.rand(100) + 3 * np.random.rand(100) * 10 + 5 + np.random.randn(100) # y = 2*f1 + 3*f2 + 5 + noise
    })
    feature_cols = ['feature1', 'feature2']
    target_col = 'target'

    X_train, X_test, y_train, y_test = ai_predictor.prepare_data(data, target_col, feature_cols)

    if not X_train.empty:
        trained_models = ai_predictor.train_models(X_train, y_train)
        print("Trained models:", trained_models)

        if trained_models:
            predictions = ai_predictor.predict(X_test)
            print("\nPredictions:", predictions)

            if predictions and 'linear_regression' in predictions:
                lr_preds = predictions['linear_regression']
                performance = ai_predictor._evaluate_performance(y_test, lr_preds)
                print("\nLinear Regression Performance:", performance)

            plot_msg = ai_predictor.plot_predictions(y_test, predictions)
            print("\nPlot Message:", plot_msg)

            save_msg = ai_predictor.save_model('linear_regression', 'linear_regression_model.pkl')
            print("\nSave Model Message:", save_msg)

            tuning_params = ai_predictor._hyperparameter_tuning(X_train, y_train, 'linear_regression')
            print("\nHyperparameter Tuning (placeholder):", tuning_params)
    else:
        print("Failed to prepare data or train models.")
