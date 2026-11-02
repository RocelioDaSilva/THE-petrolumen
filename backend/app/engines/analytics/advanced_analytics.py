import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN
import tensorflow as tf
from typing import Dict, List, Optional, Tuple, Union
import xgboost as xgb
from scipy.stats import gaussian_kde

class AdvancedDataAnalysis:
    """Sistema avançado de análise de dados e IA para petróleo e gás"""
    
    def __init__(self):
        self.data = {}
        self.models = {}
        self.transformers = {}
        self.clusters = {}
        self.patterns = {}
        
    def load_production_data(self, filename: Union[str, pd.DataFrame]):
        """Carrega e pré-processa dados de produção"""
        df = (
            filename.copy()
            if isinstance(filename, pd.DataFrame)
            else pd.read_csv(filename)
        )
        
        # Detectar e tratar outliers
        for col in df.select_dtypes(include=[np.number]).columns:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            df[col] = df[col].clip(lower=q1 - 1.5*iqr, upper=q3 + 1.5*iqr)
            
        self.data["production"] = df.copy()
        
    def analyze_production_patterns(self):
        """Análise avançada de padrões de produção"""
        if "production" not in self.data:
            raise ValueError("Dados de produção não carregados")
            
        df = self.data["production"].copy()
        
        # Análise de tendências
        for col in ["oil_rate", "gas_rate", "water_rate"]:
            if col in df.columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    continue
                series = pd.to_numeric(df[col], errors="coerce").replace(
                    [np.inf, -np.inf], np.nan
                )
                if series.notna().sum() < 30:
                    continue

                df[f"{col}_trend"] = series.rolling(
                    window=30, min_periods=1
                ).mean()
                valid_series = series.dropna()
                if len(valid_series) > 60:
                    from statsmodels.tsa.seasonal import seasonal_decompose

                    decomposition = seasonal_decompose(
                        valid_series, period=30, extrapolate_trend="freq"
                    )
                    df[f"{col}_seasonal"] = pd.Series(
                        decomposition.seasonal, index=valid_series.index
                    ).reindex(df.index)
                df[f"{col}_events"] = self._detect_events(series)
                
        self.data["production_analysis"] = df
        
    def _detect_events(self, series: pd.Series) -> pd.Series:
        """Detecta eventos significativos na série temporal"""
        # Calcular mudanças percentuais
        changes = series.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0)
        
        # Definir thresholds
        std_dev = changes.std()
        events = pd.Series(index=series.index, data=False, dtype=bool)
        
        # Marcar eventos significativos
        if np.isfinite(std_dev) and std_dev > 1e-9:
            events[abs(changes) > 2 * std_dev] = True
        
        return events
        
    def cluster_wells(self, features: List[str], n_clusters: Optional[int] = None):
        """Agrupa poços com características similares usando DBSCAN"""
        if "production" not in self.data:
            raise ValueError("Dados de produção não carregados")
            
        # Preparar dados
        X = (
            self.data["production"][features]
            .replace([np.inf, -np.inf], np.nan)
            .dropna()
            .values
        )
        if X.shape[0] == 0:
            raise ValueError("No complete production rows are available for clustering.")
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Clustering usando DBSCAN
        dbscan = DBSCAN(eps=0.5, min_samples=5)
        clusters = dbscan.fit_predict(X_scaled)
        
        self.clusters["wells"] = {
            "labels": clusters,
            "features": features,
            "scaler": scaler
        }
        
    def analyze_spatial_patterns(
        self,
        coordinates: Union[List[Tuple[float, float]], pd.DataFrame],
        value_column: Optional[str] = None,
    ):
        """Analisa padrões espaciais de produção"""
        is_weighted = isinstance(coordinates, pd.DataFrame)
        if not is_weighted and "production" not in self.data:
            raise ValueError("Dados de produção não carregados")

        weights = None
        if is_weighted:
            if value_column is None or not all(
                column in coordinates.columns for column in ("x", "y", value_column)
            ):
                raise ValueError(
                    "Coordinate data must include 'x', 'y', and the value column."
                )
            points = coordinates.loc[:, ["x", "y", value_column]].replace(
                [np.inf, -np.inf], np.nan
            ).dropna()
            x = points["x"].to_numpy(dtype=float)
            y = points["y"].to_numpy(dtype=float)
            weights = points[value_column].to_numpy(dtype=float)
            if np.any(weights < 0) or not np.any(weights > 0):
                raise ValueError("Spatial KDE weights must be non-negative and nonzero.")
        else:
            points_array = np.asarray(coordinates, dtype=float)
            if points_array.ndim != 2 or points_array.shape[1] != 2:
                raise ValueError("Coordinates must have shape (n_points, 2).")
            valid = np.all(np.isfinite(points_array), axis=1)
            x, y = points_array[valid].T if np.any(valid) else (np.array([]), np.array([]))

        if len(x) < 2:
            raise ValueError("At least two valid spatial points are required.")
        try:
            kde = gaussian_kde(np.vstack([x, y]), weights=weights)
        except np.linalg.LinAlgError as error:
            raise ValueError("Spatial points do not span a 2D area for KDE.") from error

        xi, yi = np.mgrid[x.min():x.max():100j, y.min():y.max():100j]
        zi = kde(np.vstack([xi.ravel(), yi.ravel()]))
        
        self.patterns["spatial"] = {
            "density": zi.reshape(xi.shape),
            "x_grid": xi,
            "y_grid": yi,
            "value_column": value_column if is_weighted else None,
        }
        
    def train_production_predictor(self, features: List[str], target: str):
        """Treina modelo de ML para previsão de produção"""
        if "production" not in self.data:
            raise ValueError("Dados de produção não carregados")
            
        df = self.data["production"]
        
        # Preparar dados
        if target in features:
            raise ValueError("Target column cannot also be a predictor.")
        training_data = df.loc[:, features + [target]].replace(
            [np.inf, -np.inf], np.nan
        ).dropna()
        if len(training_data) < 5:
            raise ValueError("At least five complete rows are required for training.")
        X = training_data[features]
        y = training_data[target]
        
        # Dividir dados
        from sklearn.model_selection import train_test_split
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
            "actual": y_test
        }
        
    def analyze_well_correlations(self):
        """Analisa correlações entre poços"""
        if "production" not in self.data:
            raise ValueError("Dados de produção não carregados")
            
        numeric_df = (
            self.data["production"]
            .select_dtypes(include=np.number)
            .replace([np.inf, -np.inf], np.nan)
            .dropna()
        )
        numeric_df = numeric_df.loc[:, numeric_df.nunique() > 1]
        if numeric_df.shape[0] < 2 or numeric_df.shape[1] < 2:
            raise ValueError("At least two varying numeric columns are required.")

        corr_matrix = numeric_df.corr()
        
        # Identificar grupos correlacionados
        from scipy.cluster.hierarchy import linkage, fcluster
        linkage_matrix = linkage(corr_matrix.values, method='ward')
        clusters = fcluster(linkage_matrix, t=1.5, criterion='distance')
        
        self.patterns["correlations"] = {
            "matrix": corr_matrix,
            "clusters": clusters
        }
        
    def reduce_dimensionality(self, features: List[str], n_components: int = 2):
        """Reduz dimensionalidade dos dados para visualização"""
        if "production" not in self.data:
            raise ValueError("Dados de produção não carregados")
            
        # Preparar dados
        X = (
            self.data["production"][features]
            .replace([np.inf, -np.inf], np.nan)
            .dropna()
            .values
        )
        if X.shape[0] == 0:
            raise ValueError("No complete production rows are available for PCA.")
        actual_components = min(n_components, X.shape[0], X.shape[1])
        if actual_components < 1:
            raise ValueError("n_components and feature count must be positive.")
        
        # PCA
        pca = PCA(n_components=actual_components)
        X_reduced = pca.fit_transform(X)
        
        self.transformers["pca"] = {
            "transformer": pca,
            "features": features,
            "transformed_data": X_reduced,
            "explained_variance": pca.explained_variance_ratio_
        }
        
    def analyze_production_decline(
        self, date_col: str = "date", rate_col: str = "oil_rate"
    ):
        """Analisa declínio de produção usando ML"""
        if "production" not in self.data:
            raise ValueError("Dados de produção não carregados")

        if date_col not in self.data["production"].columns:
            raise ValueError(f"Missing date column: '{date_col}'.")
        if rate_col not in self.data["production"].columns:
            raise ValueError(f"Missing production-rate column: '{rate_col}'.")

        df = self.data["production"].copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="raise")
        df = df.sort_values(date_col)
        df["days_online"] = (df[date_col] - df[date_col].min()).dt.days
        training_data = df[["days_online", rate_col]].replace(
            [np.inf, -np.inf], np.nan
        ).dropna()
        if training_data.empty:
            raise ValueError(f"No valid data in '{rate_col}' for decline analysis.")
        
        # Treinar modelo de declínio
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(1,)),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse')
        
        # Treinar em dados históricos
        X = training_data["days_online"].values.reshape(-1, 1)
        y = training_data[rate_col].values
        
        model.fit(X, y, epochs=100, verbose=0)
        
        # Fazer previsões
        future_days = np.arange(X.max() + 1, X.max() + 366).reshape(-1, 1)
        predictions = model.predict(future_days)
        
        self.models["decline_curve"] = {
            "model": model,
            "predictions": predictions,
            "future_days": future_days,
            "rate_col_used": rate_col,
        }
        
    def export_analysis(self, filename: str):
        """Exporta resultados da análise"""
        def convert_to_json(value):
            if isinstance(value, np.ndarray):
                return value.tolist()
            if isinstance(value, (pd.DataFrame, pd.Series)):
                return value.to_dict(orient="records") if isinstance(
                    value, pd.DataFrame
                ) else value.tolist()
            if isinstance(value, dict):
                return {key: convert_to_json(item) for key, item in value.items()}
            if isinstance(value, (list, tuple)):
                return [convert_to_json(item) for item in value]
            if isinstance(value, np.generic):
                return value.item()
            return value

        results = {
            "clusters": {
                key: convert_to_json(value.get("labels"))
                for key, value in self.clusters.items()
                if isinstance(value, dict) and "labels" in value
            },
            "patterns": convert_to_json(self.patterns),
            "model_scores": {
                key: value["score"]
                for key, value in self.models.items()
                if isinstance(value, dict) and "score" in value
            },
        }
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
