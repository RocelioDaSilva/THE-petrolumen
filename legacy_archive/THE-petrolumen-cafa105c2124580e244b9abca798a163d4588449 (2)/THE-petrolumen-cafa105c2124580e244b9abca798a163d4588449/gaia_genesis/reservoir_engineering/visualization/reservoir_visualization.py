import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Optional
import logging
from ..simulation.reservoir_simulation import ReservoirSimulation

class ReservoirVisualization:
    """Classe para visualização de dados do reservatório."""
    
    def __init__(self, simulator: ReservoirSimulation):
        self.simulator = simulator
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('ReservoirVisualization')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def plot_saturation_map(self,
                          layer: int,
                          property_name: str = 'saturation',
                          cmap: str = 'viridis',
                          title: Optional[str] = None) -> plt.Figure:
        """
        Plota mapa de saturação.
        
        Args:
            layer: Camada a ser plotada
            property_name: Nome da propriedade
            cmap: Mapa de cores
            title: Título do gráfico
            
        Returns:
            Figura do matplotlib
        """
        data = self.simulator.get_grid_property(property_name)[:, :, layer]
        
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(data, cmap=cmap)
        plt.colorbar(im, ax=ax, label=property_name)
        
        if title is None:
            title = f'Mapa de {property_name} - Camada {layer}'
        ax.set_title(title)
        
        # Adiciona poços
        for well_name, well_data in self.simulator.wells.items():
            i, j, k = well_data['position']
            if k == layer:
                ax.plot(j, i, 'ko')
                ax.text(j, i, well_name, ha='center', va='bottom')
                
        self.logger.info(f"Mapa de {property_name} plotado para camada {layer}")
        return fig
        
    def plot_pressure_map(self,
                         layer: int,
                         cmap: str = 'viridis',
                         title: Optional[str] = None) -> plt.Figure:
        """
        Plota mapa de pressão.
        
        Args:
            layer: Camada a ser plotada
            cmap: Mapa de cores
            title: Título do gráfico
            
        Returns:
            Figura do matplotlib
        """
        return self.plot_saturation_map(layer, 'pressure', cmap, title)
        
    def plot_well_performance(self,
                            well_name: str,
                            time: np.ndarray,
                            rate: np.ndarray,
                            pressure: Optional[np.ndarray] = None,
                            title: Optional[str] = None) -> plt.Figure:
        """
        Plota performance do poço.
        
        Args:
            well_name: Nome do poço
            time: Array com tempos
            rate: Array com vazões
            pressure: Array com pressões (opcional)
            title: Título do gráfico
            
        Returns:
            Figura do matplotlib
        """
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # Vazão
        ax1.plot(time, rate, 'b-', label='Vazão')
        ax1.set_xlabel('Tempo')
        ax1.set_ylabel('Vazão', color='b')
        ax1.tick_params(axis='y', labelcolor='b')
        
        # Pressão
        if pressure is not None:
            ax2 = ax1.twinx()
            ax2.plot(time, pressure, 'r-', label='Pressão')
            ax2.set_ylabel('Pressão', color='r')
            ax2.tick_params(axis='y', labelcolor='r')
            
        if title is None:
            title = f'Performance do Poço {well_name}'
        ax1.set_title(title)
        
        # Legenda
        lines1, labels1 = ax1.get_legend_handles_labels()
        if pressure is not None:
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        else:
            ax1.legend(loc='upper right')
            
        self.logger.info(f"Performance do poço {well_name} plotada")
        return fig
        
    def plot_cross_section(self,
                          axis: str,
                          index: int,
                          property_name: str = 'pressure',
                          cmap: str = 'viridis',
                          title: Optional[str] = None) -> plt.Figure:
        """
        Plota seção transversal.
        
        Args:
            axis: Eixo da seção ('x', 'y' ou 'z')
            index: Índice da seção
            property_name: Nome da propriedade
            cmap: Mapa de cores
            title: Título do gráfico
            
        Returns:
            Figura do matplotlib
        """
        data = self.simulator.get_grid_property(property_name)
        
        if axis == 'x':
            section = data[index, :, :]
            xlabel, ylabel = 'Y', 'Z'
        elif axis == 'y':
            section = data[:, index, :]
            xlabel, ylabel = 'X', 'Z'
        else:  # z
            section = data[:, :, index]
            xlabel, ylabel = 'X', 'Y'
            
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(section, cmap=cmap)
        plt.colorbar(im, ax=ax, label=property_name)
        
        if title is None:
            title = f'Seção {axis.upper()} - {property_name}'
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        self.logger.info(f"Seção {axis.upper()} plotada para {property_name}")
        return fig
        
    def plot_3d_property(self,
                        property_name: str,
                        cmap: str = 'viridis',
                        title: Optional[str] = None) -> plt.Figure:
        """
        Plota propriedade em 3D.
        
        Args:
            property_name: Nome da propriedade
            cmap: Mapa de cores
            title: Título do gráfico
            
        Returns:
            Figura do matplotlib
        """
        from mpl_toolkits.mplot3d import Axes3D
        
        data = self.simulator.get_grid_property(property_name)
        x, y, z = np.meshgrid(
            np.arange(self.simulator.nx),
            np.arange(self.simulator.ny),
            np.arange(self.simulator.nz)
        )
        
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        scatter = ax.scatter(x, y, z, c=data.flatten(), cmap=cmap)
        plt.colorbar(scatter, label=property_name)
        
        if title is None:
            title = f'Visualização 3D - {property_name}'
        ax.set_title(title)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        
        self.logger.info(f"Visualização 3D plotada para {property_name}")
        return fig 