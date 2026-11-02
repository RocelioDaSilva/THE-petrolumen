import numpy as np
import tensorflow as tf
from typing import Dict, List, Tuple, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

class ReservoirProxy:
    """Modelo proxy avançado baseado em redes neurais para simulação de reservatório"""
    
    def __init__(self, input_dim: int, output_dim: int,
                 model_type: str = "dense",
                 uncertainty: bool = False):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.model = None
        self.uncertainty_model = None
        self.input_scaler = StandardScaler()
        self.output_scaler = StandardScaler()
        self.model_type = model_type
        self.use_uncertainty = uncertainty
        
        # Histórico de treinamento
        self.training_history = []
        self.validation_metrics = {}
        
    def build_model(self, layers: List[int] = [64, 32]):
        """Constrói arquitetura da rede neural"""
        model = tf.keras.Sequential()
        
        # Camada de entrada
        model.add(tf.keras.layers.Dense(
            layers[0],
            input_dim=self.input_dim,
            activation='relu'
        ))
        
        # Camadas intermediárias
        for units in layers[1:]:
            model.add(tf.keras.layers.Dense(units, activation='relu'))
            model.add(tf.keras.layers.Dropout(0.2))
            
        # Camada de saída
        model.add(tf.keras.layers.Dense(self.output_dim))
        
        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        
        self.model = model
        
    def prepare_data(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Prepara dados para treinamento"""
        # Normalização
        X_scaled = self.input_scaler.fit_transform(X)
        y_scaled = self.output_scaler.fit_transform(y)
        
        return X_scaled, y_scaled
    
    def train(self, X: np.ndarray, y: np.ndarray,
              validation_split: float = 0.2,
              epochs: int = 100,
              batch_size: int = 32):
        """Treina o modelo proxy"""
        # Preparar dados
        X_scaled, y_scaled = self.prepare_data(X, y)
        
        # Dividir em treino e validação
        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, y_scaled,
            test_size=validation_split,
            random_state=42
        )
        
        # Early stopping
        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        
        # Treinar modelo
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stopping],
            verbose=1
        )
        
        return history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Realiza predições usando o modelo proxy"""
        # Normalizar entrada
        X_scaled = self.input_scaler.transform(X)
        
        # Fazer predição
        y_pred_scaled = self.model.predict(X_scaled)
        
        # Desnormalizar saída
        return self.output_scaler.inverse_transform(y_pred_scaled)
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Avalia performance do modelo"""
        # Preparar dados
        X_scaled = self.input_scaler.transform(X)
        y_scaled = self.output_scaler.transform(y)
        
        # Avaliar modelo
        metrics = self.model.evaluate(X_scaled, y_scaled)
        
        return {
            "mse": metrics[0],
            "mae": metrics[1]
        }
    
class WellProductionProxy(ReservoirProxy):
    """Modelo proxy específico para previsão de produção de poços"""
    
    def __init__(self):
        super().__init__(input_dim=5, output_dim=3)  # [P, k, phi, Sw, t] -> [qo, qw, qg]
        
    def build_model(self):
        """Constrói arquitetura específica para produção"""
        super().build_model(layers=[128, 64, 32])
        
class PressureProxy(ReservoirProxy):
    """Modelo proxy específico para distribuição de pressão"""
    
    def __init__(self, nx: int, ny: int, nz: int):
        self.grid_dims = (nx, ny, nz)
        super().__init__(
            input_dim=4,  # [t, qo, qw, qg]
            output_dim=nx * ny * nz  # Pressão em cada célula
        )
        
    def build_model(self):
        """Constrói arquitetura específica para pressão"""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(256, input_dim=self.input_dim, activation='relu'),
            tf.keras.layers.Dense(512, activation='relu'),
            tf.keras.layers.Dense(1024, activation='relu'),
            tf.keras.layers.Dense(self.output_dim),
            tf.keras.layers.Reshape(self.grid_dims)
        ])
        
        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        
        self.model = model
        
class SaturationProxy(ReservoirProxy):
    """Modelo proxy específico para distribuição de saturação"""
    
    def __init__(self, nx: int, ny: int, nz: int):
        self.grid_dims = (nx, ny, nz)
        super().__init__(
            input_dim=4,  # [t, qo, qw, qg]
            output_dim=nx * ny * nz * 3  # Sw, So, Sg em cada célula
        )
        
    def build_model(self):
        """Constrói arquitetura específica para saturação"""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(256, input_dim=self.input_dim, activation='relu'),
            tf.keras.layers.Dense(512, activation='relu'),
            tf.keras.layers.Dense(1024, activation='relu'),
            tf.keras.layers.Dense(self.output_dim),
            tf.keras.layers.Reshape((*self.grid_dims, 3))
        ])
        
        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        
        self.model = model
