import numpy as np
import pandas as pd

# from scipy.optimize import differential_evolution, minimize # Unused
# from sklearn.metrics import mean_squared_error # Unused
import matplotlib.pyplot as plt

# import seaborn as sns # Unused
from typing import Dict  # List, Tuple, Optional are unused
from SALib.sample import saltelli
from SALib.analyze import sobol

# import streamlit as st # Unused
import json  # For export_results


class UncertaintyAnalysis:
    def __init__(self, history_matching):
        """
        Inicializa a análise de incertezas.

        Args:
            history_matching: Objeto de ajuste de histórico
        """
        self.hm = history_matching
        self.uncertainty_results = None
        self.sensitivity_results = None
        self.optimization_results = None

    def define_parameter_ranges(self) -> Dict:
        """
        Define os intervalos de variação dos parâmetros.

        Returns:
            Dicionário com os intervalos dos parâmetros
        """
        problem = {
            "num_vars": len(self.hm.parameters),
            "names": list(self.hm.parameters.keys()),
            "bounds": [p["bounds"] for p in self.hm.parameters.values()],
        }
        return problem

    def run_uncertainty_analysis(self, n_samples: int = 1000) -> Dict:
        """
        Executa análise de incertezas usando amostragem de Saltelli.

        Args:
            n_samples: Número de amostras para análise

        Returns:
            Dicionário com resultados da análise
        """
        # Definir problema
        problem = self.define_parameter_ranges()

        # Gerar amostras
        param_values = saltelli.sample(problem, n_samples)

        # Executar simulações
        results = []
        for (
            params_set
        ) in param_values:  # Renamed 'params' to 'params_set' to avoid conflict
            # Atualizar parâmetros
            for i, name in enumerate(problem["names"]):
                self.hm.parameters[name]["value"] = params_set[i]  # Use params_set

            # Executar simulação
            simulated = (
                self.hm.run_simulation()
            )  # Make sure this method exists and is callable

            # Calcular erro
            error = self.hm.calculate_error(simulated)  # Make sure this method exists
            results.append(error)

        # Análise de Sobol
        sobol_indices = sobol.analyze(problem, np.array(results))

        self.uncertainty_results = {
            "param_values": param_values,
            "results": results,
            "sobol_indices": sobol_indices,
        }

        return self.uncertainty_results

    def run_automatic_optimization(
        self,
        method: str = "differential_evolution",
        n_runs: int = 5,
        population_size: int = 20,
        max_iterations: int = 100,
    ) -> Dict:
        """
        Executa múltiplas otimizações para encontrar diferentes soluções.

        Args:
            method: Método de otimização
            n_runs: Número de execuções
            population_size: Tamanho da população
            max_iterations: Número máximo de iterações

        Returns:
            Dicionário com resultados das otimizações
        """
        results = []

        for i in range(n_runs):
            # Executar otimização
            self.hm.run_optimization(  # Make sure this method exists
                method=method,
                max_iterations=max_iterations,
                population_size=population_size,
            )

            # Armazenar resultados
            results.append(
                {
                    "run": i + 1,
                    "parameters": {
                        name: param["value"]
                        for name, param in self.hm.parameters.items()
                    },
                    "error": self.hm.optimization_results["fun"],
                }
            )

        self.optimization_results = results
        return results

    def run_parameter_sensitivity(self, n_samples: int = 100) -> Dict:
        """
        Executa análise de sensitividade dos parâmetros.

        Args:
            n_samples: Número de amostras por parâmetro

        Returns:
            Dicionário com resultados da análise
        """
        results = {}

        for name, param_info in self.hm.parameters.items():  # Iterate through items
            # Gerar amostras
            values = np.linspace(
                param_info["bounds"][0], param_info["bounds"][1], n_samples
            )
            errors = []

            original_value = param_info["value"]  # Store original value

            # Calcular erro para cada valor
            for value_sample in values:  # Renamed 'value' to 'value_sample'
                # Atualizar parâmetro
                self.hm.parameters[name]["value"] = value_sample

                # Executar simulação
                simulated = self.hm.run_simulation()

                # Calcular erro
                error = self.hm.calculate_error(simulated)
                errors.append(error)

            self.hm.parameters[name]["value"] = original_value  # Restore original value

            # Calcular sensitividade
            sensitivity = (
                np.std(errors) / np.mean(errors) if np.mean(errors) != 0 else 0
            )

            results[name] = {
                "values": values,
                "errors": errors,
                "sensitivity": sensitivity,
            }

        self.sensitivity_results = results
        return results

    def plot_uncertainty_results(self):
        """Plota resultados da análise de incertezas."""
        if self.uncertainty_results is None:
            raise ValueError("Execute a análise de incertezas primeiro")

        # Plotar distribuição dos erros
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(self.uncertainty_results["results"], bins=50)
        ax.set_title("Distribuição dos Erros")
        ax.set_xlabel("Erro")
        ax.set_ylabel("Frequência")
        ax.grid(True)

        return fig

    def plot_sensitivity_results(self):
        """Plota resultados da análise de sensitividade."""
        if self.sensitivity_results is None:
            raise ValueError("Execute a análise de sensitividade primeiro")

        # Plotar sensitividade dos parâmetros
        fig, ax = plt.subplots(figsize=(10, 6))

        sensitivities = {
            name: results["sensitivity"]
            for name, results in self.sensitivity_results.items()
        }

        # Ordenar por sensitividade
        sorted_sens = dict(
            sorted(sensitivities.items(), key=lambda item: item[1], reverse=True)
        )

        # Plotar barras
        ax.bar(range(len(sorted_sens)), list(sorted_sens.values()))

        # Configurar eixo x
        ax.set_xticks(range(len(sorted_sens)))
        ax.set_xticklabels(list(sorted_sens.keys()), rotation=45, ha="right")

        ax.set_title("Sensitividade dos Parâmetros")
        ax.set_ylabel("Sensitividade")
        ax.grid(True)

        plt.tight_layout()
        return fig

    def plot_optimization_results(self):
        """Plota resultados das otimizações."""
        if self.optimization_results is None:
            raise ValueError("Execute a otimização primeiro")

        # Criar DataFrame com resultados
        df = pd.DataFrame(self.optimization_results)

        # Plotar evolução do erro
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(df["run"], df["error"], "o-")
        ax.set_title("Evolução do Erro nas Otimizações")
        ax.set_xlabel("Execução")
        ax.set_ylabel("Erro")
        ax.grid(True)

        return fig

    def export_results(self, filename: str):
        """
        Exporta resultados da análise.

        Args:
            filename: Nome do arquivo de saída
        """
        # Prepare data for DataFrame to handle potentially complex nested dicts in results
        export_data = {}
        if self.uncertainty_results:
            export_data["uncertainty_param_values"] = [
                str(p) for p in self.uncertainty_results.get("param_values", [])
            ]
            export_data["uncertainty_results_errors"] = self.uncertainty_results.get(
                "results", []
            )
            # Sobol indices can be complex, convert to string or simplify
            export_data["uncertainty_sobol_S1"] = str(
                self.uncertainty_results.get("sobol_indices", {}).get("S1", [])
            )
            export_data["uncertainty_sobol_ST"] = str(
                self.uncertainty_results.get("sobol_indices", {}).get("ST", [])
            )

        if self.sensitivity_results:
            for k, v in self.sensitivity_results.items():
                export_data[f"sensitivity_{k}_values"] = v.get("values", [])
                export_data[f"sensitivity_{k}_errors"] = v.get("errors", [])
                export_data[f"sensitivity_{k}_sensitivity"] = v.get("sensitivity", None)

        if self.optimization_results:
            export_data["optimization_runs"] = [
                r.get("run") for r in self.optimization_results
            ]
            export_data["optimization_errors"] = [
                r.get("error") for r in self.optimization_results
            ]
            # Parameters for each run could be flattened or stored as JSON strings
            for i, run_res in enumerate(self.optimization_results):
                export_data[f"optimization_run_{i}_params"] = str(
                    run_res.get("parameters", {})
                )

        # Create DataFrame from dict, handling unequal lengths by padding
        # (pandas default). Or convert complex structures to string representations
        # or multiple columns. For simplicity, using basic conversion; more
        # sophisticated flattening might be needed.

        # A simple approach is to save each main result type to a different sheet
        # or file. For now, let's create a potentially sparse DataFrame.
        try:
            df_export = pd.DataFrame(
                dict([(k, pd.Series(v)) for k, v in export_data.items()])
            )
            df_export.to_csv(filename, index=False)
        except Exception as e:
            print(
                "Error exporting results to CSV, consider exporting parts "
                f"separately: {e}"
            )
            # Fallback: export parts or save as JSON
            with open(filename.replace(".csv", ".json"), "w") as f:
                json.dump(
                    {
                        "uncertainty": self.uncertainty_results,
                        "sensitivity": self.sensitivity_results,
                        "optimization": self.optimization_results,
                    },
                    f,
                    default=lambda o: "<not serializable>",
                    indent=2,
                )
