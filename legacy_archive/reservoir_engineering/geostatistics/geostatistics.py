import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import gstools as gs
from scipy.stats import norm
import pyvista as pv

class Geostatistics:
    """Classe para análise geoestatística."""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.variogram = None
        self.kriging = None
        self.simulation = None
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('Geostatistics')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def calculate_variogram(self,
                          coordinates: np.ndarray,
                          values: np.ndarray,
                          model: str = 'spherical',
                          bin_edges: Optional[np.ndarray] = None,
                          max_dist: Optional[float] = None):
        """
        Calcula variograma.
        
        Args:
            coordinates: Coordenadas dos pontos
            values: Valores
            model: Modelo de variograma
            bin_edges: Limites dos bins
            max_dist: Distância máxima
        """
        try:
            # Calcula variograma empírico
            bin_center, gamma = gs.vario_estimate(
                coordinates,
                values,
                bin_edges=bin_edges,
                max_dist=max_dist
            )
            
            # Ajusta modelo
            self.variogram = gs.Spherical(
                dim=3,
                var=np.var(values),
                len_scale=np.mean(bin_center)
            )
            
            self.logger.info("Variograma calculado")
        except Exception as e:
            self.logger.error(f"Erro ao calcular variograma: {str(e)}")
            
    def perform_kriging(self,
                       coordinates: np.ndarray,
                       values: np.ndarray,
                       grid_coordinates: np.ndarray) -> np.ndarray:
        """
        Realiza krigagem.
        
        Args:
            coordinates: Coordenadas dos pontos
            values: Valores
            grid_coordinates: Coordenadas da grade
            
        Returns:
            Array com valores interpolados
        """
        try:
            if not self.variogram:
                raise ValueError("Variograma não calculado")
                
            # Cria objeto de krigagem
            self.kriging = gs.krige.Ordinary(
                model=self.variogram,
                cond_pos=coordinates,
                cond_val=values
            )
            
            # Realiza krigagem
            kriged_values = self.kriging(grid_coordinates)
            
            self.logger.info("Krigagem realizada")
            return kriged_values
        except Exception as e:
            self.logger.error(f"Erro ao realizar krigagem: {str(e)}")
            return None
            
    def stochastic_simulation(self,
                            coordinates: np.ndarray,
                            values: np.ndarray,
                            grid_coordinates: np.ndarray,
                            n_realizations: int = 10) -> List[np.ndarray]:
        """
        Realiza simulação estocástica.
        
        Args:
            coordinates: Coordenadas dos pontos
            values: Valores
            grid_coordinates: Coordenadas da grade
            n_realizations: Número de realizações
            
        Returns:
            Lista de realizações
        """
        try:
            if not self.variogram:
                raise ValueError("Variograma não calculado")
                
            # Cria objeto de simulação
            self.simulation = gs.SRF(
                model=self.variogram,
                mean=np.mean(values),
                var=np.var(values)
            )
            
            # Realiza simulações
            realizations = []
            for i in range(n_realizations):
                sim_values = self.simulation(grid_coordinates)
                realizations.append(sim_values)
                
            self.logger.info(f"{n_realizations} realizações geradas")
            return realizations
        except Exception as e:
            self.logger.error(f"Erro ao realizar simulação: {str(e)}")
            return []
            
    def analyze_uncertainty(self,
                          realizations: List[np.ndarray]) -> Dict:
        """
        Analisa incerteza das simulações.
        
        Args:
            realizations: Lista de realizações
            
        Returns:
            Dicionário com estatísticas
        """
        try:
            # Converte para array
            realizations_array = np.array(realizations)
            
            # Calcula estatísticas
            stats = {
                'mean': np.mean(realizations_array, axis=0),
                'std': np.std(realizations_array, axis=0),
                'p10': np.percentile(realizations_array, 10, axis=0),
                'p50': np.percentile(realizations_array, 50, axis=0),
                'p90': np.percentile(realizations_array, 90, axis=0)
            }
            
            return stats
        except Exception as e:
            self.logger.error(f"Erro ao analisar incerteza: {str(e)}")
            return {}
            
    def visualize_variogram(self,
                          save_path: Optional[str] = None):
        """
        Visualiza variograma.
        
        Args:
            save_path: Caminho para salvar figura
        """
        try:
            if not self.variogram:
                raise ValueError("Variograma não calculado")
                
            # Plota variograma
            self.variogram.plot()
            
            if save_path:
                import matplotlib.pyplot as plt
                plt.savefig(save_path)
                plt.close()
            else:
                plt.show()
                
        except Exception as e:
            self.logger.error(f"Erro ao visualizar variograma: {str(e)}")
            
    def visualize_simulation(self,
                           grid: pv.UniformGrid,
                           realization: np.ndarray,
                           save_path: Optional[str] = None):
        """
        Visualiza simulação.
        
        Args:
            grid: Grade do modelo
            realization: Realização
            save_path: Caminho para salvar figura
        """
        try:
            plotter = pv.Plotter()
            plotter.add_mesh(grid, scalars=realization)
            
            if save_path:
                plotter.screenshot(save_path)
            else:
                plotter.show()
                
        except Exception as e:
            self.logger.error(f"Erro ao visualizar simulação: {str(e)}")
            
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