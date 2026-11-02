import numpy as np
import pandas as pd
from typing import Dict, List, Optional  # Removed Tuple, Union
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# import tensorflow as tf # Unused
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout


class ProductionForecasting:
    def __init__(self):
        """Inicializa o sistema de previsão de produção."""
        self.historical_data = None
        self.decline_curves = {}
        self.material_balance = {}
        self.scenarios = {}
        self.ai_model = None

    def load_historical_data(self, data: pd.DataFrame):
        """
        Carrega dados históricos de produção.

        Args:
            data: DataFrame com dados históricos
        """
        self.historical_data = data

    def fit_decline_curves(
        self,
        well_name: str,
        decline_type: str = "hyperbolic",
        min_data_points: int = 30,
    ):
        """
        Ajusta curvas de declínio.

        Args:
            well_name: Nome do poço
            decline_type: Tipo de declínio ('exponential', 'hyperbolic', 'harmonic')
            min_data_points: Número mínimo de pontos para ajuste
        """
        if well_name not in self.historical_data["well_name"].unique():
            raise ValueError(f"Poço {well_name} não encontrado nos dados históricos")

        # Filtrar dados do poço
        well_data = self.historical_data[self.historical_data["well_name"] == well_name]

        if len(well_data) < min_data_points:
            raise ValueError(
                f"Dados insuficientes para ajuste (mínimo: {min_data_points})"
            )

        # Extrair variáveis
        t = well_data["time"].values
        q = well_data["rate"].values

        # Definir função de declínio
        if decline_type == "exponential":

            def decline_func(t, qi, Di):
                return qi * np.exp(-Di * t)

        elif decline_type == "hyperbolic":

            def decline_func(t, qi, Di, b):
                return qi * (1 + b * Di * t) ** (-1 / b)

        elif decline_type == "harmonic":

            def decline_func(t, qi, Di):
                return qi / (1 + Di * t)

        else:
            raise ValueError("Tipo de declínio inválido")

        # Ajustar curva
        if decline_type == "hyperbolic":
            popt, pcov = curve_fit(decline_func, t, q, p0=[q[0], 0.1, 0.5])
            qi, Di, b = popt
        else:
            popt, pcov = curve_fit(decline_func, t, q, p0=[q[0], 0.1])
            qi, Di = popt
            b = 1 if decline_type == "harmonic" else 0

        # Armazenar resultados
        self.decline_curves[well_name] = {
            "type": decline_type,
            "qi": qi,
            "Di": Di,
            "b": b,
            "r2": self._calculate_r2(q, decline_func(t, *popt)),
        }

    def forecast_production(
        self, well_name: str, forecast_period: int, decline_type: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Previsão de produção futura.

        Args:
            well_name: Nome do poço
            forecast_period: Período de previsão (dias)
            decline_type: Tipo de declínio (opcional)

        Returns:
            DataFrame com previsão
        """
        if well_name not in self.decline_curves:
            if decline_type is None:
                raise ValueError("Tipo de declínio não especificado")
            self.fit_decline_curves(well_name, decline_type)

        # Parâmetros da curva
        params = self.decline_curves[well_name]
        qi, Di, b = params["qi"], params["Di"], params["b"]

        # Gerar tempos futuros
        t_last = self.historical_data[self.historical_data["well_name"] == well_name][
            "time"
        ].max()
        t_forecast = np.arange(t_last, t_last + forecast_period + 1)

        # Calcular taxas
        if params["type"] == "exponential":
            q_forecast = qi * np.exp(-Di * t_forecast)
        elif params["type"] == "hyperbolic":
            q_forecast = qi * (1 + b * Di * t_forecast) ** (-1 / b)
        else:  # harmonic
            q_forecast = qi / (1 + Di * t_forecast)

        # Criar DataFrame
        forecast = pd.DataFrame(
            {"time": t_forecast, "rate": q_forecast, "well_name": well_name}
        )

        return forecast

    def calculate_material_balance(
        self, reservoir_name: str, pvt_data: Dict, aquifer_model: Optional[str] = None
    ):
        """
        Calcula balanço de materiais.

        Args:
            reservoir_name: Nome do reservatório
            pvt_data: Dados PVT
            aquifer_model: Modelo de aquífero (opcional)
        """
        # Extrair dados
        p = self.historical_data["pressure"].values
        Np = self.historical_data["cumulative_oil"].values
        Gp = self.historical_data["cumulative_gas"].values
        Wp = self.historical_data["cumulative_water"].values

        # Calcular parâmetros PVT
        Bo = np.interp(p, pvt_data["pressure"], pvt_data["bo"])
        Bg = np.interp(p, pvt_data["pressure"], pvt_data["bg"])
        Bw = np.interp(p, pvt_data["pressure"], pvt_data["bw"])
        Rs = np.interp(p, pvt_data["pressure"], pvt_data["rs"])

        # Calcular F (produção total)
        F = Np * (Bo + (Gp / Np - Rs) * Bg) + Wp * Bw

        # Calcular Eo (expansão do óleo)
        Eo = (Bo - Bo[0]) + (Rs[0] - Rs) * Bg

        # Calcular Eg (expansão do gás)
        Eg = Bo[0] * (Bg / Bg[0] - 1)

        # Calcular Ew (expansão da água)
        Ew = Bw - Bw[0]

        # Calcular Ef (expansão da formação)
        Ef = (p[0] - p) * (1 + pvt_data["swi"]) * pvt_data["cf"]

        # Calcular We (influxo de água)
        if aquifer_model == "fetkovich":
            We = self._calculate_fetkovich_aquifer(p, pvt_data)
        elif aquifer_model == "carter_tracy":
            We = self._calculate_carter_tracy_aquifer(p, pvt_data)
        else:
            We = np.zeros_like(p)

        # Calcular OOIP
        X = np.column_stack((Eo, Eg, Ew, Ef, We))
        y = F

        # Ajustar modelo
        model = np.linalg.lstsq(X, y, rcond=None)[0]

        # Armazenar resultados
        self.material_balance[reservoir_name] = {
            "OOIP": model[0],
            "aquifer_constant": model[4] if aquifer_model else None,
            "r2": self._calculate_r2(y, X @ model),
        }

    def generate_development_scenarios(
        self,
        reservoir_name: str,
        num_scenarios: int,
        well_spacing: List[float],
        completion_length: List[float],
        constraints: Dict,
    ):
        """
        Gera cenários de desenvolvimento.

        Args:
            reservoir_name: Nome do reservatório
            num_scenarios: Número de cenários
            well_spacing: Espaçamentos entre poços
            completion_length: Comprimentos de completação
            constraints: Restrições operacionais
        """
        scenarios = []

        for i in range(num_scenarios):
            # Gerar parâmetros aleatórios
            spacing = np.random.choice(well_spacing)
            length = np.random.choice(completion_length)

            # Calcular número de poços
            area = constraints["area"]
            num_wells = int(area / (spacing**2))

            # Gerar posições dos poços
            x = np.random.uniform(0, constraints["length"], num_wells)
            y = np.random.uniform(0, constraints["width"], num_wells)

            # Calcular produção
            production = self._calculate_scenario_production(
                num_wells, length, constraints
            )

            # Armazenar cenário
            scenarios.append(
                {
                    "spacing": spacing,
                    "completion_length": length,
                    "num_wells": num_wells,
                    "well_positions": np.column_stack((x, y)),
                    "production": production,
                }
            )

        self.scenarios[reservoir_name] = scenarios

    def optimize_eor_plan(
        self, reservoir_name: str, eor_type: str, constraints: Dict
    ) -> Dict:
        """
        Otimiza plano de recuperação avançada.

        Args:
            reservoir_name: Nome do reservatório
            eor_type: Tipo de EOR ('polymer', 'surfactant', 'thermal')
            constraints: Restrições operacionais

        Returns:
            Dicionário com plano otimizado
        """
        if eor_type == "polymer":
            # Otimizar concentração e taxa de injeção
            concentration = np.linspace(0.1, 2.0, 20)
            injection_rate = np.linspace(100, 1000, 20)

            best_recovery = 0
            best_params = {}

            for c in concentration:
                for q in injection_rate:
                    recovery = self._calculate_polymer_recovery(c, q, constraints)
                    if recovery > best_recovery:
                        best_recovery = recovery
                        best_params = {
                            "concentration": c,
                            "injection_rate": q,
                            "recovery_factor": recovery,
                        }

        elif eor_type == "surfactant":
            # Otimizar concentração e salinidade
            concentration = np.linspace(0.1, 5.0, 20)
            salinity = np.linspace(1000, 50000, 20)

            best_recovery = 0
            best_params = {}

            for c in concentration:
                for s in salinity:
                    recovery = self._calculate_surfactant_recovery(c, s, constraints)
                    if recovery > best_recovery:
                        best_recovery = recovery
                        best_params = {
                            "concentration": c,
                            "salinity": s,
                            "recovery_factor": recovery,
                        }

        elif eor_type == "thermal":
            # Otimizar temperatura e taxa de injeção
            temperature = np.linspace(200, 400, 20)
            injection_rate = np.linspace(100, 1000, 20)

            best_recovery = 0
            best_params = {}

            for t in temperature:
                for q in injection_rate:
                    recovery = self._calculate_thermal_recovery(t, q, constraints)
                    if recovery > best_recovery:
                        best_recovery = recovery
                        best_params = {
                            "temperature": t,
                            "injection_rate": q,
                            "recovery_factor": recovery,
                        }

        return best_params

    def train_ai_model(
        self, input_features: List[str], target_feature: str, model_type: str = "lstm"
    ):
        """
        Treina modelo de IA para simulação rápida.

        Args:
            input_features: Lista de features de entrada
            target_feature: Feature alvo
            model_type: Tipo de modelo ('lstm', 'rf')
        """
        # Preparar dados
        X = self.historical_data[input_features].values
        y = self.historical_data[target_feature].values

        # Dividir dados
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        if model_type == "lstm":
            # Reshape para LSTM
            X_train = X_train.reshape(X_train.shape[0], 1, X_train.shape[1])
            X_test = X_test.reshape(X_test.shape[0], 1, X_test.shape[1])

            # Criar modelo
            model = Sequential(
                [
                    LSTM(64, input_shape=(1, X_train.shape[2])),
                    Dropout(0.2),
                    Dense(32, activation="relu"),
                    Dense(1),
                ]
            )

            # Compilar e treinar
            model.compile(optimizer="adam", loss="mse")
            model.fit(X_train, y_train, epochs=100, batch_size=32, validation_split=0.2)

        else:  # random forest
            model = RandomForestRegressor(n_estimators=100)
            model.fit(X_train, y_train)

        # Avaliar modelo
        score = model.score(X_test, y_test)
        print(f"R² score: {score:.3f}")

        self.ai_model = model

    def predict_with_ai(self, input_data: np.ndarray) -> np.ndarray:
        """
        Faz previsões usando modelo de IA.

        Args:
            input_data: Dados de entrada

        Returns:
            Array com previsões
        """
        if self.ai_model is None:
            raise ValueError("Modelo de IA não treinado")

        if isinstance(self.ai_model, Sequential):
            input_data = input_data.reshape(input_data.shape[0], 1, input_data.shape[1])

        return self.ai_model.predict(input_data)

    def plot_decline_curve(self, well_name: str):
        """
        Plota curva de declínio.

        Args:
            well_name: Nome do poço
        """
        if well_name not in self.decline_curves:
            raise ValueError(f"Curva de declínio não encontrada para {well_name}")

        # Dados históricos
        well_data = self.historical_data[self.historical_data["well_name"] == well_name]
        t_hist = well_data["time"].values
        q_hist = well_data["rate"].values

        # Dados ajustados
        params = self.decline_curves[well_name]
        t_fit = np.linspace(t_hist[0], t_hist[-1], 100)

        if params["type"] == "exponential":
            q_fit = params["qi"] * np.exp(-params["Di"] * t_fit)
        elif params["type"] == "hyperbolic":
            q_fit = params["qi"] * (1 + params["b"] * params["Di"] * t_fit) ** (
                -1 / params["b"]
            )
        else:  # harmonic
            q_fit = params["qi"] / (1 + params["Di"] * t_fit)

        # Plotar
        plt.figure(figsize=(10, 6))
        plt.plot(t_hist, q_hist, "ko", label="Dados históricos")
        plt.plot(t_fit, q_fit, "r-", label="Curva ajustada")
        plt.xlabel("Tempo (dias)")
        plt.ylabel("Taxa (bbl/d)")
        plt.title(f"Curva de Declínio - {well_name}")
        plt.legend()
        plt.grid(True)

        return plt.gcf()

    def plot_material_balance(self, reservoir_name: str):
        """
        Plota balanço de materiais.

        Args:
            reservoir_name: Nome do reservatório
        """
        if reservoir_name not in self.material_balance:
            raise ValueError(
                f"Balanço de materiais não encontrado para {reservoir_name}"
            )

        # Dados
        p = self.historical_data["pressure"].values
        Np = self.historical_data["cumulative_oil"].values

        # Calcular F/Eo
        F = Np * (self.material_balance[reservoir_name]["OOIP"])
        Eo = (p[0] - p) / p[0]

        # Plotar
        plt.figure(figsize=(10, 6))
        plt.plot(Eo, F, "ko-")
        plt.xlabel("Eo")
        plt.ylabel("F")
        plt.title(f"Balanço de Materiais - {reservoir_name}")
        plt.grid(True)

        return plt.gcf()

    def plot_scenarios(self, reservoir_name: str):
        """
        Plota cenários de desenvolvimento.

        Args:
            reservoir_name: Nome do reservatório
        """
        if reservoir_name not in self.scenarios:
            raise ValueError(f"Cenários não encontrados para {reservoir_name}")

        # Plotar posições dos poços
        plt.figure(figsize=(12, 8))

        for i, scenario in enumerate(self.scenarios[reservoir_name]):
            plt.subplot(2, 2, i + 1)
            plt.scatter(
                scenario["well_positions"][:, 0],
                scenario["well_positions"][:, 1],
                c="b",
                marker="o",
            )
            plt.title(f'Cenário {i +1}\nEspaçamento: {scenario["spacing"]:.0f}m')
            plt.xlabel("X (m)")
            plt.ylabel("Y (m)")
            plt.grid(True)

        plt.tight_layout()

        return plt.gcf()

    def _calculate_r2(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calcula R²."""
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return 1 - (ss_res / ss_tot)

    def _calculate_fetkovich_aquifer(self, p: np.ndarray, pvt_data: Dict) -> np.ndarray:
        """Calcula influxo de água usando modelo de Fetkovich."""
        # Parâmetros do aquífero
        J = pvt_data["aquifer_constant"]
        pi = pvt_data["initial_pressure"]
        We_max = pvt_data["aquifer_volume"]

        # Calcular influxo
        We = np.zeros_like(p)
        for i in range(1, len(p)):
            dp = pi - p[i]
            We[i] = We[i - 1] + J * dp * (1 - We[i - 1] / We_max)

        return We

    def _calculate_carter_tracy_aquifer(
        self, p: np.ndarray, pvt_data: Dict
    ) -> np.ndarray:
        """Calcula influxo de água usando modelo de Carter-Tracy."""
        # Parâmetros do aquífero
        U = pvt_data["aquifer_constant"]
        pi = pvt_data["initial_pressure"]
        t = np.arange(len(p))

        # Calcular influxo
        We = np.zeros_like(p)
        for i in range(1, len(p)):
            dp = pi - p[i]
            We[i] = U * dp * np.sqrt(t[i])

        return We

    def _calculate_scenario_production(
        self, num_wells: int, completion_length: float, constraints: Dict
    ) -> Dict:
        """Calcula produção para um cenário."""
        # Parâmetros
        qi = constraints["initial_rate"]
        b = constraints["b_factor"]
        Di = constraints["initial_decline"]

        # Calcular produção
        t = np.arange(constraints["forecast_period"])
        q = qi * (1 + b * Di * t) ** (-1 / b)

        # Ajustar para comprimento de completação
        q *= completion_length / constraints["reference_length"]

        # Calcular produção total
        Q = np.sum(q) * num_wells

        return {"time": t, "rate": q, "cumulative": Q}

    def _calculate_polymer_recovery(
        self, concentration: float, injection_rate: float, constraints: Dict
    ) -> float:
        """Calcula recuperação para injeção de polímero."""
        # Parâmetros
        mu_water = constraints["water_viscosity"]
        mu_polymer = mu_water * (1 + concentration)
        mobility_ratio = mu_water / mu_polymer

        # Calcular recuperação
        recovery = constraints["base_recovery"] * (1 + 0.1 * (1 - mobility_ratio))

        return recovery

    def _calculate_surfactant_recovery(
        self, concentration: float, salinity: float, constraints: Dict
    ) -> float:
        """Calcula recuperação para injeção de surfactante."""
        # Parâmetros
        IFT = constraints["base_IFT"] * np.exp(-concentration / 0.1)
        capillary_number = IFT / salinity

        # Calcular recuperação
        recovery = constraints["base_recovery"] * (1 + 0.2 * capillary_number)

        return recovery

    def _calculate_thermal_recovery(
        self, temperature: float, injection_rate: float, constraints: Dict
    ) -> float:
        """Calcula recuperação para recuperação térmica."""
        # Parâmetros
        _mu_oil = constraints["oil_viscosity"]  # noqa: F841
        _mu_steam = constraints["steam_viscosity"]  # noqa: F841
        temperature_factor = (temperature - constraints["reservoir_temperature"]) / 100

        # Calcular recuperação
        recovery = constraints["base_recovery"] * (1 + 0.3 * temperature_factor)

        return recovery
