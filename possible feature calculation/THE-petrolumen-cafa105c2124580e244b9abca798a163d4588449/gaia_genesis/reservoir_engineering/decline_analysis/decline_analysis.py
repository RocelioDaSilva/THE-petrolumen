import numpy as np
from typing import Dict, Tuple
import logging
from scipy.optimize import curve_fit

class DeclineAnalysis:
    """Classe para análise de declínio de produção."""
    
    def __init__(self):
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('DeclineAnalysis')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def _exponential_decline(self, t: np.ndarray, qi: float, di: float) -> np.ndarray:
        """Função de declínio exponencial."""
        return qi * np.exp(-di * t)
        
    def _harmonic_decline(self, t: np.ndarray, qi: float, di: float) -> np.ndarray:
        """Função de declínio harmônico."""
        return qi / (1 + di * t)
        
    def _hyperbolic_decline(self, t: np.ndarray, qi: float, di: float, b: float) -> np.ndarray:
        """Função de declínio hiperbólico."""
        return qi * (1 + b * di * t)**(-1/b)
        
    def fit_arps(self,
                time: np.ndarray,
                rate: np.ndarray,
                method: str = 'hyperbolic') -> Dict:
        """
        Ajusta curva de declínio usando o método de Arps.
        
        Args:
            time: Array com tempos
            rate: Array com vazões
            method: Método de declínio ('exponential', 'harmonic' ou 'hyperbolic')
            
        Returns:
            Dicionário com parâmetros ajustados
        """
        self.logger.info(f"Ajustando curva de declínio usando método {method}")
        
        if method == 'exponential':
            # Ajuste exponencial
            popt, pcov = curve_fit(self._exponential_decline, time, rate, p0=[rate[0], 0.1])
            qi, di = popt
            
            return {
                'qi': qi,
                'di': di,
                'b': 0,
                'method': 'exponential'
            }
            
        elif method == 'harmonic':
            # Ajuste harmônico
            popt, pcov = curve_fit(self._harmonic_decline, time, rate, p0=[rate[0], 0.1])
            qi, di = popt
            
            return {
                'qi': qi,
                'di': di,
                'b': 1,
                'method': 'harmonic'
            }
            
        else:  # hyperbolic
            # Ajuste hiperbólico
            popt, pcov = curve_fit(self._hyperbolic_decline, time, rate, p0=[rate[0], 0.1, 0.5])
            qi, di, b = popt
            
            return {
                'qi': qi,
                'di': di,
                'b': b,
                'method': 'hyperbolic'
            }
            
    def forecast_production(self,
                          params: Dict,
                          time: np.ndarray) -> np.ndarray:
        """
        Previsão de produção usando parâmetros ajustados.
        
        Args:
            params: Dicionário com parâmetros ajustados
            time: Array com tempos para previsão
            
        Returns:
            Array com vazões previstas
        """
        if params['method'] == 'exponential':
            return self._exponential_decline(time, params['qi'], params['di'])
        elif params['method'] == 'harmonic':
            return self._harmonic_decline(time, params['qi'], params['di'])
        else:  # hyperbolic
            return self._hyperbolic_decline(time, params['qi'], params['di'], params['b'])
            
    def calculate_eur(self,
                     params: Dict,
                     economic_limit: float) -> float:
        """
        Calcula EUR (Estimated Ultimate Recovery).
        
        Args:
            params: Dicionário com parâmetros ajustados
            economic_limit: Vazão limite econômica
            
        Returns:
            EUR (MMbbl ou MMscf)
        """
        if params['method'] == 'exponential':
            eur = params['qi'] / params['di']
        elif params['method'] == 'harmonic':
            eur = params['qi'] * np.log(params['qi'] / economic_limit) / params['di']
        else:  # hyperbolic
            b = params['b']
            eur = params['qi'] * ((params['qi'] / economic_limit)**b - 1) / (b * params['di'])
            
        self.logger.info(f"EUR calculado: {eur:.2f}")
        return eur
        
    def calculate_remaining_life(self,
                               params: Dict,
                               current_rate: float,
                               economic_limit: float) -> float:
        """
        Calcula vida remanescente do poço.
        
        Args:
            params: Dicionário com parâmetros ajustados
            current_rate: Vazão atual
            economic_limit: Vazão limite econômica
            
        Returns:
            Vida remanescente (anos)
        """
        if params['method'] == 'exponential':
            t = np.log(current_rate / economic_limit) / params['di']
        elif params['method'] == 'harmonic':
            t = (current_rate / economic_limit - 1) / params['di']
        else:  # hyperbolic
            b = params['b']
            t = ((current_rate / economic_limit)**b - 1) / (b * params['di'])
            
        self.logger.info(f"Vida remanescente calculada: {t:.2f} anos")
        return t 