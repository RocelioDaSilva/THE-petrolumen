import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
from scipy.optimize import minimize
import pyvista as pv

class HistoryMatcher:
    """Classe para ajuste de histórico e análise de incertezas."""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.parameters = {}
        self.objective_function = None
        self.simulation_results = None
        self.historical_data = None
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('HistoryMatcher')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def define_parameters(self,
                         parameters: Dict[str, Dict[str, float]]):
        """
        Define parâmetros para ajuste.
        
        Args:
            parameters: Dicionário com parâmetros e limites
        """
        self.parameters = parameters
        self.logger.info(f"{len(parameters)} parâmetros definidos")
        
    def set_historical_data(self,
                          data: pd.DataFrame):
        """
        Define dados históricos.
        
        Args:
            data: DataFrame com dados históricos
        """
        self.historical_data = data
        self.logger.info("Dados históricos definidos")
        
    def _objective_function(self,
                          params: np.ndarray,
                          simulator) -> float:
        """
        Função objetivo para otimização.
        
        Args:
            params: Parâmetros
            simulator: Simulador
            
        Returns:
            Valor da função objetivo
        """
        try:
            # Atualiza parâmetros do simulador
            for i, (param_name, _) in enumerate(self.parameters.items()):
                simulator.update_parameter(param_name, params[i])
                
            # Executa simulação
            simulator.run_simulation()
            
            # Calcula erro
            error = 0.0
            for var in ['pressure', 'saturation']:
                sim_values = simulator.solution[var]
                hist_values = self.historical_data[var]
                error += np.sum((sim_values - hist_values) ** 2)
                
            return error
        except Exception as e:
            self.logger.error(f"Erro na função objetivo: {str(e)}")
            return np.inf
            
    def run_matching(self,
                    simulator,
                    method: str = 'Nelder-Mead',
                    max_iter: int = 100) -> Dict:
        """
        Executa ajuste de histórico.
        
        Args:
            simulator: Simulador
            method: Método de otimização
            max_iter: Número máximo de iterações
            
        Returns:
            Dicionário com resultados
        """
        try:
            # Prepara parâmetros iniciais
            initial_params = []
            bounds = []
            
            for param_info in self.parameters.values():
                initial_params.append(param_info['initial'])
                bounds.append((param_info['min'], param_info['max']))
                
            # Executa otimização
            result = minimize(
                self._objective_function,
                initial_params,
                args=(simulator,),
                method=method,
                bounds=bounds,
                options={'maxiter': max_iter}
            )
            
            # Atualiza parâmetros finais
            for i, (param_name, _) in enumerate(self.parameters.items()):
                self.parameters[param_name]['final'] = result.x[i]
                
            self.logger.info("Ajuste de histórico concluído")
            return {
                'success': result.success,
                'message': result.message,
                'fun': result.fun,
                'nit': result.nit,
                'parameters': self.parameters
            }
        except Exception as e:
            self.logger.error(f"Erro no ajuste de histórico: {str(e)}")
            return {}
            
    def analyze_uncertainty(self,
                          simulator,
                          n_samples: int = 100) -> Dict:
        """
        Analisa incertezas.
        
        Args:
            simulator: Simulador
            n_samples: Número de amostras
            
        Returns:
            Dicionário com resultados
        """
        try:
            results = {
                'pressure': [],
                'saturation': []
            }
            
            # Gera amostras
            for _ in range(n_samples):
                # Amostra parâmetros
                params = {}
                for param_name, param_info in self.parameters.items():
                    params[param_name] = np.random.uniform(
                        param_info['min'],
                        param_info['max']
                    )
                    
                # Atualiza simulador
                for param_name, value in params.items():
                    simulator.update_parameter(param_name, value)
                    
                # Executa simulação
                simulator.run_simulation()
                
                # Armazena resultados
                results['pressure'].append(simulator.solution['pressure'])
                results['saturation'].append(simulator.solution['saturation'])
                
            # Calcula estatísticas
            stats = {
                'pressure': {
                    'mean': np.mean(results['pressure'], axis=0),
                    'std': np.std(results['pressure'], axis=0),
                    'p10': np.percentile(results['pressure'], 10, axis=0),
                    'p50': np.percentile(results['pressure'], 50, axis=0),
                    'p90': np.percentile(results['pressure'], 90, axis=0)
                },
                'saturation': {
                    'mean': np.mean(results['saturation'], axis=0),
                    'std': np.std(results['saturation'], axis=0),
                    'p10': np.percentile(results['saturation'], 10, axis=0),
                    'p50': np.percentile(results['saturation'], 50, axis=0),
                    'p90': np.percentile(results['saturation'], 90, axis=0)
                }
            }
            
            self.logger.info(f"Análise de incerteza concluída com {n_samples} amostras")
            return stats
        except Exception as e:
            self.logger.error(f"Erro na análise de incerteza: {str(e)}")
            return {}
            
    def visualize_results(self,
                         simulator,
                         save_path: Optional[str] = None):
        """
        Visualiza resultados.
        
        Args:
            simulator: Simulador
            save_path: Caminho para salvar figura
        """
        try:
            import matplotlib.pyplot as plt
            
            # Plota pressão
            plt.figure(figsize=(10, 6))
            plt.plot(simulator.solution['time'],
                    simulator.solution['pressure'],
                    label='Simulado')
            plt.plot(self.historical_data['time'],
                    self.historical_data['pressure'],
                    label='Histórico')
            plt.xlabel('Tempo')
            plt.ylabel('Pressão')
            plt.legend()
            
            if save_path:
                plt.savefig(f"{save_path}_pressure.png")
                plt.close()
            else:
                plt.show()
                
            # Plota saturação
            plt.figure(figsize=(10, 6))
            plt.plot(simulator.solution['time'],
                    simulator.solution['saturation'],
                    label='Simulado')
            plt.plot(self.historical_data['time'],
                    self.historical_data['saturation'],
                    label='Histórico')
            plt.xlabel('Tempo')
            plt.ylabel('Saturação')
            plt.legend()
            
            if save_path:
                plt.savefig(f"{save_path}_saturation.png")
                plt.close()
            else:
                plt.show()
                
        except Exception as e:
            self.logger.error(f"Erro ao visualizar resultados: {str(e)}")
            
    def export_results(self,
                      path: str,
                      results: Dict):
        """
        Exporta resultados.
        
        Args:
            path: Caminho para salvar
            results: Resultados
        """
        try:
            np.save(path, results)
            self.logger.info(f"Resultados exportados para {path}")
        except Exception as e:
            self.logger.error(f"Erro ao exportar resultados: {str(e)}") 