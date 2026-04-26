import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN
import tensorflow as tf
from typing import List  # Removed Dict, Optional, Tuple
import xgboost as xgb
from scipy.stats import gaussian_kde

# Required for seasonal_decompose, ensure statsmodels is in requirements if not already
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.model_selection import train_test_split

# Required for linkage, fcluster
from scipy.cluster.hierarchy import linkage, fcluster
import json  # For export_analysis


class AdvancedDataAnalysis:
    """Sistema avançado de análise de dados e IA para petróleo e gás"""

    def __init__(self):
        self.data = {}
        self.models = {}
        self.transformers = {}
        self.clusters = {}
        self.patterns = {}

    def load_production_data(self, df: pd.DataFrame):  # Changed filename to df
        """Carrega e pré-processa dados de produção"""
        # df = pd.read_csv(filename) # Assuming df is already loaded

        # Detectar e tratar outliers
        for col in df.select_dtypes(include=[np.number]).columns:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            # Clip data to be within 1.5*IQR of Q1 and Q3
            df[col] = df[col].clip(lower=q1 - 1.5 * iqr, upper=q3 + 1.5 * iqr)

        self.data["production"] = (
            df.copy()
        )  # Use a copy to avoid modifying original DataFrame

    def analyze_production_patterns(self):
        """Análise avançada de padrões de produção"""
        if "production" not in self.data:
            raise ValueError("Dados de produção não carregados")

        # Make a copy to avoid SettingWithCopyWarning
        df = self.data["production"].copy()

        # Análise de tendências
        for col in ["oil_rate", "gas_rate", "water_rate"]:
            if col in df.columns:
                # Ensure column is numeric and has enough non-NaN values for rolling window
                if (
                    pd.api.types.is_numeric_dtype(df[col])
                    and df[col].notna().sum() >= 30
                ):
                    df[f"{col}_trend"] = (
                        df[col].rolling(window=30, min_periods=1).mean()
                    )

                    # Sazonalidade usando decomposição
                    # Ensure enough data points for seasonal decomposition (e.g., > 2*period)
                    if len(df[col].dropna()) > 2 * 30:  # period is 30
                        try:
                            decomposition = seasonal_decompose(
                                df[col].dropna(), period=30, extrapolate_trend="freq"
                            )
                            # Align seasonal component with original dataframe index
                            seasonal_comp = pd.Series(
                                index=df[col].dropna().index,
                                data=decomposition.seasonal,
                            )
                            df[f"{col}_seasonal"] = seasonal_comp.reindex(df.index)
                        except Exception as e:
                            print(
                                f"Could not compute seasonal decomposition for {col}: {e}"
                            )
                            df[f"{col}_seasonal"] = np.nan

                    # Detecção de eventos
                    df[f"{col}_events"] = self._detect_events(df[col])
                else:
                    print(
                        f"Skipping trend/seasonal analysis for {col} due to "
                        "insufficient data or non-numeric type."
                    )

        self.data["production_analysis"] = df

    def _detect_events(self, series: pd.Series) -> pd.Series:
        """Detecta eventos significativos na série temporal"""
        # Calcular mudanças percentuais
        changes = series.pct_change().fillna(0)  # fillna to handle first element

        # Definir thresholds
        std_dev = changes.std()
        events = pd.Series(index=series.index, data=False, dtype=bool)

        # Marcar eventos significativos
        # Avoid division by zero if std_dev is 0
        if std_dev > 1e-9:  # Check if std_dev is not effectively zero
            events[abs(changes) > 2 * std_dev] = True

        return events

    def cluster_wells(
        self, features: List[str]
    ):  # Removed n_clusters as DBSCAN determines it
        """Agrupa poços com características similares usando DBSCAN"""
        if "production" not in self.data:
            raise ValueError("Dados de produção não carregados")

        # Preparar dados
        X = (
            self.data["production"][features].dropna().values
        )  # dropna before processing
        if X.shape[0] == 0:
            raise ValueError("No data available for clustering after dropping NaNs.")

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Clustering usando DBSCAN
        dbscan = DBSCAN(eps=0.5, min_samples=5)
        clusters = dbscan.fit_predict(X_scaled)

        self.clusters["wells"] = {
            "labels": clusters,
            "features": features,
            "scaler": scaler,
        }

    def analyze_spatial_patterns(
        self, coordinates: pd.DataFrame, value_column: str
    ):  # Added value_column
        """Analisa padrões espaciais de produção"""
        if (
            "production" not in self.data
        ):  # This method might not directly use self.data["production"]
            # but rather specific coordinate data and a value column.
            # Consider if this check is appropriate or if it should be more generic.
            print(
                "Warning: Production data not loaded, but spatial analysis might "
                "proceed if coordinates are provided."
            )

        if not all(col in coordinates.columns for col in ["x", "y", value_column]):
            raise ValueError(
                f"Coordinates DataFrame must contain 'x', 'y', and '{value_column}' columns."
            )

        # Extract x, y, and values for KDE
        x = coordinates["x"].values
        y = coordinates["y"].values
        values = coordinates[value_column].values

        # Filter out NaNs from coordinates and values as KDE cannot handle them
        valid_indices = ~np.isnan(x) & ~np.isnan(y) & ~np.isnan(values)
        x_valid = x[valid_indices]
        y_valid = y[valid_indices]
        values_valid = values[valid_indices]

        if len(x_valid) < 2:  # KDE needs at least 2 points
            print("Warning: Not enough valid data points for KDE spatial analysis.")
            self.patterns["spatial"] = None
            return

        # Kernel Density Estimation on coordinates, weighted by the value_column
        # gaussian_kde doesn't directly support weighted KDE in the way needed for
        # spatial density of a value. A common approach is to perform KDE on
        # coordinates and then interpolate values, or use a different method.
        # For simplicity, let's do KDE on coordinates and store it.
        # If values are to represent density, they should be used as weights, which
        # KDE can do.
        try:
            kde = gaussian_kde(np.vstack([x_valid, y_valid]), weights=values_valid)
        except np.linalg.LinAlgError as e:
            print(
                "Singular matrix in KDE, possibly due to collinear points or "
                f"insufficient data: {e}"
            )
            # Fallback: KDE without weights if weighted fails and there are enough points
            if len(x_valid) > 1:  # Check if there are enough points for unweighted KDE
                try:
                    kde = gaussian_kde(np.vstack([x_valid, y_valid]))
                except np.linalg.LinAlgError as e_unweighted:
                    print(f"Unweighted KDE also failed: {e_unweighted}")
                    self.patterns["spatial"] = None
                    return
            else:  # Not enough points for unweighted KDE either
                self.patterns["spatial"] = None
                return

        # Criar superfície de densidade
        xi, yi = np.mgrid[
            x_valid.min() : x_valid.max() : 100j, y_valid.min() : y_valid.max() : 100j
        ]
        zi = kde(np.vstack([xi.flatten(), yi.flatten()]))

        self.patterns["spatial"] = {
            "density": zi.reshape(xi.shape),
            "x_grid": xi,
            "y_grid": yi,
            "value_column": value_column,
        }

    def train_production_predictor(self, features: List[str], target: str):
        """Treina modelo de ML para previsão de produção"""
        if "production" not in self.data:
            raise ValueError("Dados de produção não carregados")

        df = self.data["production"].copy()  # Use a copy

        # Preparar dados
        X = df[features].dropna()  # Drop rows with NaNs in features
        y = df.loc[X.index, target]  # Align target with X after dropping NaNs

        if X.empty or y.empty:
            raise ValueError(
                "Not enough data after handling NaNs for training production predictor."
            )

        # Dividir dados
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Treinar XGBoost
        model = xgb.XGBRegressor(
            objective="reg:squarederror",
            n_estimators=100,
            learning_rate=0.1,
            random_state=42,
        )
        model.fit(X_train, y_train)

        # Avaliar modelo
        score = model.score(X_test, y_test)
        predictions = model.predict(X_test)

        self.models[f"{target}_predictor"] = {
            "model": model,
            "features": features,
            "score": score,
            "predictions": predictions,
            "actual": y_test.values,  # Store actual values as numpy array
        }

    def analyze_well_correlations(self):
        """Analisa correlações entre poços"""
        if "production" not in self.data:
            raise ValueError("Dados de produção não carregados")

        # Pivot data to have wells as columns and time as index for correlation
        # Assuming 'date' or a time index, 'well_id', and 'oil_rate' (example)
        # This needs a clear definition of how wells are correlated (e.g., their
        # production rates over time)
        # For simplicity, let's assume a pivot table exists or can be made.
        # Example: df_pivot = self.data["production"].pivot(index='date', columns='well_id', values='oil_rate')
        # If not, correlation matrix on raw feature columns might not be meaningful for
        # "well correlations"

        # Using numeric columns for general correlation, not specifically "well"
        # correlation yet
        numeric_df = self.data["production"].select_dtypes(include=np.number).dropna()
        if numeric_df.shape[1] < 2:  # Need at least 2 columns for correlation
            print("Not enough numeric columns for correlation analysis.")
            self.patterns["correlations"] = None
            return

        corr_matrix = numeric_df.corr()

        # Hierarchical clustering on the correlation matrix
        # Ensure the matrix is suitable for linkage (e.g. not all NaNs)
        if not corr_matrix.isnull().all().all() and corr_matrix.shape[0] > 1:
            try:
                linkage_matrix_val = linkage(corr_matrix.values, method="ward")
                # The criterion 't' for fcluster depends on the scale of distances in
                # linkage_matrix. A common approach is to use a max number of
                # clusters or a distance threshold. For now, using a placeholder
                # distance; this might need tuning.
                clusters = fcluster(linkage_matrix_val, t=1.5, criterion="distance")
            except Exception as e:
                print(
                    "Could not perform hierarchical clustering on correlation matrix: "
                    f"{e}"
                )
                clusters = None
        else:
            clusters = None

        self.patterns["correlations"] = {"matrix": corr_matrix, "clusters": clusters}

    def reduce_dimensionality(self, features: List[str], n_components: int = 2):
        """Reduz dimensionalidade dos dados para visualização"""
        if "production" not in self.data:
            raise ValueError("Dados de produção não carregados")

        # Preparar dados
        X = self.data["production"][features].dropna().values  # dropna
        if X.shape[0] == 0:
            raise ValueError("No data available for PCA after dropping NaNs.")

        # PCA
        # Ensure n_components is not more than available features or samples
        n_samples, n_features = X.shape
        actual_n_components = min(n_components, n_features, n_samples)
        if actual_n_components < 1:
            raise ValueError("Not enough features or samples for PCA.")

        pca = PCA(n_components=actual_n_components)
        X_reduced = pca.fit_transform(X)

        self.transformers["pca"] = {
            "transformer": pca,
            "features": features,
            "transformed_data": X_reduced,
            "explained_variance": pca.explained_variance_ratio_,
        }

    def analyze_production_decline(self, date_col: str, rate_col: str):  # Added params
        """Analisa declínio de produção usando ML"""
        if "production" not in self.data:
            raise ValueError("Dados de produção não carregados")

        df = self.data["production"].copy()  # Use a copy

        if date_col not in df.columns or rate_col not in df.columns:
            raise ValueError(f"Missing required columns: '{date_col}' or '{rate_col}'")

        # Ensure date_col is datetime
        try:
            df[date_col] = pd.to_datetime(df[date_col])
        except Exception as e:
            raise ValueError(f"Could not convert '{date_col}' to datetime: {e}")

        df = df.sort_values(by=date_col)  # Sort by date

        # Criar features de tempo (days since first production day in the dataset)
        df["days_online"] = (df[date_col] - df[date_col].min()).dt.days

        # Treinar modelo de declínio (simple feedforward NN)
        model = tf.keras.Sequential(
            [
                tf.keras.layers.Dense(
                    64, activation="relu", input_shape=(1,)
                ),  # Input is 'days_online'
                tf.keras.layers.Dense(32, activation="relu"),
                tf.keras.layers.Dense(1),  # Output is the rate
            ]
        )

        model.compile(optimizer="adam", loss="mse")

        # Treinar em dados históricos (non-NaN rates)
        train_df = df[[rate_col, "days_online"]].dropna()
        if train_df.empty:
            raise ValueError(f"No valid data in '{rate_col}' for decline analysis.")

        X = train_df["days_online"].values.reshape(-1, 1)
        y = train_df[rate_col].values

        model.fit(X, y, epochs=100, verbose=0, batch_size=32)  # Added batch_size

        # Fazer previsões for a future period (e.g., 365 days past last known day)
        last_day = X.max() if X.size > 0 else 0
        future_days = np.arange(last_day + 1, last_day + 365 + 1).reshape(-1, 1)
        predictions = model.predict(future_days)

        self.models["decline_curve"] = {
            "model": model,
            "predictions": predictions.flatten(),  # Flatten predictions
            "future_days": future_days.flatten(),  # Flatten days
            "rate_col_used": rate_col,
        }

    def export_analysis(self, filename: str):
        """Exporta resultados da análise para JSON"""

        # Helper to convert numpy arrays to lists for JSON serialization
        def convert_to_list(item):
            if isinstance(item, np.ndarray):
                return item.tolist()
            if isinstance(item, pd.DataFrame):
                return item.to_dict(orient="records")  # Or other format
            if isinstance(item, pd.Series):
                return item.tolist()
            return item

        results = {
            "clusters": {
                k: convert_to_list(v.get("labels"))
                for k, v in self.clusters.items()
                if "labels" in v
            },
            "patterns": {},
            "model_scores": {
                k: v.get("score") for k, v in self.models.items() if "score" in v
            },
        }

        # Handle patterns, which might have mixed types including numpy arrays
        for k, v_dict in self.patterns.items():
            results["patterns"][k] = {}
            if isinstance(v_dict, dict):
                for sub_k, sub_v in v_dict.items():
                    results["patterns"][k][sub_k] = convert_to_list(sub_v)
            else:
                results["patterns"][k] = convert_to_list(v_dict)

        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
