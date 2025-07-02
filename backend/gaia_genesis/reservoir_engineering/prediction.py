import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
# AI Models - e.g., XGBoost, SVR. Ensure these are installed.
import xgboost as xgb
from sklearn.svm import SVR
import matplotlib.pyplot as plt
import joblib # For saving/loading models

class AIPrediction:
    def __init__(self, models_to_train=None):
        """
        Initializes the AIPrediction class.
        models_to_train: A list or dict specifying models to use, e.g., ['xgboost', 'svr']
                         or {'xgboost': xgb.XGBRegressor(), 'svr': SVR()}.
                         If None, defaults to XGBoost and SVR.
        """
        if models_to_train is None:
            self.models = {
                'xgboost': xgb.XGBRegressor(objective='reg:squarederror', random_state=42),
                'svr': SVR()
            }
        elif isinstance(models_to_train, dict):
            self.models = models_to_train
        elif isinstance(models_to_train, list):
            self.models = {}
            if 'xgboost' in models_to_train:
                self.models['xgboost'] = xgb.XGBRegressor(objective='reg:squarederror', random_state=42)
            if 'svr' in models_to_train:
                self.models['svr'] = SVR()
            # Add other models here if specified by name
        else:
            raise ValueError("models_to_train should be a dict, list, or None.")

        self.trained_models = {}
        self.scalers = {} # To store scalers for features and target if used
        self.best_params = {}
        self.performance_metrics = {}

    def prepare_data(self, data: pd.DataFrame, target_column: str, feature_columns: list[str],
                     test_size=0.2, random_state=42, scale_features=True, scale_target=False):
        """
        Prepares data for AI model training: splits, scales.
        Returns X_train, X_test, y_train, y_test
        """
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Data must be a pandas DataFrame.")
        if target_column not in data.columns:
            raise ValueError(f"Target column '{target_column}' not found in DataFrame.")
        for col in feature_columns:
            if col not in data.columns:
                raise ValueError(f"Feature column '{col}' not found in DataFrame.")

        X = data[feature_columns]
        y = data[target_column]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

        if scale_features:
            self.scalers['features'] = StandardScaler()
            X_train = self.scalers['features'].fit_transform(X_train)
            X_test = self.scalers['features'].transform(X_test)
            # Convert back to DataFrame for compatibility if needed by some models, though numpy array is fine for sklearn
            X_train = pd.DataFrame(X_train, columns=feature_columns, index=X_train.index if isinstance(X_train, pd.DataFrame) else None)
            X_test = pd.DataFrame(X_test, columns=feature_columns, index=X_test.index if isinstance(X_test, pd.DataFrame) else None)


        if scale_target:
            self.scalers['target'] = StandardScaler()
            y_train = self.scalers['target'].fit_transform(y_train.values.reshape(-1, 1)).ravel()
            y_test = self.scalers['target'].transform(y_test.values.reshape(-1, 1)).ravel()
            # y_train and y_test are now numpy arrays

        return X_train, X_test, y_train, y_test

    def train_models(self, X_train, y_train, X_test=None, y_test=None, hyperparam_tuning=False, cv_folds=3):
        """
        Trains AI models. Optionally performs hyperparameter tuning and evaluates.
        """
        if isinstance(X_train, pd.DataFrame): X_train = X_train.values
        if isinstance(X_test, pd.DataFrame) and X_test is not None: X_test = X_test.values


        for name, model_instance in self.models.items():
            print(f"Training {name}...")
            current_model = model_instance # Use the instance from self.models

            if hyperparam_tuning:
                param_grid = self._get_param_grid(name)
                if param_grid:
                    print(f"Performing GridSearchCV for {name}...")
                    grid_search = GridSearchCV(current_model, param_grid, cv=cv_folds, scoring='neg_mean_squared_error', n_jobs=-1)
                    grid_search.fit(X_train, y_train)
                    self.trained_models[name] = grid_search.best_estimator_
                    self.best_params[name] = grid_search.best_params_
                    print(f"Best params for {name}: {self.best_params[name]}")
                else:
                    print(f"No hyperparameter grid defined for {name}. Training with default parameters.")
                    current_model.fit(X_train, y_train)
                    self.trained_models[name] = current_model
            else:
                current_model.fit(X_train, y_train)
                self.trained_models[name] = current_model

            print(f"{name} training complete.")

            if X_test is not None and y_test is not None:
                y_pred = self.trained_models[name].predict(X_test)
                if 'target' in self.scalers: # Inverse transform if target was scaled
                    y_pred = self.scalers['target'].inverse_transform(y_pred.reshape(-1, 1)).ravel()
                    y_test_eval = self.scalers['target'].inverse_transform(y_test.reshape(-1, 1)).ravel()
                else:
                    y_test_eval = y_test

                mse = mean_squared_error(y_test_eval, y_pred)
                r2 = r2_score(y_test_eval, y_pred)
                self.performance_metrics[name] = {'mse': mse, 'r2': r2}
                print(f"Performance for {name} on test set: MSE={mse:.4f}, R2={r2:.4f}")


    def _get_param_grid(self, model_name):
        """Helper to return parameter grids for GridSearchCV."""
        if model_name == 'xgboost':
            return {
                'n_estimators': [100, 200],
                'learning_rate': [0.01, 0.1],
                'max_depth': [3, 5],
                # 'subsample': [0.7, 1.0],
                # 'colsample_bytree': [0.7, 1.0]
            }
        elif model_name == 'svr':
            return {
                'C': [0.1, 1, 10],
                'gamma': ['scale', 'auto', 0.01, 0.1],
                'kernel': ['rbf', 'linear']
            }
        return None # No grid for other models by default

    def predict(self, X_new, model_name=None):
        """
        Makes predictions using a trained AI model.
        If model_name is None, uses the first available trained model.
        X_new: New data for prediction, should be preprocessed (scaled) like training data.
        """
        if not self.trained_models:
            raise RuntimeError("No models have been trained yet.")

        if model_name:
            if model_name not in self.trained_models:
                raise ValueError(f"Model '{model_name}' not found or not trained.")
            model_to_use = self.trained_models[model_name]
        else: # Use the first model if no name specified
            model_name = list(self.trained_models.keys())[0]
            model_to_use = self.trained_models[model_name]
            print(f"No model_name specified, using '{model_name}'.")

        # Ensure X_new is in the correct format (e.g., numpy array)
        # and scaled if features were scaled during training.
        if isinstance(X_new, pd.DataFrame):
            X_new_processed = X_new.values
        else:
            X_new_processed = X_new # Assuming it's already a numpy array or similar

        if 'features' in self.scalers:
             # If X_new was a DataFrame, ensure columns match before transform
            if isinstance(X_new, pd.DataFrame) and list(X_new.columns) != self.scalers['features'].feature_names_in_.tolist():
                 raise ValueError("X_new columns do not match columns used for training scaler.")
            X_new_processed = self.scalers['features'].transform(X_new_processed)


        predictions = model_to_use.predict(X_new_processed)

        if 'target' in self.scalers: # Inverse transform if target was scaled
            predictions = self.scalers['target'].inverse_transform(predictions.reshape(-1, 1)).ravel()

        return predictions

    def plot_predictions(self, y_test, y_pred, model_name, title_suffix="", file_path=None):
        """Generates plots of actual vs. predicted values."""
        plt.figure(figsize=(10, 6))
        plt.scatter(y_test, y_pred, alpha=0.7, edgecolors='k')
        plt.plot([min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())],
                 [min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())],
                 'k--', lw=2) # Diagonal line
        plt.xlabel('Actual Values')
        plt.ylabel('Predicted Values')
        plt.title(f'Actual vs. Predicted Values for {model_name} {title_suffix}')
        plt.grid(True)
        if file_path:
            plt.savefig(file_path)
            print(f"Prediction plot saved to {file_path}")
        else:
            plt.show()

    def save_model(self, model_name: str, model_path: str):
        """Saves a trained AI model and its associated scaler."""
        if model_name not in self.trained_models:
            raise ValueError(f"Model '{model_name}' not found or not trained.")

        model_data = {
            'model': self.trained_models[model_name],
            'feature_scaler': self.scalers.get('features', None),
            'target_scaler': self.scalers.get('target', None),
            'best_params': self.best_params.get(model_name, None),
            'performance': self.performance_metrics.get(model_name, None)
        }
        joblib.dump(model_data, model_path)
        print(f"Model '{model_name}' and scalers saved to {model_path}")

    @classmethod
    def load_model(cls, model_path: str):
        """Loads a trained AI model and its scalers. Returns an AIPrediction instance."""
        model_data = joblib.load(model_path)

        # Create an instance of AIPrediction, perhaps with the model name
        # This part is a bit tricky as the class structure would need to accommodate this
        # For now, let's assume we are loading one specific model into a new instance.
        model_name = "loaded_model" # Or try to infer from model_data if stored

        # A bit of a workaround: create a dummy instance then populate it
        ai_predictor = cls(models_to_train={model_name: model_data['model']}) # Pass the model instance
        ai_predictor.trained_models[model_name] = model_data['model']
        if model_data.get('feature_scaler'):
            ai_predictor.scalers['features'] = model_data['feature_scaler']
        if model_data.get('target_scaler'):
            ai_predictor.scalers['target'] = model_data['target_scaler']
        if model_data.get('best_params'):
            ai_predictor.best_params[model_name] = model_data['best_params']
        if model_data.get('performance'):
            ai_predictor.performance_metrics[model_name] = model_data['performance']

        print(f"Model loaded from {model_path} into '{model_name}' key.")
        return ai_predictor, model_name # Return model_name to know how it's stored


