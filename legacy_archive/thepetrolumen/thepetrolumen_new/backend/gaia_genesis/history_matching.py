import numpy as np
import pandas as pd
from scipy.optimize import minimize, differential_evolution
from sklearn.metrics import mean_squared_error  # Removed r2_score
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Callable, Tuple, Optional  # Removed List

# import streamlit as st # Unused


class HistoryMatching:
    def __init__(self):
        """Inicializa o objeto de ajuste de histórico."""
        self.historical_data = None
        self.simulation_results = None
        self.parameters = {}
        self.parameter_bounds = {}
        self.objective_function = None
        self.optimization_method = None
        self.optimization_results = None
        self.sensitivity_results = None

    def load_historical_data(
        self,
        data: pd.DataFrame,
        time_col: str,
        pressure_col: str,
        production_cols: Dict[str, str],
    ):
        """
        Carrega dados históricos.

        Args:
            data: DataFrame com dados históricos
            time_col: Nome da coluna de tempo
            pressure_col: Nome da coluna de pressão
            production_cols: Dicionário com nomes das colunas de produção
                           {'oil': 'oil_col', 'water': 'water_col', 'gas': 'gas_col'}
        """
        self.historical_data = {
            "time": data[time_col].values,
            "pressure": data[pressure_col].values,
            "production": {
                phase: data[col].values for phase, col in production_cols.items()
            },
        }

    def add_parameter(
        self,
        name: str,
        initial_value: float,
        bounds: Tuple[float, float],
        description: str = "",
    ):
        """
        Adiciona parâmetro para ajuste.

        Args:
            name: Nome do parâmetro
            initial_value: Valor inicial
            bounds: Tupla com limites (min, max)
            description: Descrição do parâmetro
        """
        self.parameters[name] = {
            "value": initial_value,
            "bounds": bounds,
            "description": description,
        }
        self.parameter_bounds[name] = bounds

    def set_objective_function(self, func: Callable):
        """
        Define função objetivo para otimização.

        Args:
            func: Função que recebe parâmetros e retorna erro
        """
        self.objective_function = func

    def calculate_error(
        self,
        simulated: Dict[str, np.ndarray],
        weights: Optional[Dict[str, float]] = None,
    ) -> float:
        """
        Calcula erro entre dados simulados e históricos.

        Args:
            simulated: Dicionário com resultados simulados
            weights: Pesos para cada tipo de dado

        Returns:
            Erro total ponderado
        """
        if weights is None:
            weights = {"pressure": 1.0, "oil": 1.0, "water": 1.0, "gas": 1.0}

        total_error = 0.0

        # Erro de pressão
        if "pressure" in simulated:
            pressure_error = mean_squared_error(
                self.historical_data["pressure"], simulated["pressure"]
            )
            total_error += weights["pressure"] * pressure_error

        # Erro de produção
        for phase in ["oil", "water", "gas"]:
            if phase in simulated and phase in self.historical_data["production"]:
                production_error = mean_squared_error(
                    self.historical_data["production"][phase],
                    simulated["production"][phase],
                )
                total_error += weights[phase] * production_error

        return total_error

    def run_optimization(
        self,
        method: str = "differential_evolution",
        max_iterations: int = 100,
        population_size: int = 20,
        weights: Optional[Dict[str, float]] = None,
    ):
        """
        Executa otimização para ajuste de parâmetros.

        Args:
            method: Método de otimização ('differential_evolution' ou 'nelder-mead')
            max_iterations: Número máximo de iterações
            population_size: Tamanho da população (apenas para differential_evolution)
            weights: Pesos para cada tipo de dado
        """
        self.optimization_method = method

        # Preparar parâmetros iniciais e limites
        initial_params = np.array([p["value"] for p in self.parameters.values()])
        bounds = [p["bounds"] for p in self.parameters.values()]

        # Definir função objetivo
        def objective(x):
            # Atualizar parâmetros
            for i, (name, _) in enumerate(self.parameters.items()):
                self.parameters[name]["value"] = x[i]

            # Executar simulação com novos parâmetros
            simulated = self.run_simulation()

            # Calcular erro
            return self.calculate_error(simulated, weights)

        # Executar otimização
        if method == "differential_evolution":
            result = differential_evolution(
                objective,
                bounds=bounds,
                maxiter=max_iterations,
                popsize=population_size,
                mutation=(0.5, 1.0),
                recombination=0.7,
                seed=42,
            )
        else:  # nelder-mead
            result = minimize(
                objective,
                x0=initial_params,
                method="Nelder-Mead",
                bounds=bounds,
                options={"maxiter": max_iterations},
            )

        self.optimization_results = {
            "success": result.success,
            "message": result.message,
            "fun": result.fun,
            "x": result.x,
            "nit": result.niter if method == "differential_evolution" else result.nit,
        }

        # Atualizar parâmetros com valores otimizados
        for i, (name, _) in enumerate(self.parameters.items()):
            self.parameters[name]["value"] = result.x[i]

    def run_sensitivity_analysis(self, n_samples: int = 100) -> Dict:
        """
        Executa análise de sensibilidade dos parâmetros.

        Args:
            n_samples: Número de amostras para análise

        Returns:
            Dicionário com resultados da análise
        """
        results = {}

        for name, param in self.parameters.items():
            # Gerar amostras
            values = np.linspace(param["bounds"][0], param["bounds"][1], n_samples)
            errors = []

            # Calcular erro para cada valor
            for value in values:
                # Atualizar parâmetro
                self.parameters[name]["value"] = value

                # Executar simulação
                simulated = self.run_simulation()

                # Calcular erro
                error = self.calculate_error(simulated)
                errors.append(error)

            # Calcular sensibilidade
            sensitivity = np.std(errors) / np.mean(errors)

            results[name] = {
                "values": values,
                "errors": errors,
                "sensitivity": sensitivity,
            }

        self.sensitivity_results = results
        return results

    def plot_history_match(self, simulated: Dict[str, np.ndarray]):
        """
        Plota comparação entre dados históricos e simulados.

        Args:
            simulated: Dicionário com resultados simulados
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        # Pressão
        axes[0, 0].plot(
            self.historical_data["time"],
            self.historical_data["pressure"],
            "ko-",
            label="Histórico",
        )
        axes[0, 0].plot(
            self.historical_data["time"], simulated["pressure"], "r--", label="Simulado"
        )
        axes[0, 0].set_title("Pressão")
        axes[0, 0].set_xlabel("Tempo")
        axes[0, 0].set_ylabel("Pressão (psia)")
        axes[0, 0].legend()
        axes[0, 0].grid(True)

        # Produção
        for i, phase in enumerate(["oil", "water", "gas"]):
            if phase in simulated and phase in self.historical_data["production"]:
                row = (i + 1) // 2
                col = (i + 1) % 2

                axes[row, col].plot(
                    self.historical_data["time"],
                    self.historical_data["production"][phase],
                    "ko-",
                    label="Histórico",
                )
                axes[row, col].plot(
                    self.historical_data["time"],
                    simulated["production"][phase],
                    "r--",
                    label="Simulado",
                )
                axes[row, col].set_title(f"Produção de {phase}")
                axes[row, col].set_xlabel("Tempo")
                axes[row, col].set_ylabel("Taxa de Produção")
                axes[row, col].legend()
                axes[row, col].grid(True)

        plt.tight_layout()
        return fig

    def plot_sensitivity(self):
        """Plota resultados da análise de sensibilidade."""
        if self.sensitivity_results is None:
            raise ValueError("Execute a análise de sensibilidade primeiro")

        fig, ax = plt.subplots(figsize=(10, 6))

        sensitivities = {
            name: results["sensitivity"]
            for name, results in self.sensitivity_results.items()
        }

        # Ordenar por sensibilidade
        sorted_sens = dict(
            sorted(sensitivities.items(), key=lambda x: x[1], reverse=True)
        )

        # Plotar barras
        ax.bar(range(len(sorted_sens)), list(sorted_sens.values()))

        # Configurar eixo x
        ax.set_xticks(range(len(sorted_sens)))
        ax.set_xticklabels(list(sorted_sens.keys()), rotation=45, ha="right")

        ax.set_title("Sensibilidade dos Parâmetros")
        ax.set_ylabel("Sensibilidade")
        ax.grid(True)

        plt.tight_layout()
        return fig

    def plot_parameter_correlations(self):
        """Plota matriz de correlação entre parâmetros."""
        if self.optimization_results is None:
            raise ValueError("Execute a otimização primeiro")

        # Criar DataFrame com resultados
        results = []
        for name, param in self.parameters.items():
            results.append(
                {
                    "parameter": name,
                    "value": param["value"],
                    "description": param["description"],
                }
            )

        df = pd.DataFrame(results)

        # Plotar matriz de correlação
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(df.corr(), annot=True, cmap="coolwarm", ax=ax)
        ax.set_title("Correlação entre Parâmetros")

        plt.tight_layout()
        return fig

    def export_results(self, filename: str):
        """
        Exporta resultados do ajuste de histórico.

        Args:
            filename: Nome do arquivo de saída
        """
        results = {
            "parameters": self.parameters,
            "optimization": self.optimization_results,
            "sensitivity": self.sensitivity_results,
        }

        pd.DataFrame(results).to_csv(filename, index=False)

    def run_simulation(self) -> Dict[str, np.ndarray]:
        """
        Executa simulação com parâmetros atuais.
        Deve ser implementado pela classe que herda HistoryMatching.
        """
        raise NotImplementedError("Método run_simulation deve ser implementado")
