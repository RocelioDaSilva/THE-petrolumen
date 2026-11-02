import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy.interpolate import griddata
import segyio

class SeismicIntegration:
    """Módulo para integração de dados sísmicos"""
    
    def __init__(self):
        self.seismic_data = None
        self.velocity_model = None
        self.horizons = {}
        self.attributes = {}
        
    def load_segy(self, filename: str):
        """Carrega arquivo SEGY"""
        with segyio.open(filename, "r", ignore_geometry=True) as f:
            # Ler cabeçalho
            self.segy_header = {
                "sample_rate": f.header[0][117],
                "num_samples": f.samples.size,
                "num_traces": len(f.trace)
            }
            
            # Ler dados
            self.seismic_data = np.array([trace for trace in f.trace])
            
    def compute_attributes(self):
        """Calcula atributos sísmicos"""
        if self.seismic_data is None:
            raise ValueError("Dados sísmicos não carregados")
            
        # Amplitude RMS
        self.attributes["rms"] = np.sqrt(
            np.mean(self.seismic_data ** 2, axis=1)
        )
        
        # Impedância acústica relativa
        self.attributes["acoustic_impedance"] = np.gradient(
            self.seismic_data, axis=1
        )
        
        # Frequência instantânea
        hilbert = np.imag(self.seismic_data)
        phase = np.arctan2(hilbert, self.seismic_data)
        self.attributes["instant_freq"] = np.gradient(phase, axis=1)
        
    def extract_horizons(self, threshold: float = 0.5):
        """Extrai horizontes automáticos"""
        # Detectar picos de amplitude
        peaks = np.argmax(np.abs(self.seismic_data), axis=1)
        
        # Filtrar por threshold
        strong_reflectors = np.abs(self.seismic_data) > threshold
        
        # Agrupar em horizontes
        current_horizon = []
        for i, peak in enumerate(peaks):
            if strong_reflectors[i, peak]:
                current_horizon.append((i, peak))
            elif current_horizon:
                if len(current_horizon) > 10:  # Mínimo de pontos
                    horizon_name = f"horizon_{len(self.horizons)}"
                    self.horizons[horizon_name] = np.array(current_horizon)
                current_horizon = []
                
    def time_to_depth(self, velocity_model: np.ndarray):
        """Converte dados de tempo para profundidade"""
        self.velocity_model = velocity_model
        
        # Criar grid de tempo
        num_traces, num_samples = self.seismic_data.shape
        time_grid = np.linspace(0, num_samples * self.segy_header["sample_rate"],
                              num_samples)
        
        # Calcular profundidade
        depth = np.cumsum(velocity_model * self.segy_header["sample_rate"], axis=1)
        
        # Interpolar para grid regular de profundidade
        depth_grid = np.linspace(0, np.max(depth), num_samples)
        depth_seismic = np.zeros_like(self.seismic_data)
        
        for i in range(num_traces):
            depth_seismic[i] = np.interp(depth_grid,
                                       depth[i],
                                       self.seismic_data[i])
            
        return depth_seismic, depth_grid
    
    def create_velocity_model(self, well_markers: Dict[str, List[Tuple[float, float]]],
                            interpolation: str = "linear"):
        """Cria modelo de velocidade a partir de marcadores de poço"""
        # Extrair coordenadas e velocidades dos marcadores
        points = []
        velocities = []
        for well, markers in well_markers.items():
            for x, y, z, v in markers:
                points.append([x, y, z])
                velocities.append(v)
                
        points = np.array(points)
        velocities = np.array(velocities)
        
        # Criar grid regular
        x = np.linspace(min(points[:,0]), max(points[:,0]), 100)
        y = np.linspace(min(points[:,1]), max(points[:,1]), 100)
        z = np.linspace(min(points[:,2]), max(points[:,2]), 100)
        
        X, Y, Z = np.meshgrid(x, y, z)
        
        # Interpolar velocidades
        self.velocity_model = griddata(points, velocities, (X, Y, Z),
                                     method=interpolation)
        
    def export_to_petrel(self, filename: str):
        """Exporta dados para formato Petrel"""
        # Implementar exportação para formato específico do Petrel
        pass
    
    def integrate_with_model(self, grid3d, properties: Dict):
        """Integra dados sísmicos com modelo geológico"""
        integrated_props = {}
        
        # Interpolar atributos sísmicos no grid do modelo
        for attr_name, attr_data in self.attributes.items():
            integrated_props[f"seismic_{attr_name}"] = griddata(
                (self.seismic_coords[:,0], self.seismic_coords[:,1], self.seismic_coords[:,2]),
                attr_data,
                (grid3d.cell_centers[:,0], grid3d.cell_centers[:,1], grid3d.cell_centers[:,2])
            )
            
        return integrated_props
