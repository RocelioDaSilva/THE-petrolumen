import numpy as np
import tensorflow as tf
from typing import Dict, List, Optional, Tuple
import segyio
from sklearn.preprocessing import StandardScaler
from scipy.signal import hilbert
from scipy.ndimage import gaussian_filter

class AISeismicAnalysis:
    """Análise sísmica avançada com IA (estilo Geoteric)"""
    
    def __init__(self):
        self.seismic_data = None
        self.attributes = {}
        self.neural_attributes = {}
        self.facies_model = None
        self.property_model = None
        
    def load_seismic(self, filename: str):
        """Carrega dados sísmicos"""
        with segyio.open(filename, "r", ignore_geometry=True) as f:
            # Carregar dados
            self.seismic_data = np.array([trace for trace in f.trace])
            
            # Informações do cabeçalho
            self.metadata = {
                "sample_rate": f.header[0][117],
                "num_samples": f.samples.size,
                "num_traces": len(f.trace)
            }
    
    def compute_attributes(self):
        """Calcula atributos sísmicos convencionais"""
        if self.seismic_data is None:
            raise ValueError("Dados sísmicos não carregados")
            
        # Envelope (força de reflexão)
        analytic = hilbert(self.seismic_data)
        self.attributes["envelope"] = np.abs(analytic)
        
        # Fase instantânea
        self.attributes["instant_phase"] = np.angle(analytic)
        
        # Frequência instantânea
        self.attributes["instant_freq"] = np.gradient(
            np.unwrap(self.attributes["instant_phase"]), axis=1
        )
        
        # Impedância relativa
        self.attributes["rel_impedance"] = np.cumsum(
            self.seismic_data, axis=1
        )
        
        # Sweetness
        self.attributes["sweetness"] = (
            self.attributes["envelope"] /
            np.sqrt(np.abs(self.attributes["instant_freq"]))
        )
        
        # Coerência
        self.attributes["coherency"] = self._compute_coherency()
        
    def _compute_coherency(self, window_size: int = 3):
        """Calcula atributo de coerência"""
        coherency = np.zeros_like(self.seismic_data)
        
        for i in range(window_size, self.seismic_data.shape[0] - window_size):
            for j in range(window_size, self.seismic_data.shape[1] - window_size):
                # Extrair janela
                window = self.seismic_data[
                    i-window_size:i+window_size+1,
                    j-window_size:j+window_size+1
                ]
                
                # Calcular matriz de covariância
                cov = np.cov(window.reshape(-1, 1))
                
                # Eigenvalues
                eigenvals = np.linalg.eigvals(cov)
                
                # Coerência como razão dos eigenvalues
                coherency[i,j] = eigenvals.min() / eigenvals.max()
                
        return coherency
    
    def train_facies_classifier(self, training_data: Dict[str, np.ndarray]):
        """Treina classificador de fácies usando CNN"""
        # Preparar dados
        X = np.stack([self.attributes[attr] for attr in self.attributes])
        y = training_data["facies"]
        
        # Criar modelo CNN
        model = tf.keras.Sequential([
            tf.keras.layers.Conv2D(32, 3, activation='relu',
                                 input_shape=X.shape[1:]),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(64, 3, activation='relu'),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(64, 3, activation='relu'),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(len(np.unique(y)), activation='softmax')
        ])
        
        model.compile(optimizer='adam',
                     loss='sparse_categorical_crossentropy',
                     metrics=['accuracy'])
        
        # Treinar modelo
        history = model.fit(X, y, epochs=50, validation_split=0.2)
        
        self.facies_model = {
            "model": model,
            "history": history.history
        }
        
    def predict_properties(self, well_data: Dict[str, np.ndarray]):
        """Previsão de propriedades usando IA"""
        # Criar features combinando atributos sísmicos
        features = np.concatenate([
            self.attributes[attr].reshape(-1, 1)
            for attr in self.attributes
        ], axis=1)
        
        # Normalizar
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Criar modelo para cada propriedade
        for prop_name, prop_data in well_data.items():
            # Criar modelo neural
            model = tf.keras.Sequential([
                tf.keras.layers.Dense(128, activation='relu',
                                   input_shape=(features.shape[1],)),
                tf.keras.layers.Dropout(0.3),
                tf.keras.layers.Dense(64, activation='relu'),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(32, activation='relu'),
                tf.keras.layers.Dense(1)
            ])
            
            model.compile(optimizer='adam', loss='mse')
            
            # Treinar
            model.fit(features_scaled, prop_data, epochs=100,
                     validation_split=0.2, verbose=0)
            
            # Fazer previsões
            predictions = model.predict(features_scaled)
            
            # Armazenar resultados
            self.property_model = {
                "model": model,
                "scaler": scaler,
                "predictions": predictions.reshape(self.seismic_data.shape)
            }
            
    def compute_neural_attributes(self):
        """Calcula atributos usando redes neurais"""
        # Preparar dados
        data = self.seismic_data.reshape(-1, 1)
        
        # Criar autoencoder para atributos
        encoder = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(1,)),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(16, activation='relu')
        ])
        
        decoder = tf.keras.Sequential([
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(1, activation='linear')
        ])
        
        autoencoder = tf.keras.Sequential([encoder, decoder])
        autoencoder.compile(optimizer='adam', loss='mse')
        
        # Treinar
        autoencoder.fit(data, data, epochs=50, batch_size=256, verbose=0)
        
        # Extrair atributos latentes
        latent = encoder.predict(data)
        
        # Reorganizar atributos
        for i in range(latent.shape[1]):
            self.neural_attributes[f"neural_attr_{i}"] = latent[:,i].reshape(
                self.seismic_data.shape
            )
            
    def detect_geobodies(self, attribute: str, threshold: float):
        """Detecta geobodies usando atributos"""
        if attribute not in self.attributes:
            raise ValueError(f"Atributo {attribute} não encontrado")
            
        # Suavizar dados
        smooth_data = gaussian_filter(self.attributes[attribute], sigma=1)
        
        # Threshold
        binary = smooth_data > threshold
        
        # Conectar componentes
        from scipy.ndimage import label
        labeled, num_features = label(binary)
        
        return {
            "labels": labeled,
            "num_bodies": num_features,
            "volumes": [np.sum(labeled == i) for i in range(1, num_features + 1)]
        }
        
    def export_results(self, filename: str):
        """Exporta resultados da análise"""
        np.savez(filename,
                 seismic=self.seismic_data,
                 attributes=self.attributes,
                 neural_attributes=self.neural_attributes,
                 predictions=self.property_model["predictions"]
                 if self.property_model else None)
