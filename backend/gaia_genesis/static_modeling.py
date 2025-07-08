import numpy as np

# import pandas as pd # Unused
from typing import Dict  # List, Tuple, Optional, Union are unused
import matplotlib.pyplot as plt
from scipy.interpolate import griddata

# from scipy.stats import norm # Unused
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
from scipy.optimize import curve_fit

# import scipy.signal # Unused


class StaticModeling:
    def __init__(self):
        """Inicializa o módulo de modelagem estática."""
        self.grid = None
        self.well_data = {}
        self.seismic_data = None
        self.maps = {}
        self.properties = {}
        self.variograms = {}
        self.nmr_data = {}

    def create_3d_grid(
        self, nx: int, ny: int, nz: int, dx: float, dy: float, dz: float
    ):
        """
        Cria malha 3D para modelagem.

        Args:
            nx, ny, nz: Dimensões da malha
            dx, dy, dz: Tamanho das células
        """
        self.grid = {
            "nx": nx,
            "ny": ny,
            "nz": nz,
            "dx": dx,
            "dy": dy,
            "dz": dz,
            "x": np.arange(0, nx * dx, dx),
            "y": np.arange(0, ny * dy, dy),
            "z": np.arange(0, nz * dz, dz),
        }

    def add_well_data(
        self,
        well_name: str,
        x: float,
        y: float,
        md: np.ndarray,
        properties: Dict[str, np.ndarray],
    ):
        """
        Adiciona dados de poço.

        Args:
            well_name: Nome do poço
            x, y: Coordenadas do poço
            md: Medidas de profundidade
            properties: Dicionário com propriedades
        """
        self.well_data[well_name] = {"x": x, "y": y, "md": md, "properties": properties}

    def add_seismic_data(
        self, seismic_cube: np.ndarray, x0: float, y0: float, dx: float, dy: float
    ):
        """
        Adiciona dados sísmicos.

        Args:
            seismic_cube: Cubo sísmico 3D
            x0, y0: Coordenadas de origem
            dx, dy: Resolução espacial
        """
        self.seismic_data = {
            "data": seismic_cube,
            "x0": x0,
            "y0": y0,
            "dx": dx,
            "dy": dy,
        }

    def add_map(
        self,
        map_name: str,
        data: np.ndarray,
        x0: float,
        y0: float,
        dx: float,
        dy: float,
    ):
        """
        Adiciona mapa 2D.

        Args:
            map_name: Nome do mapa
            data: Dados do mapa
            x0, y0: Coordenadas de origem
            dx, dy: Resolução espacial
        """
        self.maps[map_name] = {"data": data, "x0": x0, "y0": y0, "dx": dx, "dy": dy}

    def calculate_variogram(
        self,
        property_name: str,
        variogram_model: str = "spherical",  # Added model type here
        direction: str = "omnidirectional",
        max_lag: float = None,
        n_lags: int = 10,
    ):
        """
        Calcula variograma experimental.

        Args:
            property_name: Nome da propriedade
            variogram_model: Modelo de variograma a ser ajustado
            direction: Direção do variograma
            max_lag: Distância máxima
            n_lags: Número de lags
        """
        # Coletar dados
        data = []
        locations = []
        for well_name, well in self.well_data.items():
            if property_name in well["properties"]:
                data.extend(well["properties"][property_name])
                for md_val in well[
                    "md"
                ]:  # Assuming md is 1D array matching property array length
                    locations.append([well["x"], well["y"], md_val])

        if not data:
            raise ValueError(f"No data found for property: {property_name}")

        data = np.array(data)
        locations = np.array(locations)

        # Calcular distâncias
        n = len(locations)
        if n < 2:
            raise ValueError("Not enough data points to calculate variogram.")

        distances = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                if direction == "omnidirectional":
                    distances[i, j] = distances[j, i] = np.sqrt(
                        (locations[i, 0] - locations[j, 0]) ** 2
                        + (locations[i, 1] - locations[j, 1]) ** 2
                        + (locations[i, 2] - locations[j, 2]) ** 2
                    )
                else:
                    # Implementar cálculo direcional
                    # For now, fall back to omnidirectional if not specified
                    distances[i, j] = distances[j, i] = np.sqrt(
                        (locations[i, 0] - locations[j, 0]) ** 2
                        + (locations[i, 1] - locations[j, 1]) ** 2
                        + (locations[i, 2] - locations[j, 2]) ** 2
                    )
                    pass

        # Calcular variograma experimental
        if max_lag is None:
            max_lag = np.max(distances) / 2
            if max_lag == 0:  # Handle case with very few points or identical locations
                max_lag = 1.0

        lags = np.linspace(0, max_lag, n_lags)
        gamma = np.zeros(n_lags)
        n_pairs = np.zeros(n_lags, dtype=int)

        for i in range(n):
            for j in range(i + 1, n):
                d = distances[i, j]
                if d <= max_lag:
                    # Ensure lag_idx is within bounds
                    lag_idx = (
                        min(int(d / (max_lag / (n_lags - 1))), n_lags - 1)
                        if max_lag > 0
                        else 0
                    )

                    gamma[lag_idx] += (data[i] - data[j]) ** 2
                    n_pairs[lag_idx] += 1

        # Avoid division by zero for lags with no pairs
        gamma = np.divide(
            gamma, 2 * n_pairs, out=np.zeros_like(gamma), where=n_pairs != 0
        )

        # Ajustar modelo teórico
        model_func = None
        if variogram_model == "spherical":

            def spherical_model(h, c0, c1, a):
                # Ensure 'a' (range) is not zero to avoid division by zero
                a = max(a, 1e-9)
                term = h / a
                return (
                    c0
                    + c1 * (1.5 * term - 0.5 * term**3) * (h <= a)
                    + (c0 + c1) * (h > a)
                )

            model_func = spherical_model

        elif variogram_model == "exponential":

            def exponential_model(h, c0, c1, a):
                a = max(a, 1e-9)
                return c0 + c1 * (1 - np.exp(-3 * h / a))

            model_func = exponential_model

        elif variogram_model == "gaussian":

            def gaussian_model(h, c0, c1, a):
                a = max(a, 1e-9)
                return c0 + c1 * (1 - np.exp(-3 * (h / a) ** 2))

            model_func = gaussian_model

        else:
            raise ValueError(f"Unsupported variogram model: {variogram_model}")

        try:
            popt, _ = curve_fit(
                model_func,
                lags[n_pairs > 0],
                gamma[n_pairs > 0],  # Use only lags with pairs
                p0=[
                    0,
                    np.max(gamma) if np.max(gamma) > 0 else 1,
                    max_lag / 2 if max_lag > 0 else 1,
                ],
                bounds=([0, 0, 0], [np.inf, np.inf, np.inf]),
            )
            model_fit = model_func(lags, *popt)
            params = {"c0": popt[0], "c1": popt[1], "a": popt[2]}
        except RuntimeError:  # Could not converge
            params = {
                "c0": 0,
                "c1": np.max(gamma) if np.max(gamma) > 0 else 1,
                "a": max_lag / 2 if max_lag > 0 else 1,
            }
            model_fit = model_func(lags, params["c0"], params["c1"], params["a"])

        # Armazenar resultados
        self.variograms[property_name] = {
            "experimental": {"lags": lags, "gamma": gamma, "n_pairs": n_pairs},
            "model_fit": model_fit,  # Store the fitted model values
            "model_type": variogram_model,
            "parameters": params,
        }

    def kriging_interpolation(
        self, property_name: str, variogram_model: str = "spherical"
    ):
        """
        Realiza interpolação por krigagem.

        Args:
            property_name: Nome da propriedade
            variogram_model: Modelo de variograma
        """
        # Coletar dados
        points = []
        values = []
        for well_name, well in self.well_data.items():
            if property_name in well["properties"]:
                points.append([well["x"], well["y"]])  # Assuming 2D kriging for now
                values.append(
                    well["properties"][property_name][0]
                )  # Assuming single value per well for simplicity

        if not points:
            raise ValueError(
                f"No data for property {property_name} to perform kriging."
            )

        points = np.array(points)
        values = np.array(values)

        # Criar grade de interpolação
        if not self.grid:
            raise ValueError("Grid not created. Call create_3d_grid first.")

        # For 2D map, use grid's x and y.
        # If 3D kriging is intended, this part needs points from the 3D grid.
        # For now, let's assume we are creating a 2D map based on well locations.
        xi = np.linspace(self.grid["x"].min(), self.grid["x"].max(), self.grid["nx"])
        yi = np.linspace(self.grid["y"].min(), self.grid["y"].max(), self.grid["ny"])
        X, Y = np.meshgrid(xi, yi)

        # Realizar krigagem using GaussianProcessRegressor as a proxy
        # This is a simplified stand-in for a full geostatistical kriging implementation
        kernel = C(1.0, (1e-3, 1e3)) * RBF(
            length_scale=max(self.grid["dx"], self.grid["dy"]) * 5,
            length_scale_bounds=(1e-2, 1e4),
        )
        gp = GaussianProcessRegressor(
            kernel=kernel, n_restarts_optimizer=10, alpha=1e-5
        )  # Added alpha for stability

        try:
            gp.fit(points, values)
            points_pred = np.vstack([X.ravel(), Y.ravel()]).T
            values_pred, std_pred = gp.predict(points_pred, return_std=True)
        except Exception as e:
            # Fallback to simpler interpolation if GPR fails (e.g. singular matrix)
            print(
                f"Kriging (GPR) failed: {e}. Falling back to griddata linear "
                "interpolation."
            )
            values_pred = griddata(points, values, (X, Y), method="linear")
            std_pred = np.zeros_like(
                values_pred
            )  # No uncertainty estimate for griddata fallback

        # Armazenar resultados
        self.properties[property_name] = values_pred.reshape(X.shape)
        self.properties[f"{property_name}_kriging_std"] = std_pred.reshape(X.shape)

    def rock_physics_modeling(
        self,
        property_name: str,  # This argument seems unused if calculations are generic
        model_type: str = "gassmann",
    ):
        """
        Modelagem de física de rochas.

        Args:
            property_name: Nome da propriedade base para nomear o resultado (e.g. 'porosity')
            model_type: Tipo de modelo
        """
        # Default parameters, these should ideally come from data or be inputs
        K_dry = 10  # Módulo de bulk da rocha seca (GPa)
        K_min = 37  # Módulo de bulk da matriz (GPa)
        K_fluid = 2.2  # Módulo de bulk do fluido (GPa)
        G_min = 44  # Módulo de cisalhamento da matriz (GPa) for Hertz-Mindlin
        phi = 0.2  # Porosidade (fraction)

        if model_type == "gassmann":
            K_sat = K_dry + (1 - K_dry / K_min) ** 2 / (
                phi / K_fluid + (1 - phi) / K_min - K_dry / K_min**2
            )
            # Assuming G_sat = G_dry for Gassmann (shear modulus doesn't change with fluid)
            # Need G_dry, which is not defined. Let's assume a G_min relationship or a default.
            G_sat = G_min * (1 - phi)  # Simplified assumption for G_dry
            rho_bulk = 2.65 * (1 - phi) + 1.0 * phi  # Densidade do bulk (g/cm³)
            Vp = (
                np.sqrt((K_sat + 4 / 3 * G_sat) / rho_bulk) if rho_bulk > 0 else 0
            )  # Velocity P (km/s)
            Vs = (
                np.sqrt(G_sat / rho_bulk) if rho_bulk > 0 and G_sat > 0 else 0
            )  # Velocity S (km/s)

            self.properties[f"{property_name}_gassmann"] = {
                "K_sat": K_sat,
                "G_sat": G_sat,
                "Vp": Vp,
                "Vs": Vs,
                "rho_bulk": rho_bulk,
            }

        elif model_type == "hertz_mindlin":
            phi_c = 0.4  # Porosidade crítica
            P = 20  # Pressão efetiva (MPa)
            nu = 0.25  # Razão de Poisson

            K_hm = (
                G_min**2 * (1 - phi) ** 2 * P / (18 * np.pi**2 * (1 - nu) ** 2)
            ) ** (1 / 3)
            G_hm = (
                (5 - 4 * nu)
                / (5 * (2 - nu))
                * (3 * G_min**2 * (1 - phi) ** 2 * P / (2 * np.pi**2 * (1 - nu) ** 2))
                ** (1 / 3)
            )

            zeta = (
                G_hm / 6 * (9 * K_hm + 8 * G_hm) / (K_hm + 2 * G_hm)
                if (K_hm + 2 * G_hm) != 0
                else 0
            )

            K_sat_denom = (
                (phi / phi_c) / (K_hm + 4 / 3 * G_hm)
                + (1 - phi / phi_c) / (K_min + 4 / 3 * G_hm)
                if (K_hm + 4 / 3 * G_hm) != 0 and (K_min + 4 / 3 * G_hm) != 0
                else np.inf
            )
            K_sat = (1 / K_sat_denom) - 4 / 3 * G_hm if K_sat_denom != 0 else 0

            G_sat_denom = (
                ((phi / phi_c) / (G_hm + zeta) + (1 - phi / phi_c) / (G_min + zeta))
                if (G_hm + zeta) != 0 and (G_min + zeta) != 0
                else np.inf
            )
            G_sat = (1 / G_sat_denom) - zeta if G_sat_denom != 0 else 0

            rho_bulk = 2.65 * (1 - phi) + 1.0 * phi  # Densidade do bulk (g/cm³)
            Vp = np.sqrt((K_sat + 4 / 3 * G_sat) / rho_bulk) if rho_bulk > 0 else 0
            Vs = np.sqrt(G_sat / rho_bulk) if rho_bulk > 0 and G_sat > 0 else 0

            self.properties[f"{property_name}_hertz_mindlin"] = {
                "K_sat": K_sat,
                "G_sat": G_sat,
                "Vp": Vp,
                "Vs": Vs,
                "rho_bulk": rho_bulk,
            }

        else:
            raise ValueError(f"Modelo {model_type} não implementado")

    def analyze_nmr_data(
        self, well_name: str, t2_distribution: np.ndarray, t2_times: np.ndarray
    ):
        """
        Análise de dados de RMN.

        Args:
            well_name: Nome do poço
            t2_distribution: Distribuição T2
            t2_times: Tempos T2
        """
        if np.sum(t2_distribution) == 0:  # Avoid division by zero
            t2_ml, bvi, ffv = 0, 0, 0
        else:
            t2_ml = np.sum(t2_distribution * t2_times) / np.sum(t2_distribution)
            bvi = np.sum(t2_distribution[t2_times < 33]) / np.sum(t2_distribution)
            ffv = np.sum(t2_distribution[t2_times > 33]) / np.sum(t2_distribution)

        rho2 = 0.1  # Constante de relaxação superficial (μm/ms)
        pore_sizes = t2_times * rho2

        k_coates = (ffv / bvi) ** 2 * (t2_ml / 10) ** 4 if bvi != 0 else 0
        k_sdr = 4 * (t2_ml**2)

        sigma = 72  # Tensão superficial (dyn/cm)
        theta = 0  # Ângulo de contato (degrees)
        # Convert theta to radians for np.cos
        pc = (2 * sigma * np.cos(np.deg2rad(theta))) / np.maximum(
            pore_sizes, 1e-9
        )  # Avoid division by zero for pore_sizes

        self.nmr_data[well_name] = {
            "t2_ml": t2_ml,
            "bvi": bvi,
            "ffv": ffv,
            "t2_distribution": t2_distribution.tolist(),
            "t2_times": t2_times.tolist(),  # For JSON serializability
            "pore_sizes": pore_sizes.tolist(),
            "k_coates": k_coates,
            "k_sdr": k_sdr,
            "pc": pc.tolist(),
        }

    def plot_variogram(self, property_name: str):
        """
        Plota variograma.

        Args:
            property_name: Nome da propriedade
        """
        if property_name not in self.variograms:
            raise ValueError(f"Variogram for {property_name} not calculated.")
        variogram = self.variograms[property_name]

        plt.figure(figsize=(10, 6))
        plt.plot(
            variogram["experimental"]["lags"],
            variogram["experimental"]["gamma"],
            "o",
            label="Experimental",
        )
        plt.plot(
            variogram["experimental"]["lags"],
            variogram["model_fit"],  # Use 'model_fit'
            "-",
            label=f"Modelo {variogram['model_type']}",
        )
        plt.xlabel("Lag Distance")
        plt.ylabel("Semivariance")
        plt.title(f"Variograma - {property_name}")
        plt.legend()
        plt.grid(True)

        return plt.gcf()

    def plot_property_map(self, property_name: str):
        """
        Plota mapa de propriedade.

        Args:
            property_name: Nome da propriedade
        """
        if property_name not in self.properties:
            raise ValueError(
                f"Property {property_name} not found in stored properties."
            )
        data = self.properties[property_name]

        plt.figure(figsize=(10, 8))
        plt.imshow(
            data,
            cmap="viridis",
            origin="lower",
            extent=(
                [
                    self.grid["x"].min(),
                    self.grid["x"].max(),
                    self.grid["y"].min(),
                    self.grid["y"].max(),
                ]
                if self.grid
                else None
            ),
        )
        plt.colorbar(label=property_name)
        plt.title(f"Mapa de {property_name}")

        for well_name, well in self.well_data.items():
            plt.plot(
                well["x"],
                well["y"],
                "ro",
                markersize=5,
                label=(
                    well_name
                    if well_name not in plt.gca().get_legend_handles_labels()[1]
                    else ""
                ),
            )  # Avoid duplicate labels
            plt.text(well["x"], well["y"], f"  {well_name}", va="bottom", ha="left")

        if self.well_data:  # Only add legend if there are wells
            plt.legend()

        return plt.gcf()

    def plot_nmr_analysis(self, well_name: str):
        """
        Plota análise de RMN.

        Args:
            well_name: Nome do poço
        """
        if well_name not in self.nmr_data:
            raise ValueError(f"NMR data for well {well_name} not found.")
        nmr_data = self.nmr_data[well_name]

        fig = plt.figure(figsize=(15, 5))

        plt.subplot(131)
        plt.semilogx(
            nmr_data["t2_times"],
            nmr_data["t2_distribution"],
            "-",
            label="Distribuição T2",
        )
        plt.axvline(x=33, color="r", linestyle="--", label="BVI Cutoff (33ms)")
        plt.xlabel("T2 (ms)")
        plt.ylabel("Amplitude")
        plt.title("Distribuição T2")
        plt.legend()
        plt.grid(True)

        plt.subplot(132)
        plt.semilogx(
            nmr_data["pore_sizes"],
            nmr_data["t2_distribution"],
            "-",
            label="Distribuição de Poros",
        )
        plt.xlabel("Tamanho de Poros (μm)")
        plt.ylabel("Amplitude")
        plt.title("Distribuição de Tamanho de Poros")
        plt.grid(True)

        plt.subplot(133)
        plt.semilogx(
            nmr_data["pc"], nmr_data["t2_distribution"], "-", label="Curva Capilar"
        )
        plt.xlabel("Pressão Capilar (psi)")
        plt.ylabel("Amplitude")
        plt.title("Curva de Pressão Capilar")
        plt.grid(True)

        fig.suptitle(f"Análise de RMN - {well_name}")
        plt.tight_layout(
            rect=[0, 0, 1, 0.96]
        )  # Adjust layout to make space for suptitle

        return fig

    def monte_carlo_simulation(
        self, property_name: str, n_realizations: int = 100, seed: int = None
    ):
        """
        Realiza simulação de Monte Carlo. (Simplified version)

        Args:
            property_name: Nome da propriedade
            n_realizations: Número de realizações
            seed: Semente para reprodutibilidade
        """
        if property_name not in self.properties:
            raise ValueError(
                f"Base property {property_name} not found for Monte Carlo."
            )
        if property_name not in self.variograms:
            raise ValueError(
                f"Variogram for {property_name} not calculated. Needed for spatial "
                "correlation."
            )

        if seed is not None:
            np.random.seed(seed)

        base_property = self.properties[property_name]
        variogram = self.variograms[property_name]
        params = variogram["parameters"]  # c0 (nugget), c1 (sill-nugget), a (range)

        realizations = []
        for _ in range(n_realizations):
            # This is a highly simplified way to generate correlated fields.
            # A proper geostatistical simulation (e.g., SGS, SIS) would be more complex.
            # Here, we generate random noise and smooth it, then scale by variogram.
            # random_field = np.random.normal(0, 1, base_property.shape) # F841: unused

            # Simplified smoothing (convolution with a basic kernel related to range 'a')
            # This is not a true geostatistical simulation based on variogram model.
            # A Gaussian kernel size could be related to 'a'.
            # For simplicity, let's use a small Gaussian filter.
            # This part needs a proper geostatistical library or more complex
            # implementation for accuracy. For demonstration, we'll just add scaled
            # random noise to the mean. A better approach would involve Cholesky
            # decomposition of covariance matrix if feasible.

            # Placeholder: Add random noise scaled by sill. This lacks spatial correlation.
            # A more correct (but still simplified) approach might involve FFT-based
            # filtering or simpler: generate unconditional simulation then condition it.
            # For now, let's assume the base_property is a mean field and we add
            # variability.

            # Simplified: perturb the mean field by random noise scaled by sill
            # This doesn't properly use the variogram range 'a' for spatial structure.
            noise_scale = np.sqrt(
                params.get("c0", 0) + params.get("c1", 1)
            )  # Total sill
            realization = base_property + np.random.normal(
                0, noise_scale * 0.1, base_property.shape
            )  # 10% of sill as noise std
            realizations.append(
                np.clip(
                    realization,
                    np.min(base_property) * 0.5,
                    np.max(base_property) * 1.5,
                )
            )  # Basic clipping

        self.properties[f"{property_name}_realizations"] = np.array(realizations)

    def calculate_uncertainty(self, property_name: str, confidence: float = 0.95):
        """
        Calcula incerteza das realizações.

        Args:
            property_name: Nome da propriedade
            confidence: Nível de confiança
        """
        realizations_key = f"{property_name}_realizations"
        if realizations_key not in self.properties:
            raise ValueError(f"Monte Carlo realizations for {property_name} not found.")

        realizations = self.properties[realizations_key]

        mean = np.mean(realizations, axis=0)
        std = np.std(realizations, axis=0)

        # Calculate P10, P50, P90 or specific confidence interval
        alpha = (1.0 - confidence) / 2.0
        lower_percentile = alpha * 100
        upper_percentile = (1.0 - alpha) * 100

        p10 = np.percentile(realizations, 10, axis=0)
        p50 = np.median(realizations, axis=0)  # Median is P50
        p90 = np.percentile(realizations, 90, axis=0)

        lower_ci = np.percentile(realizations, lower_percentile, axis=0)
        upper_ci = np.percentile(realizations, upper_percentile, axis=0)

        self.properties[f"{property_name}_uncertainty"] = {
            "mean": mean,
            "std": std,
            "p10": p10,
            "p50": p50,
            "p90": p90,
            f"lower_ci_{confidence * 100:.0f}": lower_ci,
            f"upper_ci_{confidence * 100:.0f}": upper_ci,
        }

    def plot_uncertainty(self, property_name: str):
        """
        Plota resultados da análise de incerteza.

        Args:
            property_name: Nome da propriedade
        """
        uncertainty_key = f"{property_name}_uncertainty"
        if uncertainty_key not in self.properties:
            raise ValueError(f"Uncertainty for {property_name} not calculated.")

        uncertainty = self.properties[uncertainty_key]

        fig = plt.figure(figsize=(15, 5))

        plt.subplot(131)
        plt.imshow(
            uncertainty["mean"],
            cmap="viridis",
            origin="lower",
            extent=(
                [
                    self.grid["x"].min(),
                    self.grid["x"].max(),
                    self.grid["y"].min(),
                    self.grid["y"].max(),
                ]
                if self.grid
                else None
            ),
        )
        plt.colorbar(label="Mean")
        plt.title("Mean")

        plt.subplot(132)
        plt.imshow(
            uncertainty["std"],
            cmap="magma",
            origin="lower",
            extent=(
                [
                    self.grid["x"].min(),
                    self.grid["x"].max(),
                    self.grid["y"].min(),
                    self.grid["y"].max(),
                ]
                if self.grid
                else None
            ),
        )
        plt.colorbar(label="Standard Deviation")
        plt.title("Standard Deviation")

        plt.subplot(133)
        # Example: plot P90-P10 range
        p_range = uncertainty["p90"] - uncertainty["p10"]
        plt.imshow(
            p_range,
            cmap="plasma",
            origin="lower",
            extent=(
                [
                    self.grid["x"].min(),
                    self.grid["x"].max(),
                    self.grid["y"].min(),
                    self.grid["y"].max(),
                ]
                if self.grid
                else None
            ),
        )
        plt.colorbar(label="P90-P10 Range")
        plt.title("P90-P10 Range")

        fig.suptitle(f"Uncertainty Analysis - {property_name}")
        plt.tight_layout(rect=[0, 0, 1, 0.95])

        return fig
