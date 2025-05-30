import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN
import tensorflow as tf
from typing import Dict, List, Optional, Tuple
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
        
    def load_production_data(self, filename: str):
        """Carrega e pré-processa dados de produção"""
        df = pd.read_csv(filename)
        
        # Detectar e tratar outliers
        for col in df.select_dtypes(include=[np.number]).columns:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            df[col] = df[col].clip(lower=q1 - 1.5*iqr, upper=q3 + 1.5*iqr)
            
        self.data["production"] = df
        
    def analyze_production_patterns(self):
        """Análise avançada de padrões de produção"""
        if "production" not in self.data:
            raise ValueError("Dados de produção não carregados")
            
        df = self.data["production"]
        
        # Análise de tendências
        for col in ["oil_rate", "gas_rate", "water_rate"]:
            if col in df.columns:
                # Tendência usando média móvel
                df[f"{col}_trend"] = df[col].rolling(window=30).mean()
                
                # Sazonalidade usando decomposição
                from statsmodels.tsa.seasonal import seasonal_decompose
                decomposition = seasonal_decompose(df[col], period=30, extrapolate_trend='freq')
                df[f"{col}_seasonal"] = decomposition.seasonal
                
                # Detecção de eventos
                df[f"{col}_events"] = self._detect_events(df[col])
                
        self.data["production_analysis"] = df
        
    def _detect_events(self, series: pd.Series) -> pd.Series:
        """Detecta eventos significativos na série temporal"""
        # Calcular mudanças percentuais
        changes = series.pct_change()
        
        # Definir thresholds
        std_dev = changes.std()
        events = pd.Series(index=series.index, data=False)
        
        # Marcar eventos significativos
        events[abs(changes) > 2*std_dev] = True
        
        return events
        
    def cluster_wells(self, features: List[str], n_clusters: Optional[int] = None):
        """Agrupa poços com características similares usando DBSCAN"""
        if "production" not in self.data:
            raise ValueError("Dados de produção não carregados")
            
        # Preparar dados
        X = self.data["production"][features].values
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
        
    def analyze_spatial_patterns(self, coordinates: List[Tuple[float, float]]):
        """Analisa padrões espaciais de produção"""
        if "production" not in self.data:
            raise ValueError("Dados de produção não carregados")
            
        # Criar grid espacial
        x = np.array([coord[0] for coord in coordinates])
        y = np.array([coord[1] for coord in coordinates])
        
        # Kernel Density Estimation
        kde = gaussian_kde(np.vstack([x, y]))
        
        # Criar superfície de densidade
        xi, yi = np.mgrid[x.min():x.max():100j, y.min():y.max():100j]
        zi = kde(np.vstack([xi.flatten(), yi.flatten()]))
        
        self.patterns["spatial"] = {
            "density": zi.reshape(xi.shape),
            "x_grid": xi,
            "y_grid": yi
        }
        
    def train_production_predictor(self, features: List[str], target: str):
        """Treina modelo de ML para previsão de produção"""
        if "production" not in self.data:
            raise ValueError("Dados de produção não carregados")
            
        df = self.data["production"]
        
        # Preparar dados
        X = df[features]
        y = df[target]
        
        # Dividir dados
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        # Treinar XGBoost
        model = xgb.XGBRegressor(
            objective="reg:squarederror",
            n_estimators=100,
            learning_rate=0.1
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
            
        df = self.data["production"]
        
        # Calcular matriz de correlação
        corr_matrix = df.corr()
        
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
        X = self.data["production"][features].values
        
        # PCA
        pca = PCA(n_components=n_components)
        X_reduced = pca.fit_transform(X)
        
        self.transformers["pca"] = {
            "transformer": pca,
            "features": features,
            "transformed_data": X_reduced,
            "explained_variance": pca.explained_variance_ratio_
        }
        
    def analyze_production_decline(self):
        """Analisa declínio de produção usando ML"""
        if "production" not in self.data:
            raise ValueError("Dados de produção não carregados")
            
        df = self.data["production"]
        
        # Criar features de tempo
        df["days_online"] = (df["date"] - df["date"].min()).dt.days
        
        # Treinar modelo de declínio
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(1,)),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse')
        
        # Treinar em dados históricos
        X = df["days_online"].values.reshape(-1, 1)
        y = df["oil_rate"].values
        
        model.fit(X, y, epochs=100, verbose=0)
        
        # Fazer previsões
        future_days = np.arange(X.max(), X.max() + 365).reshape(-1, 1)
        predictions = model.predict(future_days)
        
        self.models["decline_curve"] = {
            "model": model,
            "predictions": predictions,
            "future_days": future_days
        }
        
    def export_analysis(self, filename: str):
        """Exporta resultados da análise"""
        import json
        
        results = {
            "clusters": {k: v["labels"].tolist() for k, v in self.clusters.items()},
            "patterns": {k: v for k, v in self.patterns.items() 
                        if not isinstance(v, (np.ndarray, pd.DataFrame))},
            "model_scores": {k: v["score"] for k, v in self.models.items() 
                           if "score" in v}
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f)
