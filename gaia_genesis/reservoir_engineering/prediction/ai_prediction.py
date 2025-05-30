import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
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
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('AIPrediction')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def prepare_data(self,
                    data: pd.DataFrame,
                    target_column: str,
                    feature_columns: List[str],
                    test_size: float = 0.2) -> Tuple:
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
        X = data[feature_columns]
        y = data[target_column]
        
        # Normaliza features
        X_scaled = self.scaler.fit_transform(X)
        
        # Divide em treino e teste
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=42
        )
        
        return X_train, X_test, y_train, y_test
        
    def train_models(self,
                    X_train: np.ndarray,
                    y_train: np.ndarray,
                    X_test: np.ndarray,
                    y_test: np.ndarray):
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
            'kernel': ['rbf', 'linear'],
            'C': [0.1, 1, 10],
            'epsilon': [0.1, 0.2, 0.3]
        }
        
        xgb_params = {
            'n_estimators': [100, 200],
            'max_depth': [3, 5, 7],
            'learning_rate': [0.01, 0.1]
        }
        
        # Treina SVR
        svr = SVR()
        svr_grid = GridSearchCV(svr, svr_params, cv=5, scoring='r2')
        svr_grid.fit(X_train, y_train)
        
        self.models['svr'] = {
            'model': svr_grid.best_estimator_,
            'params': svr_grid.best_params_,
            'score': svr_grid.best_score_
        }
        
        # Treina XGBoost
        xgb = XGBRegressor()
        xgb_grid = GridSearchCV(xgb, xgb_params, cv=5, scoring='r2')
        xgb_grid.fit(X_train, y_train)
        
        self.models['xgb'] = {
            'model': xgb_grid.best_estimator_,
            'params': xgb_grid.best_params_,
            'score': xgb_grid.best_score_
        }
        
        # Avalia modelos
        for name, model_info in self.models.items():
            y_pred = model_info['model'].predict(X_test)
            r2 = r2_score(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            
            model_info.update({
                'test_r2': r2,
                'test_rmse': rmse,
                'predictions': y_pred
            })
            
        # Seleciona melhor modelo
        best_model = max(self.models.items(),
                        key=lambda x: x[1]['test_r2'])
        self.best_model = best_model[0]
        
        # Calcula importância das features (XGBoost)
        if 'xgb' in self.models:
            self.feature_importance = pd.DataFrame({
                'feature': self.feature_columns,
                'importance': self.models['xgb']['model'].feature_importances_
            }).sort_values('importance', ascending=False)
            
    def predict(self,
               X: np.ndarray,
               model_name: Optional[str] = None) -> np.ndarray:
        """
        Faz previsões.
        
        Args:
            X: Features
            model_name: Nome do modelo (opcional)
            
        Returns:
            Array com previsões
        """
        if model_name:
            if model_name not in self.models:
                raise ValueError(f"Modelo {model_name} não encontrado")
            model = self.models[model_name]['model']
        else:
            if not self.best_model:
                raise ValueError("Nenhum modelo treinado")
            model = self.models[self.best_model]['model']
            
        X_scaled = self.scaler.transform(X)
        return model.predict(X_scaled)
        
    def plot_predictions(self,
                        X_test: np.ndarray,
                        y_test: np.ndarray,
                        save_path: Optional[str] = None) -> go.Figure:
        """
        Plota resultados das previsões.
        
        Args:
            X_test: Features de teste
            y_test: Target de teste
            save_path: Caminho para salvar figura
            
        Returns:
            Figura do Plotly
        """
        fig = make_subplots(rows=2, cols=1,
                           subplot_titles=('Previsões vs Real',
                                         'Resíduos'))
                                         
        # Dados reais
        fig.add_trace(
            go.Scatter(x=range(len(y_test)), y=y_test,
                      mode='markers',
                      name='Real'),
            row=1, col=1
        )
        
        # Previsões
        for name, model_info in self.models.items():
            fig.add_trace(
                go.Scatter(x=range(len(y_test)),
                          y=model_info['predictions'],
                          mode='lines',
                          name=f'{name.upper()} (R²={model_info["test_r2"]:.3f})'),
                row=1, col=1
            )
            
            # Resíduos
            residuals = y_test - model_info['predictions']
            fig.add_trace(
                go.Scatter(x=range(len(y_test)),
                          y=residuals,
                          mode='markers',
                          name=f'Resíduos {name}'),
                row=2, col=1
            )
            
        fig.update_layout(
            title='Resultados da Predição',
            xaxis_title='Amostra',
            yaxis_title='Valor',
            xaxis2_title='Amostra',
            yaxis2_title='Resíduo',
            showlegend=True
        )
        
        if save_path:
            fig.write_image(save_path)
            
        return fig
        
    def plot_feature_importance(self,
                              save_path: Optional[str] = None) -> go.Figure:
        """
        Plota importância das features.
        
        Args:
            save_path: Caminho para salvar figura
            
        Returns:
            Figura do Plotly
        """
        if self.feature_importance is None:
            raise ValueError("Importância das features não calculada")
            
        fig = go.Figure()
        
        fig.add_trace(
            go.Bar(
                x=self.feature_importance['importance'],
                y=self.feature_importance['feature'],
                orientation='h'
            )
        )
        
        fig.update_layout(
            title='Importância das Features',
            xaxis_title='Importância',
            yaxis_title='Feature',
            showlegend=False
        )
        
        if save_path:
            fig.write_image(save_path)
            
        return fig
        
    def save_model(self, path: str):
        """
        Salva modelo treinado.
        
        Args:
            path: Caminho para salvar modelo
        """
        if not self.best_model:
            raise ValueError("Nenhum modelo treinado")
            
        model_path = Path(path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        joblib.dump({
            'model': self.models[self.best_model]['model'],
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'params': self.models[self.best_model]['params']
        }, model_path)
        
    def load_model(self, path: str):
        """
        Carrega modelo salvo.
        
        Args:
            path: Caminho do modelo
        """
        saved_data = joblib.load(path)
        
        self.models[self.best_model] = {
            'model': saved_data['model'],
            'params': saved_data['params']
        }
        
        self.scaler = saved_data['scaler']
        self.feature_columns = saved_data['feature_columns'] 