import numpy as np
from typing import Dict, List, Callable
import logging
from scipy.optimize import minimize
from ..simulation.reservoir_simulation import ReservoirSimulation

class HistoryMatching:
    """Classe para ajuste de histórico de simulação."""
    
    def __init__(self, simulator: ReservoirSimulation):
        self.simulator = simulator
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('HistoryMatching')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def _objective_function(self,
                          params: np.ndarray,
                          param_names: List[str],
                          observed_data: Dict,
                          weights: Dict = None) -> float:
        """
        Função objetivo para otimização.
        
        Args:
            params: Array com valores dos parâmetros
            param_names: Lista com nomes dos parâmetros
            observed_data: Dicionário com dados observados
            weights: Dicionário com pesos para cada tipo de dado
            
        Returns:
            Valor da função objetivo
        """
        # Atualiza parâmetros do simulador
        for name, value in zip(param_names, params):
            self.simulator.set_grid_property(name, value)
            
        # Executa simulação
        self.simulator.run_simulation(timesteps=len(observed_data['time']), dt=1.0)
        
        # Calcula erro
        error = 0
        if weights is None:
            weights = {'pressure': 1.0, 'rate': 1.0}
            
        # Erro de pressão
        if 'pressure' in observed_data:
            simulated_pressure = self.simulator.get_grid_property('pressure')
            pressure_error = np.sum((simulated_pressure - observed_data['pressure'])**2)
            error += weights['pressure'] * pressure_error
            
        # Erro de vazão
        if 'rate' in observed_data:
            simulated_rate = self.simulator.get_grid_property('rate')
            rate_error = np.sum((simulated_rate - observed_data['rate'])**2)
            error += weights['rate'] * rate_error
            
        return error
        
    def match_history(self,
                     param_names: List[str],
                     param_bounds: List[tuple],
                     observed_data: Dict,
                     weights: Dict = None,
                     method: str = 'L-BFGS-B') -> Dict:
        """
        Realiza ajuste de histórico.
        
        Args:
            param_names: Lista com nomes dos parâmetros
            param_bounds: Lista com limites dos parâmetros
            observed_data: Dicionário com dados observados
            weights: Dicionário com pesos para cada tipo de dado
            method: Método de otimização
            
        Returns:
            Dicionário com resultados do ajuste
        """
        self.logger.info("Iniciando ajuste de histórico")
        
        # Valores iniciais
        x0 = np.array([self.simulator.get_grid_property(name).mean() for name in param_names])
        
        # Otimização
        result = minimize(
            self._objective_function,
            x0,
            args=(param_names, observed_data, weights),
            method=method,
            bounds=param_bounds
        )
        
        # Resultados
        optimized_params = dict(zip(param_names, result.x))
        
        return {
            'optimized_params': optimized_params,
            'objective_value': result.fun,
            'success': result.success,
            'message': result.message
        }
        
    def sensitivity_analysis(self,
                           param_names: List[str],
                           param_bounds: List[tuple],
                           observed_data: Dict,
                           n_samples: int = 100) -> Dict:
        """
        Análise de sensibilidade dos parâmetros.
        
        Args:
            param_names: Lista com nomes dos parâmetros
            param_bounds: Lista com limites dos parâmetros
            observed_data: Dicionário com dados observados
            n_samples: Número de amostras
            
        Returns:
            Dicionário com resultados da análise
        """
        self.logger.info("Iniciando análise de sensibilidade")
        
        # Amostragem de parâmetros
        param_samples = {}
        for name, (lower, upper) in zip(param_names, param_bounds):
            param_samples[name] = np.random.uniform(lower, upper, n_samples)
            
        # Avaliação da função objetivo
        objective_values = []
        for i in range(n_samples):
            params = np.array([param_samples[name][i] for name in param_names])
            obj_value = self._objective_function(params, param_names, observed_data)
            objective_values.append(obj_value)
            
        # Cálculo de sensibilidade
        sensitivity = {}
        for name in param_names:
            correlation = np.corrcoef(param_samples[name], objective_values)[0, 1]
            sensitivity[name] = abs(correlation)
            
        return {
            'sensitivity': sensitivity,
            'param_samples': param_samples,
            'objective_values': objective_values
        }
        
    def uncertainty_analysis(self,
                           param_names: List[str],
                           param_distributions: Dict,
                           observed_data: Dict,
                           n_samples: int = 1000) -> Dict:
        """
        Análise de incerteza dos parâmetros.
        
        Args:
            param_names: Lista com nomes dos parâmetros
            param_distributions: Dicionário com distribuições dos parâmetros
            observed_data: Dicionário com dados observados
            n_samples: Número de amostras
            
        Returns:
            Dicionário com resultados da análise
        """
        self.logger.info("Iniciando análise de incerteza")
        
        # Amostragem de parâmetros
        param_samples = {}
        for name in param_names:
            dist = param_distributions[name]
            param_samples[name] = dist.rvs(n_samples)
            
        # Avaliação da função objetivo
        objective_values = []
        for i in range(n_samples):
            params = np.array([param_samples[name][i] for name in param_names])
            obj_value = self._objective_function(params, param_names, observed_data)
            objective_values.append(obj_value)
            
        # Estatísticas
        statistics = {
            'mean': np.mean(objective_values),
            'std': np.std(objective_values),
            'min': np.min(objective_values),
            'max': np.max(objective_values),
            'percentiles': {
                'p10': np.percentile(objective_values, 10),
                'p50': np.percentile(objective_values, 50),
                'p90': np.percentile(objective_values, 90)
            }
        }
        
        return {
            'statistics': statistics,
            'param_samples': param_samples,
            'objective_values': objective_values
        } 