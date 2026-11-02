import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, Conv2D, MaxPooling2D, Flatten, Dropout, Input, LSTM, GRU
from tensorflow.keras.applications import ResNet50
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

class DataAnalytics:
    def __init__(self):
        """Inicializa o sistema de análise de dados."""
        self.seismic_data = None
        self.production_data = None
        self.reservoir_data = None
        self.models = {}
        self.dashboard = None
        
    def load_seismic_data(self, data: np.ndarray, metadata: Dict):
        """
        Carrega dados sísmicos.
        
        Args:
            data: Array com dados sísmicos
            metadata: Metadados (coordenadas, frequência, etc.)
        """
        self.seismic_data = {
            'data': data,
            'metadata': metadata
        }
        
    def load_production_data(self, data: pd.DataFrame):
        """
        Carrega dados de produção.
        
        Args:
            data: DataFrame com dados de produção
        """
        self.production_data = data
        
    def load_reservoir_data(self, data: pd.DataFrame):
        """
        Carrega dados de reservatório.
        
        Args:
            data: DataFrame com dados de reservatório
        """
        self.reservoir_data = data
        
    def train_seismic_classifier(self,
                               labels: np.ndarray,
                               model_type: str = 'cnn'):
        """
        Treina classificador para interpretação sísmica.
        
        Args:
            labels: Labels para classificação
            model_type: Tipo de modelo ('cnn', 'resnet')
        """
        if self.seismic_data is None:
            raise ValueError("Dados sísmicos não carregados")
            
        # Preparar dados
        X = self.seismic_data['data']
        y = labels
        
        # Normalizar
        scaler = StandardScaler()
        X = scaler.fit_transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
        
        # Dividir dados
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        if model_type == 'cnn':
            # Criar modelo CNN
            model = Sequential([
                Conv2D(32, (3, 3), activation='relu', input_shape=X.shape[1:]),
                MaxPooling2D((2, 2)),
                Conv2D(64, (3, 3), activation='relu'),
                MaxPooling2D((2, 2)),
                Conv2D(64, (3, 3), activation='relu'),
                Flatten(),
                Dense(64, activation='relu'),
                Dropout(0.5),
                Dense(len(np.unique(y)), activation='softmax')
            ])
            
        else:  # resnet
            # Criar modelo ResNet
            base_model = ResNet50(
                weights='imagenet',
                include_top=False,
                input_shape=X.shape[1:]
            )
            
            x = base_model.output
            x = Flatten()(x)
            x = Dense(1024, activation='relu')(x)
            x = Dropout(0.5)(x)
            predictions = Dense(len(np.unique(y)), activation='softmax')(x)
            
            model = Model(inputs=base_model.input, outputs=predictions)
            
        # Compilar e treinar
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        model.fit(
            X_train, y_train,
            epochs=50,
            batch_size=32,
            validation_data=(X_test, y_test)
        )
        
        # Avaliar modelo
        score = model.evaluate(X_test, y_test)
        print(f"Accuracy: {score[1]:.3f}")
        
        self.models['seismic_classifier'] = model
        
    def analyze_production_patterns(self,
                                  window_size: int = 30,
                                  n_clusters: int = 3):
        """
        Analisa padrões em séries temporais de produção.
        
        Args:
            window_size: Tamanho da janela para análise
            n_clusters: Número de clusters
        """
        if self.production_data is None:
            raise ValueError("Dados de produção não carregados")
            
        # Extrair features
        features = []
        for well in self.production_data['well_name'].unique():
            well_data = self.production_data[self.production_data['well_name'] == well]
            
            # Calcular estatísticas em janela móvel
            for i in range(len(well_data) - window_size + 1):
                window = well_data.iloc[i:i+window_size]
                features.append([
                    window['rate'].mean(),
                    window['rate'].std(),
                    window['rate'].max(),
                    window['rate'].min(),
                    window['water_cut'].mean(),
                    window['pressure'].mean()
                ])
                
        features = np.array(features)
        
        # Normalizar
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Reduzir dimensionalidade
        pca = PCA(n_components=2)
        features_pca = pca.fit_transform(features_scaled)
        
        # Clusterizar
        kmeans = KMeans(n_clusters=n_clusters)
        clusters = kmeans.fit_predict(features_scaled)
        
        # Armazenar resultados
        self.production_patterns = {
            'features': features,
            'features_pca': features_pca,
            'clusters': clusters,
            'scaler': scaler,
            'pca': pca,
            'kmeans': kmeans
        }
        
    def train_reservoir_predictor(self,
                                input_features: List[str],
                                target_feature: str,
                                model_type: str = 'lstm'):
        """
        Treina preditor de performance de reservatório.
        
        Args:
            input_features: Lista de features de entrada
            target_feature: Feature alvo
            model_type: Tipo de modelo ('lstm', 'gru')
        """
        if self.reservoir_data is None:
            raise ValueError("Dados de reservatório não carregados")
            
        # Preparar dados
        X = self.reservoir_data[input_features].values
        y = self.reservoir_data[target_feature].values
        
        # Normalizar
        scaler = StandardScaler()
        X = scaler.fit_transform(X)
        
        # Dividir dados
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        if model_type == 'lstm':
            # Reshape para LSTM
            X_train = X_train.reshape(X_train.shape[0], 1, X_train.shape[1])
            X_test = X_test.reshape(X_test.shape[0], 1, X_test.shape[1])
            
            # Criar modelo LSTM
            model = Sequential([
                LSTM(64, input_shape=(1, X_train.shape[2])),
                Dropout(0.2),
                Dense(32, activation='relu'),
                Dense(1)
            ])
            
        else:  # gru
            # Reshape para GRU
            X_train = X_train.reshape(X_train.shape[0], 1, X_train.shape[1])
            X_test = X_test.reshape(X_test.shape[0], 1, X_test.shape[1])
            
            # Criar modelo GRU
            model = Sequential([
                GRU(64, input_shape=(1, X_train.shape[2])),
                Dropout(0.2),
                Dense(32, activation='relu'),
                Dense(1)
            ])
            
        # Compilar e treinar
        model.compile(optimizer='adam', loss='mse')
        model.fit(
            X_train, y_train,
            epochs=100,
            batch_size=32,
            validation_data=(X_test, y_test)
        )
        
        # Avaliar modelo
        score = model.evaluate(X_test, y_test)
        print(f"MSE: {score:.3f}")
        
        self.models['reservoir_predictor'] = {
            'model': model,
            'scaler': scaler,
            'input_features': input_features,
            'target_feature': target_feature
        }
        
    def create_dashboard(self):
        """Cria dashboard interativo."""
        app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        
        # Layout
        app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("Monitoramento de Reservatório"),
                    html.Hr()
                ])
            ]),
            
            dbc.Row([
                dbc.Col([
                    html.H3("Produção"),
                    dcc.Graph(id='production-plot')
                ], width=6),
                
                dbc.Col([
                    html.H3("Pressão"),
                    dcc.Graph(id='pressure-plot')
                ], width=6)
            ]),
            
            dbc.Row([
                dbc.Col([
                    html.H3("Padrões de Produção"),
                    dcc.Graph(id='pattern-plot')
                ], width=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    html.H3("Controles"),
                    dbc.Select(
                        id='well-selector',
                        options=[
                            {'label': well, 'value': well}
                            for well in self.production_data['well_name'].unique()
                        ],
                        value=self.production_data['well_name'].unique()[0]
                    ),
                    dbc.Select(
                        id='time-range',
                        options=[
                            {'label': '1 mês', 'value': 30},
                            {'label': '3 meses', 'value': 90},
                            {'label': '6 meses', 'value': 180},
                            {'label': '1 ano', 'value': 365}
                        ],
                        value=90
                    )
                ], width=3)
            ])
        ])
        
        # Callbacks
        @app.callback(
            [Output('production-plot', 'figure'),
             Output('pressure-plot', 'figure'),
             Output('pattern-plot', 'figure')],
            [Input('well-selector', 'value'),
             Input('time-range', 'value')]
        )
        def update_plots(well_name, time_range):
            # Filtrar dados
            well_data = self.production_data[
                (self.production_data['well_name'] == well_name) &
                (self.production_data['time'] <= time_range)
            ]
            
            # Plotar produção
            production_fig = px.line(
                well_data,
                x='time',
                y='rate',
                title=f'Produção - {well_name}'
            )
            
            # Plotar pressão
            pressure_fig = px.line(
                well_data,
                x='time',
                y='pressure',
                title=f'Pressão - {well_name}'
            )
            
            # Plotar padrões
            pattern_fig = px.scatter(
                self.production_patterns['features_pca'],
                x=0,
                y=1,
                color=self.production_patterns['clusters'],
                title='Padrões de Produção'
            )
            
            return production_fig, pressure_fig, pattern_fig
            
        self.dashboard = app
        
    def run_dashboard(self, debug: bool = True, port: int = 8050):
        """
        Executa dashboard.
        
        Args:
            debug: Modo debug
            port: Porta do servidor
        """
        if self.dashboard is None:
            raise ValueError("Dashboard não criado")
            
        self.dashboard.run_server(debug=debug, port=port)
        
    def predict_seismic(self, data: np.ndarray) -> np.ndarray:
        """
        Faz predições em dados sísmicos.
        
        Args:
            data: Dados sísmicos
            
        Returns:
            Array com predições
        """
        if 'seismic_classifier' not in self.models:
            raise ValueError("Classificador sísmico não treinado")
            
        # Normalizar
        scaler = StandardScaler()
        data = scaler.fit_transform(data.reshape(-1, data.shape[-1])).reshape(data.shape)
        
        # Fazer predições
        predictions = self.models['seismic_classifier'].predict(data)
        
        return predictions
        
    def predict_reservoir(self, input_data: pd.DataFrame) -> np.ndarray:
        """
        Faz predições de performance de reservatório.
        
        Args:
            input_data: Dados de entrada
            
        Returns:
            Array com predições
        """
        if 'reservoir_predictor' not in self.models:
            raise ValueError("Preditor de reservatório não treinado")
            
        # Preparar dados
        X = input_data[self.models['reservoir_predictor']['input_features']].values
        
        # Normalizar
        X = self.models['reservoir_predictor']['scaler'].transform(X)
        
        # Reshape para LSTM/GRU
        X = X.reshape(X.shape[0], 1, X.shape[1])
        
        # Fazer predições
        predictions = self.models['reservoir_predictor']['model'].predict(X)
        
        return predictions
        
    def plot_production_patterns(self):
        """Plota padrões de produção."""
        if not hasattr(self, 'production_patterns'):
            raise ValueError("Padrões de produção não calculados")
            
        # Plotar clusters
        plt.figure(figsize=(10, 8))
        plt.scatter(
            self.production_patterns['features_pca'][:,0],
            self.production_patterns['features_pca'][:,1],
            c=self.production_patterns['clusters'],
            cmap='viridis'
        )
        plt.xlabel('PC1')
        plt.ylabel('PC2')
        plt.title('Padrões de Produção')
        plt.colorbar(label='Cluster')
        
        return plt.gcf()
        
    def plot_seismic_interpretation(self,
                                  data: np.ndarray,
                                  predictions: np.ndarray):
        """
        Plota interpretação sísmica.
        
        Args:
            data: Dados sísmicos
            predictions: Predições do modelo
        """
        # Plotar seção sísmica
        plt.figure(figsize=(15, 5))
        
        plt.subplot(121)
        plt.imshow(data, aspect='auto', cmap='seismic')
        plt.colorbar(label='Amplitude')
        plt.title('Seção Sísmica')
        
        plt.subplot(122)
        plt.imshow(predictions, aspect='auto', cmap='viridis')
        plt.colorbar(label='Classe')
        plt.title('Interpretação')
        
        plt.tight_layout()
        
        return plt.gcf() 