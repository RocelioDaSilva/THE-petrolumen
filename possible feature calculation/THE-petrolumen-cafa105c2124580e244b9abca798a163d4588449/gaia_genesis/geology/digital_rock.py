import numpy as np
import pyvista as pv
from typing import Dict, List, Optional, Tuple
from scipy.ndimage import binary_erosion, binary_dilation, label
from skimage import filters, morphology, segmentation
import tensorflow as tf

class DigitalRockAnalysis:
    """Análise digital de rochas (similar ao GeoDict)"""
    
    def __init__(self):
        self.rock_volume = None
        self.porosity_network = None
        self.properties = {}
        self.pore_statistics = {}
        self.permeability_tensor = None
        
    def load_microct_data(self, filename: str):
        """Carrega dados de micro-CT"""
        # Carregar dados 3D
        self.rock_volume = np.load(filename)
        
        # Normalizar dados
        self.rock_volume = (self.rock_volume - np.min(self.rock_volume)) / (
            np.max(self.rock_volume) - np.min(self.rock_volume)
        )
        
    def segment_pores(self, method: str = 'otsu'):
        """Segmenta poros da rocha"""
        if method == 'otsu':
            threshold = filters.threshold_otsu(self.rock_volume)
            self.porosity_network = self.rock_volume < threshold
        elif method == 'adaptive':
            threshold = filters.threshold_local(self.rock_volume, block_size=35)
            self.porosity_network = self.rock_volume < threshold
        elif method == 'watershed':
            gradient = filters.sobel(self.rock_volume)
            markers = np.zeros_like(self.rock_volume, dtype=int)
            markers[self.rock_volume < 0.2] = 1
            markers[self.rock_volume > 0.8] = 2
            self.porosity_network = segmentation.watershed(gradient, markers) == 1
            
    def analyze_pore_network(self):
        """Analisa rede de poros"""
        if self.porosity_network is None:
            raise ValueError("Execute a segmentação primeiro")
            
        # Calcular porosidade total
        self.properties["porosity"] = np.mean(self.porosity_network)
        
        # Identificar poros conectados
        labeled_pores, num_pores = label(self.porosity_network)
        
        # Análise de conectividade
        connectivity = []
        volumes = []
        surface_areas = []
        
        for i in range(1, num_pores + 1):
            pore = labeled_pores == i
            
            # Volume do poro
            volume = np.sum(pore)
            volumes.append(volume)
            
            # Área superficial
            surface = np.sum(morphology.erosion(pore) != pore)
            surface_areas.append(surface)
            
            # Conectividade
            connections = len(np.unique(labeled_pores[
                morphology.binary_dilation(pore)
            ])) - 2  # -2 para excluir background e o próprio poro
            connectivity.append(connections)
            
        self.pore_statistics = {
            "num_pores": num_pores,
            "volumes": np.array(volumes),
            "surface_areas": np.array(surface_areas),
            "connectivity": np.array(connectivity),
            "mean_coordination": np.mean(connectivity)
        }
        
    def calculate_permeability(self):
        """Calcula tensor de permeabilidade"""
        if self.porosity_network is None:
            raise ValueError("Execute a segmentação primeiro")
            
        # Simulação de fluxo nas três direções
        permeability = np.zeros((3, 3))
        
        for direction in range(3):
            # Criar gradiente de pressão
            pressure = np.zeros_like(self.porosity_network, dtype=float)
            slice_in = [slice(None)] * 3
            slice_out = [slice(None)] * 3
            
            slice_in[direction] = 0
            slice_out[direction] = -1
            
            pressure[tuple(slice_in)] = 1.0
            pressure[tuple(slice_out)] = 0.0
            
            # Resolver equação de Laplace
            for _ in range(100):  # Iterações
                laplace = np.zeros_like(pressure)
                for d in range(3):
                    pad_width = [(0, 0)] * 3
                    pad_width[d] = (1, 1)
                    padded = np.pad(pressure, pad_width, mode='edge')
                    slice1 = [slice(None)] * 3
                    slice2 = [slice(None)] * 3
                    slice1[d] = slice(1, -1)
                    slice2[d] = slice(2, None)
                    laplace += np.diff(np.diff(padded, axis=d), axis=d)
                
                pressure[self.porosity_network] += 0.1 * laplace[self.porosity_network]
                
            # Calcular fluxo
            velocity = np.zeros_like(pressure)
            for d in range(3):
                velocity[..., d] = -np.gradient(pressure, axis=d)
                
            # Calcular permeabilidade
            flux = np.mean(velocity[self.porosity_network])
            permeability[direction, direction] = flux
            
        self.permeability_tensor = permeability
        
    def analyze_throat_sizes(self):
        """Analisa distribuição de gargantas de poro"""
        if self.porosity_network is None:
            raise ValueError("Execute a segmentação primeiro")
            
        # Encontrar gargantas usando transformada de distância
        distance = morphology.distance_transform_edt(self.porosity_network)
        local_max = filters.peak_local_max(distance, min_distance=5)
        
        # Calcular raios das gargantas
        throat_radii = distance[tuple(local_max.T)]
        
        self.properties["throat_sizes"] = {
            "mean": np.mean(throat_radii),
            "std": np.std(throat_radii),
            "distribution": np.histogram(throat_radii, bins=50)
        }
        
    def calculate_formation_factor(self):
        """Calcula fator de formação elétrica"""
        if self.porosity_network is None:
            raise ValueError("Execute a segmentação primeiro")
            
        # Simulação de condutividade elétrica
        voltage = np.zeros_like(self.porosity_network, dtype=float)
        voltage[:, 0, :] = 1.0  # Voltagem na entrada
        
        # Resolver equação de Laplace
        for _ in range(100):
            padded = np.pad(voltage, 1, mode='edge')
            laplace = np.zeros_like(voltage)
            
            for i in range(1, padded.shape[0] - 1):
                for j in range(1, padded.shape[1] - 1):
                    for k in range(1, padded.shape[2] - 1):
                        if self.porosity_network[i-1, j-1, k-1]:
                            laplace[i-1, j-1, k-1] = (
                                padded[i+1, j, k] + padded[i-1, j, k] +
                                padded[i, j+1, k] + padded[i, j-1, k] +
                                padded[i, j, k+1] + padded[i, j, k-1] -
                                6 * padded[i, j, k]
                            )
                            
            voltage[self.porosity_network] += 0.1 * laplace[self.porosity_network]
            
        # Calcular fator de formação
        current = np.mean(np.gradient(voltage, axis=1))
        formation_factor = 1.0 / (current * self.properties["porosity"])
        
        self.properties["formation_factor"] = formation_factor
        
    def visualize_3d(self):
        """Visualiza modelo 3D da rocha"""
        # Criar grid
        grid = pv.UniformGrid()
        grid.dimensions = np.array(self.rock_volume.shape) + 1
        grid.spacing = (1, 1, 1)
        
        # Adicionar dados
        grid.cell_data["density"] = self.rock_volume.flatten()
        if self.porosity_network is not None:
            grid.cell_data["porosity"] = self.porosity_network.flatten()
            
        # Criar plotter
        plotter = pv.Plotter()
        plotter.add_mesh(grid, opacity=0.7, cmap="viridis")
        
        return plotter
        
    def export_results(self, filename: str):
        """Exporta resultados da análise"""
        results = {
            "properties": self.properties,
            "pore_statistics": self.pore_statistics,
            "permeability_tensor": self.permeability_tensor.tolist()
            if self.permeability_tensor is not None else None
        }
        
        import json
        with open(filename, 'w') as f:
            json.dump(results, f)