# Example Usage:
if __name__ == '__main__':
    # Generate some dummy data for regression
    np.random.seed(42)
    X_data = np.random.rand(100, 3)  # 100 samples, 3 features
    # A simple linear relationship with some noise for y
    y_data = X_data[:, 0] * 2 - X_data[:, 1] * 1.5 + X_data[:, 2] * 0.5 + np.random.normal(0, 0.5, 100)

    df = pd.DataFrame(X_data, columns=['feature1', 'feature2', 'feature3'])
    df['target'] = y_data

    ai_pred = AIPrediction() # Uses default XGBoost and SVR

    # 1. Prepare data
    X_train, X_test, y_train, y_test = ai_pred.prepare_data(
        df,
        target_column='target',
        feature_columns=['feature1', 'feature2', 'feature3'],
        scale_features=True,
        scale_target=True # Let's test target scaling
    )
    print(f"\nData prepared. X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")

    # 2. Train models (with hyperparameter tuning for XGBoost as an example)
    # For SVR, we'll train without explicit tuning in this run to save time, but it's supported.
    ai_pred_tuned = AIPrediction(models_to_train={'xgboost': xgb.XGBRegressor(random_state=42)})
    ai_pred_tuned.scalers = ai_pred.scalers # Share scalers if split done outside

    print("\n--- Training XGBoost with Hyperparameter Tuning ---")
    ai_pred_tuned.train_models(X_train, y_train, X_test, y_test, hyperparam_tuning=True)

    # Train all default models (XGBoost, SVR) without tuning on the original ai_pred instance
    print("\n--- Training Default Models (XGBoost, SVR) without extensive tuning ---")
    # Re-use original ai_pred instance that has both models defined
    # We need to ensure the models are fresh if we are re-training
    ai_pred = AIPrediction()
    ai_pred.scalers = ai_pred_tuned.scalers # Copy scalers from the instance that did prepare_data

    ai_pred.train_models(X_train, y_train, X_test, y_test, hyperparam_tuning=False) # No tuning for this run

    # 3. Make predictions (using the first model trained in ai_pred, likely XGBoost)
    if ai_pred.trained_models:
        # To predict, X_test needs to be in the same format as during training
        # If prepare_data returned DataFrames, use them. If numpy, use those.
        # Our prepare_data returns DataFrames for X, and numpy for y if scaled.
        # The predict method handles scaling internally if scalers are present.
        # X_test_df = pd.DataFrame(X_test, columns=['feature1', 'feature2', 'feature3']) # if X_test is numpy

        # Use the X_test that came from prepare_data (already DataFrame if not scaled, or became one after scaling)
        predictions = ai_pred.predict(X_test) # X_test is already correctly formatted from prepare_data

        # y_test for plotting should be original scale if target was scaled
        y_test_orig_scale = y_test
        if 'target' in ai_pred.scalers:
            y_test_orig_scale = ai_pred.scalers['target'].inverse_transform(y_test.reshape(-1,1)).ravel()

        print(f"\nSample Predictions (first 5): {predictions[:5]}")
        print(f"Actual Values (first 5): {y_test_orig_scale[:5]}")

        # 4. Plot predictions for one of the models
        chosen_model_for_plot = list(ai_pred.trained_models.keys())[0]
        ai_pred.plot_predictions(y_test_orig_scale, predictions, model_name=chosen_model_for_plot, file_path=f"{chosen_model_for_plot}_predictions.png")

        # 5. Save and Load a model
        model_to_save = list(ai_pred.trained_models.keys())[0] # e.g., xgboost
        model_file = f"{model_to_save}_model.joblib"
        ai_pred.save_model(model_to_save, model_file)

        loaded_predictor, loaded_model_name = AIPrediction.load_model(model_file)
        print(f"\nModel '{loaded_model_name}' loaded successfully.")
        print(f"Scaler for features loaded: {'features' in loaded_predictor.scalers}")
        print(f"Scaler for target loaded: {'target' in loaded_predictor.scalers}")
        print(f"Original performance of loaded model: {loaded_predictor.performance_metrics.get(loaded_model_name)}")

        # Make a prediction with the loaded model
        # X_test_df_for_loaded = pd.DataFrame(X_test, columns=['feature1', 'feature2', 'feature3']) # if X_test is numpy
        loaded_predictions = loaded_predictor.predict(X_test, model_name=loaded_model_name)
        print(f"Predictions from loaded model (first 5): {loaded_predictions[:5]}")

        # Verify consistency (should be very close)
        np.testing.assert_array_almost_equal(predictions, loaded_predictions)
        print("Predictions from original and loaded model are consistent.")

        # Clean up dummy files
        import os
        if os.path.exists(f"{chosen_model_for_plot}_predictions.png"):
            os.remove(f"{chosen_model_for_plot}_predictions.png")
        if os.path.exists(model_file):
            os.remove(model_file)
    else:
        print("No models were trained successfully to run prediction and saving steps.")

```
