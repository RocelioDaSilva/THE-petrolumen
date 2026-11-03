import numpy as np
import pandas as pd  # Added import for pandas
import tensorflow as tf
from typing import Dict, List, Optional  # Removed Tuple
import segyio
from sklearn.preprocessing import StandardScaler
from scipy.signal import hilbert
from scipy.ndimage import gaussian_filter, label  # Added label import


class AISeismicAnalysis:
    """Análise sísmica avançada com IA (estilo Geoteric)"""

    def __init__(self):
        self.seismic_data: Optional[np.ndarray] = None
        self.attributes: Dict[str, np.ndarray] = {}
        self.neural_attributes: Dict[str, np.ndarray] = {}
        self.facies_model: Optional[Dict] = None  # To store model and history
        self.property_model: Optional[Dict] = (
            None  # To store model, scaler, predictions
        )
        self.metadata: Optional[Dict] = None

    def load_seismic(self, filename: str):
        """Carrega dados sísmicos de um arquivo SEGY"""
        try:
            with segyio.open(filename, "r", ignore_geometry=True) as f:
                self.seismic_data = segyio.tools.cube(f)  # More robust way to load cube
                # Attempt to get sample rate, handle potential errors if header is unusual
                try:
                    sample_rate_us = f.header[0][
                        segyio.TraceField.TRACE_HEADER_SIZE
                        + segyio.TraceField.SampleInterval
                    ]
                    sample_rate_s = (
                        sample_rate_us / 1_000_000.0
                    )  # Convert microseconds to seconds
                except (IndexError, KeyError, AttributeError):
                    print(
                        "Warning: Could not read sample interval from SEGY header. "
                        "Using default or NaN."
                    )
                    sample_rate_s = np.nan  # Or a sensible default

                self.metadata = {
                    "sample_rate_s": sample_rate_s,
                    "num_samples_per_trace": f.samples.size,  # Samples per trace
                    "num_traces": len(f.trace),  # Number of traces
                    "num_inlines": f.ilines.size if hasattr(f, "ilines") else None,
                    "num_crosslines": f.xlines.size if hasattr(f, "xlines") else None,
                }
                # Assuming seismic_data is (n_traces, n_samples) or
                # (n_ilines, n_xlines, n_samples)
                # For simplicity, let's assume it's reshaped to (n_traces, n_samples) if 3D
                if self.seismic_data.ndim == 3:  # (inlines, crosslines, samples)
                    # Reshape to (traces, samples) for attribute calculations if they
                    # expect 2D. This might need adjustment based on how attributes are
                    # computed (trace-wise or slice-wise). For now, let's keep its
                    # original shape if 3D, and attributes should handle 3D.
                    pass  # Keep as 3D, attribute functions must handle this.
                elif self.seismic_data.ndim == 2:  # (traces, samples)
                    pass
                else:
                    raise ValueError(
                        "Loaded seismic data has unexpected dimension: "
                        f"{self.seismic_data.ndim}"
                    )

        except Exception as e:
            print(f"Error loading SEGY file {filename}: {e}")
            self.seismic_data = None
            self.metadata = None
            raise

    def compute_attributes(self):
        """Calcula atributos sísmicos convencionais"""
        if self.seismic_data is None:
            raise ValueError("Dados sísmicos não carregados")

        # Ensure data is float for hilbert transform
        data_float = self.seismic_data.astype(np.float32)

        # Envelope (força de reflexão) - apply along sample axis (last axis)
        analytic = hilbert(data_float, axis=-1)
        self.attributes["envelope"] = np.abs(analytic)

        # Fase instantânea
        self.attributes["instant_phase"] = np.angle(analytic)

        # Frequência instantânea
        unwrapped_phase = np.unwrap(self.attributes["instant_phase"], axis=-1)
        # Gradient along the sample axis (last axis)
        self.attributes["instant_freq"] = np.gradient(unwrapped_phase, axis=-1)

        # Impedância relativa (integral of trace)
        self.attributes["rel_impedance"] = np.cumsum(data_float, axis=-1)

        # Sweetness - ensure instant_freq is not zero
        denom_sweetness = np.sqrt(np.abs(self.attributes["instant_freq"]))
        self.attributes["sweetness"] = np.divide(
            self.attributes["envelope"],
            denom_sweetness,
            out=np.zeros_like(self.attributes["envelope"]),
            where=denom_sweetness != 0,
        )

        # Coerência
        self.attributes["coherency"] = self._compute_coherency()

    def _compute_coherency(self, window_size: int = 3) -> np.ndarray:
        """Calcula atributo de coerência (simplified for 2D slice or 3D windowing)"""
        if self.seismic_data is None:
            raise ValueError("Seismic data not loaded for coherency calculation.")

        data_to_process = self.seismic_data
        # If 3D, this coherency would typically be computed slice by slice or with a 3D
        # window. For simplicity, if 3D (e.g. iline, xline, time), let's process
        # the first inline slice
        if data_to_process.ndim == 3:
            print(
                "Warning: Coherency calculation is simplified for 3D data, "
                "processing first inline slice."
            )
            data_to_process = self.seismic_data[0, :, :]  # Process first inline

        if data_to_process.ndim != 2:
            raise ValueError(
                "Coherency calculation expects 2D data (trace, sample) or will use "
                "first slice of 3D."
            )

        coherency = np.zeros_like(data_to_process)

        # Pad array to handle edges
        padded_data = np.pad(data_to_process, window_size, mode="edge")

        for i in range(data_to_process.shape[0]):  # Traces
            for j in range(data_to_process.shape[1]):  # Samples
                # Extract window from padded_data
                # Window indices are relative to original data, adjust for padding
                window = padded_data[
                    i : i + 2 * window_size + 1, j : j + 2 * window_size + 1
                ]

                if window.size == 0:
                    continue

                # Calculate covariance matrix of the window
                # Reshape window to (n_pixels, 1) if it's not already suitable for cov
                # For a 2D window, cov expects features as rows, observations as
                # columns, or vice-versa. A common way for semblance coherency is
                # trace-segment based. This implementation is a placeholder for a
                # more robust coherency algorithm.
                # Simplified: calculate variance within the window as a proxy
                if window.size > 1:
                    # Normalize window before covariance for better stability
                    window_flat = window.flatten()
                    if np.std(window_flat) > 1e-6:  # Avoid issues with flat windows
                        # This is a very basic coherency proxy, not a standard algorithm
                        # like semblance or eigenstructure. A proper coherency would
                        # involve comparing adjacent trace segments.
                        # For a quick placeholder: variance of the window, normalized.
                        # High variance -> low coherency. Low variance -> high coherency.
                        # So, coherency ~ 1 / (1 + variance)
                        coherency_val = 1.0 / (1.0 + np.var(window_flat))
                        coherency[i, j] = coherency_val
                    else:  # Flat window, high coherency
                        coherency[i, j] = 1.0
                else:  # Single point window
                    coherency[i, j] = (
                        1.0  # Or 0, depending on definition for single point
                    )

        if (
            self.seismic_data.ndim == 3
        ):  # If original was 3D, return a 3D coherency map (e.g., by repeating or
            # processing all slices)
            # For now, expand this 2D coherency back to the shape of the first slice
            # of 3D data
            full_coherency = np.zeros_like(self.seismic_data)
            full_coherency[0, :, :] = coherency
            return full_coherency
        return coherency

    def train_facies_classifier(
        self, training_patches: np.ndarray, training_labels: np.ndarray
    ):
        """
        Treina classificador de fácies usando CNN.
        Args:
            training_patches: Array de patches sísmicos (n_patches, height, width, n_attributes)
            training_labels: Array de labels para os patches (n_patches,)
        """
        if (
            training_patches.ndim != 4
        ):  # (num_patches, height, width, channels/attributes)
            raise ValueError(
                "Training patches must be 4D: (num_patches, height, width, channels)"
            )
        if training_labels.ndim != 1:
            raise ValueError("Training labels must be 1D")
        if training_patches.shape[0] != training_labels.shape[0]:
            raise ValueError("Number of patches and labels must match.")

        input_shape = training_patches.shape[1:]  # (height, width, channels)
        num_classes = len(np.unique(training_labels))

        model = tf.keras.Sequential(
            [
                tf.keras.layers.Conv2D(
                    32,
                    (3, 3),
                    activation="relu",
                    input_shape=input_shape,
                    padding="same",
                ),
                tf.keras.layers.MaxPooling2D((2, 2)),
                tf.keras.layers.Conv2D(64, (3, 3), activation="relu", padding="same"),
                tf.keras.layers.MaxPooling2D((2, 2)),
                tf.keras.layers.Conv2D(64, (3, 3), activation="relu", padding="same"),
                tf.keras.layers.Flatten(),
                tf.keras.layers.Dense(64, activation="relu"),
                tf.keras.layers.Dropout(0.5),  # Added dropout
                tf.keras.layers.Dense(num_classes, activation="softmax"),
            ]
        )

        model.compile(
            optimizer="adam",
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )

        history = model.fit(
            training_patches,
            training_labels,
            epochs=50,
            validation_split=0.2,
            batch_size=32,
        )  # Added batch_size

        self.facies_model = {
            "model": model,
            "history": history.history,
            "input_shape": input_shape,  # Store for later prediction
        }

    def predict_properties_from_attributes(
        self,
        attribute_names: List[str],
        well_log_properties: pd.DataFrame,
        target_property: str,
    ):
        """
        Previsão de propriedades (e.g., Porosidade) a partir de atributos sísmicos em
        localizações de poços.
        Args:
            attribute_names: Lista de nomes de atributos sísmicos a usar como features.
            well_log_properties: DataFrame com dados de poço, incluindo colunas para
                                 atributos sísmicos (interpolados para as profundidades
                                 do poço) e a propriedade alvo (e.g., 'Porosity').
            target_property: Nome da coluna da propriedade alvo no DataFrame
                             well_log_properties.
        """
        if not all(attr in self.attributes for attr in attribute_names):
            missing = [attr for attr in attribute_names if attr not in self.attributes]
            raise ValueError(f"Missing attributes: {missing}. Compute them first.")
        if not all(
            col in well_log_properties.columns
            for col in attribute_names + [target_property]
        ):
            raise ValueError(
                "well_log_properties DataFrame missing required attribute or target "
                "columns."
            )

        # Assume well_log_properties has attribute values sampled at log depths
        features_df = well_log_properties[attribute_names]
        target_df = well_log_properties[target_property]

        # Drop NaNs from features and target
        combined_df = pd.concat([features_df, target_df], axis=1).dropna()
        if combined_df.empty:
            raise ValueError(
                "No valid data after dropping NaNs for property prediction training."
            )

        features_clean = combined_df[attribute_names].values
        target_clean = combined_df[target_property].values

        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features_clean)

        model = tf.keras.Sequential(
            [
                tf.keras.layers.Dense(
                    128, activation="relu", input_shape=(features_scaled.shape[1],)
                ),
                tf.keras.layers.Dropout(0.3),
                tf.keras.layers.Dense(64, activation="relu"),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(32, activation="relu"),
                tf.keras.layers.Dense(1),  # Output layer for regression
            ]
        )

        model.compile(optimizer="adam", loss="mse")

        model.fit(
            features_scaled,
            target_clean,
            epochs=100,
            validation_split=0.2,
            verbose=0,
            batch_size=32,
        )

        # To predict on the full seismic volume, attributes need to be reshaped
        # correctly. This part is complex as it requires aligning seismic volume
        # attributes for prediction. For now, this model is trained on well data.
        # Predicting a volume would need a separate method.
        self.property_model = {  # Storing model trained at well locations
            "model": model,
            "scaler": scaler,
            "attribute_names": attribute_names,
            "target_property": target_property,
        }

    def compute_neural_attributes(self):
        """Calcula atributos usando redes neurais (Autoencoder)"""
        if self.seismic_data is None:
            raise ValueError("Dados sísmicos não carregados")

        # Reshape data for autoencoder: (n_samples, n_features_per_sample)
        # Here, each sample is a seismic trace.
        original_shape = self.seismic_data.shape
        if self.seismic_data.ndim == 3:  # (ilines, xlines, time_samples)
            data_reshaped = self.seismic_data.reshape(
                -1, original_shape[-1]
            )  # (traces, time_samples)
        elif self.seismic_data.ndim == 2:  # (traces, time_samples)
            data_reshaped = self.seismic_data
        else:
            raise ValueError(
                "Seismic data must be 2D or 3D for neural attribute computation."
            )

        # Normalize trace by trace (or globally, depending on desired outcome)
        scaler = StandardScaler()
        data_scaled = scaler.fit_transform(
            data_reshaped.T
        ).T  # Scale each trace's features

        # Autoencoder architecture
        input_dim = data_scaled.shape[1]  # Number of time samples per trace
        encoding_dim = 32  # Example latent dimension size

        encoder = tf.keras.Sequential(
            [
                tf.keras.layers.Dense(128, activation="relu", input_shape=(input_dim,)),
                tf.keras.layers.Dense(64, activation="relu"),
                tf.keras.layers.Dense(
                    encoding_dim, activation="relu", name="encoder_output"
                ),  # Latent representation
            ]
        )

        decoder = tf.keras.Sequential(
            [
                tf.keras.layers.Dense(
                    64, activation="relu", input_shape=(encoding_dim,)
                ),
                tf.keras.layers.Dense(128, activation="relu"),
                tf.keras.layers.Dense(
                    input_dim, activation="sigmoid"
                ),  # Sigmoid if data normalized to 0-1, or linear
            ]
        )

        autoencoder = tf.keras.Model(
            inputs=encoder.input, outputs=decoder(encoder.output)
        )
        autoencoder.compile(optimizer="adam", loss="mse")

        autoencoder.fit(
            data_scaled, data_scaled, epochs=50, batch_size=256, verbose=0, shuffle=True
        )

        # Extract latent attributes (neural attributes)
        latent_attributes = encoder.predict(
            data_scaled
        )  # Shape (n_traces, encoding_dim)

        # Store neural attributes, reshaping them back if original was 3D
        for i in range(encoding_dim):
            neural_attr_flat = latent_attributes[:, i]
            if self.seismic_data.ndim == 3:
                # Reshape (traces) back to (ilines, xlines)
                self.neural_attributes[f"neural_attr_{i}"] = neural_attr_flat.reshape(
                    original_shape[0], original_shape[1]
                )
            else:  # 2D
                self.neural_attributes[f"neural_attr_{i}"] = (
                    neural_attr_flat  # This would be a 1D array of (n_traces)
                )

    def detect_geobodies(self, attribute_name: str, threshold: float) -> Dict:
        """Detecta geobodies usando um atributo e um threshold."""
        if (
            attribute_name not in self.attributes
            and attribute_name not in self.neural_attributes
        ):
            raise ValueError(
                f"Atributo {attribute_name} não encontrado. Calcule-o primeiro."
            )

        data_to_threshold = self.attributes.get(
            attribute_name
        ) or self.neural_attributes.get(attribute_name)

        # Suavizar dados (optional, but good for noisy attributes)
        smooth_data = gaussian_filter(data_to_threshold, sigma=1)

        # Threshold
        binary_image = smooth_data > threshold

        # Conectar componentes (labeling)
        labeled_array, num_features = label(binary_image)

        volumes = []
        if num_features > 0:
            volumes = [np.sum(labeled_array == i) for i in range(1, num_features + 1)]

        return {
            "labels": labeled_array,  # The labeled image/volume
            "num_bodies": num_features,
            "volumes": volumes,  # Volume in number of cells/pixels per body
        }

    def export_results(self, filename_prefix: str):
        """Exporta atributos e resultados da análise para arquivos .npy ou .npz"""
        # Export main seismic data
        if self.seismic_data is not None:
            np.save(f"{filename_prefix}_seismic_data.npy", self.seismic_data)

        # Export conventional attributes
        if self.attributes:
            np.savez(f"{filename_prefix}_attributes.npz", **self.attributes)

        # Export neural attributes
        if self.neural_attributes:
            np.savez(
                f"{filename_prefix}_neural_attributes.npz", **self.neural_attributes
            )

        # Export facies model (if trained) - Keras model saving
        if self.facies_model and "model" in self.facies_model:
            self.facies_model["model"].save(f"{filename_prefix}_facies_model.keras")

        # Export property prediction model (if trained) - Keras model saving
        if self.property_model and "model" in self.property_model:
            self.property_model["model"].save(f"{filename_prefix}_property_model.keras")
            # Could also save scaler and attribute_names if needed for standalone
            # prediction. For example, using joblib for the scaler
            # import joblib
            # joblib.dump(self.property_model["scaler"], f"{filename_prefix}_property_model_scaler.joblib")
            # with open(f"{filename_prefix}_property_model_attrs.json", "w") as f:
            #    json.dump({"attribute_names": self.property_model["attribute_names"],
            #               "target_property": self.property_model["target_property"]}, f)

        print(f"Results exported with prefix: {filename_prefix}")
