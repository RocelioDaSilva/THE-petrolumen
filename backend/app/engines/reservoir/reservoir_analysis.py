import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from typing import Dict, List, Tuple, Optional, Union
import matplotlib.pyplot as plt
import seaborn as sns

class ReservoirAnalysis:
    def __init__(self):
        """Inicializa o analisador de reservatórios."""
        self.production_model = None
        self.classification_model = None
        self.scaler = MinMaxScaler()
        self.history = None
        
    def prepare_production_data(self, df: pd.DataFrame, 
                              target_column: str,
                              sequence_length: int = 30,
                              train_split: float = 0.8) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepara dados de produção para o modelo LSTM.
        
        Args:
            df: DataFrame com dados de produção
            target_column: Coluna alvo para previsão
            sequence_length: Tamanho da sequência para LSTM
            train_split: Proporção de dados para treino
            
        Returns:
            X_train, y_train, X_test, y_test
        """
        # Normalizar dados
        scaled_data = self.scaler.fit_transform(df[[target_column]])
        
        # Criar sequências
        X, y = [], []
        for i in range(len(scaled_data) - sequence_length):
            X.append(scaled_data[i:(i + sequence_length)])
            y.append(scaled_data[i + sequence_length])
            
        X = np.array(X)
        y = np.array(y)
        
        # Dividir em treino e teste
        train_size = int(len(X) * train_split)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        return X_train, y_train, X_test, y_test
        
    def build_lstm_model(self, sequence_length: int = 30):
        """
        Constrói modelo LSTM para previsão de produção.
        
        Args:
            sequence_length: Tamanho da sequência para LSTM
        """
        model = Sequential([
            LSTM(50, activation='relu', input_shape=(sequence_length, 1), return_sequences=True),
            Dropout(0.2),
            LSTM(50, activation='relu'),
            Dropout(0.2),
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse')
        self.production_model = model
        
    def train_production_model(self, X_train: np.ndarray, y_train: np.ndarray,
                             epochs: int = 100, batch_size: int = 32,
                             validation_split: float = 0.1):
        """
        Treina modelo LSTM para previsão de produção.
        
        Args:
            X_train: Dados de treino
            y_train: Alvos de treino
            epochs: Número de épocas
            batch_size: Tamanho do batch
            validation_split: Proporção de dados para validação
        """
        self.history = self.production_model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=1
        )
        
    def predict_production(self, X: np.ndarray) -> np.ndarray:
        """
        Faz previsão de produção.
        
        Args:
            X: Dados de entrada
            
        Returns:
            Previsões normalizadas
        """
        predictions = self.production_model.predict(X)
        return predictions
        
    def inverse_transform_predictions(self, predictions: np.ndarray) -> np.ndarray:
        """
        Converte previsões normalizadas para escala original.
        
        Args:
            predictions: Previsões normalizadas
            
        Returns:
            Previsões na escala original
        """
        return self.scaler.inverse_transform(predictions)
        
    def plot_training_history(self):
        """Plota histórico de treinamento."""
        if self.history is None:
            raise ValueError("Modelo ainda não foi treinado")
            
        plt.figure(figsize=(10, 6))
        plt.plot(self.history.history['loss'], label='Treino')
        plt.plot(self.history.history['val_loss'], label='Validação')
        plt.title('Histórico de Treinamento')
        plt.xlabel('Época')
        plt.ylabel('Erro Quadrático Médio')
        plt.legend()
        plt.grid(True)
        return plt.gcf()
        
    def classify_reservoirs(self, features: pd.DataFrame, n_clusters: int = 3):
        """
        Classifica reservatórios por produtividade usando K-means.
        
        Args:
            features: DataFrame com features dos reservatórios
            n_clusters: Número de clusters
        """
        # Normalizar features
        scaled_features = self.scaler.fit_transform(features)
        
        # Aplicar K-means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(scaled_features)
        
        # Adicionar clusters ao DataFrame
        features['Cluster'] = clusters
        
        # Calcular estatísticas por cluster
        cluster_stats = features.groupby('Cluster').agg({
            'Production': ['mean', 'std', 'min', 'max'],
            'Pressure': ['mean', 'std'],
            'Temperature': ['mean', 'std']
        })
        
        return features, cluster_stats
        
    def plot_reservoir_clusters(self, features: pd.DataFrame, 
                              x_col: str, y_col: str):
        """
        Plota clusters de reservatórios.
        
        Args:
            features: DataFrame com features e clusters
            x_col: Coluna para eixo x
            y_col: Coluna para eixo y
        """
        plt.figure(figsize=(10, 8))
        sns.scatterplot(data=features, x=x_col, y=y_col, 
                       hue='Cluster', palette='deep')
        plt.title('Classificação de Reservatórios')
        plt.xlabel(x_col)
        plt.ylabel(y_col)
        plt.grid(True)
        return plt.gcf()
        
    def diagnose_underutilized_reservoirs(self, 
                                        production_data: pd.DataFrame,
                                        pressure_data: pd.DataFrame,
                                        threshold_pressure: float = 0.7,
                                        threshold_production: float = 0.3):
        """
        Diagnostica reservatórios subutilizados.
        
        Args:
            production_data: DataFrame com dados de produção
            pressure_data: DataFrame com dados de pressão
            threshold_pressure: Limiar de pressão (proporção da pressão inicial)
            threshold_production: Limiar de produção (proporção da produção máxima)
            
        Returns:
            DataFrame com diagnóstico
        """
        # Calcular métricas
        initial_pressure = pressure_data['Pressure'].iloc[0]
        max_production = production_data['Production'].max()
        
        # Identificar reservatórios subutilizados
        underutilized = pd.DataFrame()
        underutilized['Current_Pressure'] = pressure_data['Pressure'].iloc[-1]
        underutilized['Pressure_Ratio'] = underutilized['Current_Pressure'] / initial_pressure
        underutilized['Current_Production'] = production_data['Production'].iloc[-1]
        underutilized['Production_Ratio'] = underutilized['Current_Production'] / max_production
        
        # Classificar reservatórios
        underutilized['Status'] = 'Normal'
        underutilized.loc[underutilized['Pressure_Ratio'] < threshold_pressure, 'Status'] = 'Pressão Baixa'
        underutilized.loc[underutilized['Production_Ratio'] < threshold_production, 'Status'] = 'Produção Baixa'
        underutilized.loc[(underutilized['Pressure_Ratio'] < threshold_pressure) & 
                         (underutilized['Production_Ratio'] < threshold_production), 
                         'Status'] = 'Subutilizado'
        
        # Adicionar recomendações
        underutilized['Recommendation'] = 'Manter operação'
        underutilized.loc[underutilized['Status'] == 'Pressão Baixa', 
                         'Recommendation'] = 'Considerar injeção de água/gás'
        underutilized.loc[underutilized['Status'] == 'Produção Baixa', 
                         'Recommendation'] = 'Otimizar operação de poços'
        underutilized.loc[underutilized['Status'] == 'Subutilizado', 
                         'Recommendation'] = 'Revisar estratégia de desenvolvimento'
        
        return underutilized
        
    def plot_underutilized_diagnosis(self, diagnosis: pd.DataFrame):
        """
        Plota diagnóstico de reservatórios subutilizados.
        
        Args:
            diagnosis: DataFrame com diagnóstico
        """
        plt.figure(figsize=(12, 8))
        
        # Plotar pressão vs produção
        plt.scatter(diagnosis['Pressure_Ratio'], 
                   diagnosis['Production_Ratio'],
                   c=diagnosis['Status'].map({
                       'Normal': 'green',
                       'Pressão Baixa': 'yellow',
                       'Produção Baixa': 'orange',
                       'Subutilizado': 'red'
                   }))
        
        # Adicionar linhas de limiar
        plt.axvline(x=0.7, color='gray', linestyle='--', alpha=0.5)
        plt.axhline(y=0.3, color='gray', linestyle='--', alpha=0.5)
        
        plt.title('Diagnóstico de Reservatórios')
        plt.xlabel('Razão de Pressão')
        plt.ylabel('Razão de Produção')
        plt.grid(True)
        
        # Adicionar legenda
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', 
                  markerfacecolor='green', label='Normal'),
            Line2D([0], [0], marker='o', color='w', 
                  markerfacecolor='yellow', label='Pressão Baixa'),
            Line2D([0], [0], marker='o', color='w', 
                  markerfacecolor='orange', label='Produção Baixa'),
            Line2D([0], [0], marker='o', color='w', 
                  markerfacecolor='red', label='Subutilizado')
        ]
        plt.legend(handles=legend_elements)
        
        return plt.gcf() 