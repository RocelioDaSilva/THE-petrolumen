import numpy as np
import pandas as pd
import tensorflow as tf
from typing import Dict, List, Optional, Tuple, Union
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
        try:
            import segyio
        except ImportError as error:
            raise ImportError(
                "Loading SEG-Y data requires the optional 'segyio' dependency."
            ) from error

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
            
        if self.seismic_data.ndim not in (2, 3) or self.seismic_data.shape[-1] < 2:
            raise ValueError("Seismic data must be 2D or 3D with at least two samples.")

        data = self.seismic_data.astype(np.float32, copy=False)
        analytic = hilbert(data, axis=-1)
        self.attributes["envelope"] = np.abs(analytic)
        
        # Fase instantânea
        self.attributes["instant_phase"] = np.angle(analytic)
        
        # Frequência instantânea
        self.attributes["instant_freq"] = np.gradient(
            np.unwrap(self.attributes["instant_phase"], axis=-1), axis=-1
        )
        
        # Impedância relativa
        self.attributes["rel_impedance"] = np.cumsum(
            data, axis=-1
        )
        
        # Sweetness
        denominator = np.sqrt(np.abs(self.attributes["instant_freq"]))
        self.attributes["sweetness"] = np.divide(
            self.attributes["envelope"],
            denominator,
            out=np.zeros_like(self.attributes["envelope"]),
            where=denominator != 0,
        )
        
        # Coerência
        self.attributes["coherency"] = self._compute_coherency()
        
    def _compute_coherency(self, window_size: int = 3):
        """Calcula atributo de coerência"""
        if self.seismic_data is None:
            raise ValueError("Dados sísmicos não carregados")
        if window_size < 1:
            raise ValueError("window_size must be positive.")
        if self.seismic_data.ndim not in (2, 3):
            raise ValueError("Seismic data must be 2D or 3D.")

        coherency = np.zeros_like(self.seismic_data)

        for i in range(window_size, self.seismic_data.shape[0] - window_size):
            for j in range(window_size, self.seismic_data.shape[1] - window_size):
                if self.seismic_data.ndim == 2:
                    window = self.seismic_data[
                        i - window_size:i + window_size + 1,
                        j - window_size:j + window_size + 1,
                    ]
                    traces = window
                else:
                    window = self.seismic_data[
                        i - window_size:i + window_size + 1,
                        j - window_size:j + window_size + 1,
                        :,
                    ]
                    traces = window.reshape(-1, window.shape[-1])

                if traces.shape[0] < 2 or traces.shape[1] < 2:
                    continue
                covariance = np.atleast_2d(np.cov(traces, rowvar=True))
                eigenvalues = np.maximum(np.linalg.eigvalsh(covariance), 0.0)
                total_variance = eigenvalues.sum()
                value = (
                    eigenvalues[-1] / total_variance
                    if total_variance > 0
                    else 1.0
                )
                coherency[i, j] = value
                
        return coherency
    
    def train_facies_classifier(
        self,
        training_patches: Union[np.ndarray, Dict[str, np.ndarray]],
        training_labels: Optional[np.ndarray] = None,
    ):
        """Train a facies CNN from labeled seismic patches."""
        if isinstance(training_patches, dict):
            if training_labels is not None:
                raise ValueError("Pass labels separately only when using patch arrays.")
            if "facies" not in training_patches:
                raise ValueError("Legacy training data must include 'facies'.")
            training_labels = np.asarray(training_patches["facies"])
            training_patches = np.stack(
                [self.attributes[attr] for attr in self.attributes]
            )

        training_patches = np.asarray(training_patches)
        if training_labels is None:
            raise ValueError("Training labels are required.")
        training_labels = np.asarray(training_labels)
        if training_patches.ndim != 4:
            raise ValueError(
                "Training patches must be 4D: "
                "(n_patches, height, width, n_attributes)."
            )
        if training_labels.ndim != 1:
            raise ValueError("Training labels must be 1D.")
        if training_patches.shape[0] != training_labels.shape[0]:
            raise ValueError("Number of patches and labels must match.")
        if min(training_patches.shape[1:3]) < 4:
            raise ValueError("Training patches must be at least 4x4 pixels.")
        if not np.all(np.isfinite(training_patches)):
            raise ValueError("Training patches must contain only finite values.")
        classes, encoded_labels = np.unique(training_labels, return_inverse=True)
        if len(classes) < 2:
            raise ValueError("At least two facies classes are required.")

        input_shape = training_patches.shape[1:]
        model = tf.keras.Sequential([
            tf.keras.layers.Conv2D(32, 3, activation='relu',
                                 input_shape=input_shape, padding="same"),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(64, 3, activation='relu', padding="same"),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(64, 3, activation='relu', padding="same"),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dropout(0.5),
            tf.keras.layers.Dense(len(classes), activation='softmax')
        ])
        
        model.compile(optimizer='adam',
                     loss='sparse_categorical_crossentropy',
                     metrics=['accuracy'])
        
        # Treinar modelo
        history = model.fit(
            training_patches,
            encoded_labels,
            epochs=50,
            validation_split=0.2 if len(encoded_labels) >= 5 else 0,
            batch_size=32,
        )
        
        self.facies_model = {
            "model": model,
            "history": history.history,
            "input_shape": input_shape,
            "classes": classes,
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
        """Extract trace-level latent attributes with an autoencoder."""
        if self.seismic_data is None:
            raise ValueError("Dados sísmicos não carregados")
        if self.seismic_data.ndim not in (2, 3):
            raise ValueError("Seismic data must be 2D or 3D.")

        original_shape = self.seismic_data.shape
        traces = self.seismic_data.reshape(-1, original_shape[-1])
        if traces.shape[0] < 2 or traces.shape[1] < 1:
            raise ValueError("At least two seismic traces are required.")

        scaler = StandardScaler()
        scaled_traces = scaler.fit_transform(traces.T).T
        input_dim = scaled_traces.shape[1]
        encoding_dim = min(32, input_dim)
        encoder = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(input_dim,)),
            tf.keras.layers.Dense(128, activation="relu"),
            tf.keras.layers.Dense(64, activation="relu"),
            tf.keras.layers.Dense(encoding_dim, activation="relu"),
        ])
        decoder = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(encoding_dim,)),
            tf.keras.layers.Dense(64, activation="relu"),
            tf.keras.layers.Dense(128, activation="relu"),
            tf.keras.layers.Dense(input_dim),
        ])
        autoencoder = tf.keras.Model(encoder.input, decoder(encoder.output))
        autoencoder.compile(optimizer='adam', loss='mse')
        autoencoder.fit(
            scaled_traces,
            scaled_traces,
            epochs=50,
            batch_size=256,
            verbose=0,
            shuffle=True,
        )

        latent = encoder.predict(scaled_traces, verbose=0)
        trace_shape = original_shape[:-1]
        for index in range(latent.shape[1]):
            values = latent[:, index]
            self.neural_attributes[f"neural_attr_{index}"] = (
                values.reshape(trace_shape) if self.seismic_data.ndim == 3 else values
            )
            
    def detect_geobodies(self, attribute: str, threshold: float):
        """Detecta geobodies usando atributos"""
        if attribute in self.attributes:
            data = self.attributes[attribute]
        elif attribute in self.neural_attributes:
            data = self.neural_attributes[attribute]
        else:
            raise ValueError(f"Atributo {attribute} não encontrado")
            
        smooth_data = gaussian_filter(data, sigma=1)
        
        # Threshold
        binary = smooth_data > threshold
        
        # Conectar componentes
        labeled, num_features = label(binary)
        
        return {
            "labels": labeled,
            "num_bodies": num_features,
            "volumes": [np.sum(labeled == i) for i in range(1, num_features + 1)]
        }
        
    def predict_properties_from_attributes(
        self,
        attribute_names: List[str],
        well_log_properties: pd.DataFrame,
        target_property: str,
    ):
        """Train a well-log property model from sampled seismic attributes."""
        if not attribute_names or len(set(attribute_names)) != len(attribute_names):
            raise ValueError("Provide at least one unique seismic attribute.")
        missing_attributes = [
            name for name in attribute_names if name not in self.attributes
        ]
        if missing_attributes:
            raise ValueError(f"Missing seismic attributes: {missing_attributes}.")
        required_columns = attribute_names + [target_property]
        if target_property in attribute_names or not all(
            column in well_log_properties.columns for column in required_columns
        ):
            raise ValueError("Well-log data is missing required, distinct columns.")

        samples = well_log_properties.loc[:, required_columns].dropna()
        if samples.empty:
            raise ValueError("No complete well-log samples are available.")
        features = samples[attribute_names].to_numpy(dtype=float)
        targets = samples[target_property].to_numpy(dtype=float)
        if not np.all(np.isfinite(features)) or not np.all(np.isfinite(targets)):
            raise ValueError("Well-log attributes and target must be finite.")
        if len(targets) < 2:
            raise ValueError("At least two valid well-log samples are required.")

        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(features_scaled.shape[1],)),
            tf.keras.layers.Dense(128, activation="relu"),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(64, activation="relu"),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(32, activation="relu"),
            tf.keras.layers.Dense(1),
        ])
        model.compile(optimizer="adam", loss="mse")
        model.fit(
            features_scaled,
            targets,
            epochs=100,
            validation_split=0.2 if len(targets) >= 5 else 0,
            verbose=0,
            batch_size=32,
        )
        self.property_model = {
            "model": model,
            "scaler": scaler,
            "attribute_names": attribute_names,
            "target_property": target_property,
        }

    def export_results(self, filename: str):
        """Exporta resultados da análise"""
        np.savez(filename,
                 seismic=self.seismic_data,
                 attributes=self.attributes,
                 neural_attributes=self.neural_attributes,
                 predictions=self.property_model.get("predictions")
                 if self.property_model else None)
