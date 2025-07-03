from typing import List, Any, Tuple, Dict
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
# For actual use, you'd import more sophisticated models:
# from xgboost import XGBRegressor
# from sklearn.svm import SVR
# import joblib # For saving/loading models

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

        # Placeholder: Train a simple Linear Regression model
        lr_model = LinearRegression()
        try:
            lr_model.fit(X_train, y_train)
            self.trained_models['linear_regression'] = lr_model
            logger.info("Linear Regression model trained successfully.")
        except Exception as e:
            logger.exception(f"Error training Linear Regression model: {e}") # Changed to logger.exception
            return {}

        # In a real scenario, you would train multiple models (XGBoost, SVR, etc.)
        # and potentially perform hyperparameter tuning.
        # Example:
        # xgb_model = XGBRegressor(random_state=42)
        # xgb_model.fit(X_train, y_train)
        # self.trained_models['xgboost'] = xgb_model

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
            return f"Model '{model_name}' not found in trained models."

        model = self.trained_models[model_name]
        # In a real scenario, use joblib or pickle:
        # try:
        #     joblib.dump(model, model_path)
        #     logger.info(f"Model '{model_name}' saved to {model_path}")
        #     return f"Model '{model_name}' saved to {model_path}"
        # except Exception as e:
        #     logger.error(f"Error saving model {model_name} to {model_path}: {e}")
        #     return f"Error saving model {model_name}: {e}"
        logger.info(f"Placeholder: Model '{model_name}' would be saved to {model_path}.")
        return f"Model '{model_name}' would be saved to {model_path} (placeholder action)."

    def _hyperparameter_tuning(self, X_train: pd.DataFrame, y_train: pd.Series, model_name: str = 'linear_regression') -> Dict[str, Any]:
        """Performs hyperparameter tuning for models (placeholder)."""
        logger.info(f"Placeholder: Hyperparameter tuning for {model_name} would be performed here.")
        # Example for LinearRegression (not many hyperparameters to tune, but for illustration)
        if model_name == 'linear_regression':
            return {'fit_intercept': True, 'positive': False}
        # For XGBoost, you'd use GridSearchCV or RandomizedSearchCV
        # from sklearn.model_selection import GridSearchCV
        # param_grid = {'n_estimators': [100, 200], 'max_depth': [3, 5]}
        # grid_search = GridSearchCV(XGBRegressor(), param_grid, cv=3)
        # grid_search.fit(X_train, y_train)
        # return grid_search.best_params_
        return {"info": f"No actual tuning implemented for {model_name} in this placeholder."}


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
