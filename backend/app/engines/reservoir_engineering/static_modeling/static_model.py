import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import lasio
import segyio
import pyvista as pv
from scipy.interpolate import griddata

class StaticModel:
    """Classe para modelagem estática de reservatórios."""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.grid = None
        self.properties = {}
        self.well_data = {}
        self.structural_model = None
        self.seismic_data = None
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('StaticModel')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def import_well_data(self, las_files: List[str], well_names: List[str]):
        """
        Importa dados de poço de arquivos LAS.
        
        Args:
            las_files: Lista de arquivos LAS
            well_names: Lista de nomes dos poços
        """
        for las_file, well_name in zip(las_files, well_names):
            try:
                las = lasio.read(las_file)
                self.well_data[well_name] = {
                    'depth': las.index,
                    'gr': las['GR'],
                    'nphi': las['NPHI'],
                    'rhob': las['RHOB'],
                    'dt': las['DT']
                }
                self.logger.info(f"Dados do poço {well_name} importados")
            except Exception as e:
                self.logger.error(f"Erro ao importar {las_file}: {str(e)}")
                
    def import_seismic_data(self, segy_file: str):
        """
        Importa dados sísmicos.
        
        Args:
            segy_file: Arquivo SEG-Y
        """
        try:
            with segyio.open(segy_file) as f:
                self.seismic_data = f.iline[:]
                self.logger.info("Dados sísmicos importados")
        except Exception as e:
            self.logger.error(f"Erro ao importar dados sísmicos: {str(e)}")
            
    def create_grid(self,
                   nx: int,
                   ny: int,
                   nz: int,
                   dx: float,
                   dy: float,
                   dz: float):
        """
        Cria grade 3D.
        
        Args:
            nx, ny, nz: Número de células
            dx, dy, dz: Tamanho das células
        """
        self.grid = pv.UniformGrid()
        self.grid.dimensions = (nx, ny, nz)
        self.grid.cell_size = (dx, dy, dz)
        self.grid.origin = (0, 0, 0)
        
        self.logger.info(f"Grade criada: {nx}x{ny}x{nz}")
        
    def build_structural_model(self,
                             horizons: Dict[str, np.ndarray],
                             faults: Optional[List[Dict]] = None):
        """
        Constrói modelo estrutural.
        
        Args:
            horizons: Dicionário com superfícies
            faults: Lista de falhas (opcional)
        """
        try:
            # Cria modelo estrutural
            self.structural_model = pv.PolyData()
            
            # Adiciona horizontes
            for name, surface in horizons.items():
                self.structural_model.merge(pv.PolyData(surface))
                
            # Adiciona falhas
            if faults:
                for fault in faults:
                    self.structural_model.merge(pv.PolyData(fault['surface']))
                    
            self.logger.info("Modelo estrutural construído")
        except Exception as e:
            self.logger.error(f"Erro ao construir modelo estrutural: {str(e)}")
            
    def calculate_properties(self):
        """Calcula propriedades petrofísicas."""
        try:
            # Porosidade
            self.properties['porosity'] = self._calculate_porosity()
            
            # Permeabilidade
            self.properties['permeability'] = self._calculate_permeability()
            
            # Saturação de água
            self.properties['sw'] = self._calculate_water_saturation()
            
            self.logger.info("Propriedades calculadas")
        except Exception as e:
            self.logger.error(f"Erro ao calcular propriedades: {str(e)}")
            
    def _calculate_porosity(self) -> np.ndarray:
        """
        Calcula porosidade.
        
        Returns:
            Array de porosidade
        """
        if not self.grid:
            raise ValueError("Grade não criada")
            
        # Número de células
        n_cells = self.grid.dimensions[0] * self.grid.dimensions[1] * self.grid.dimensions[2]
        
        # Extrai coordenadas dos poços e valores de porosidade
        well_coords = []
        porosity_values = []
        
        for well_name, well in self.well_data.items():
            # Calcula porosidade a partir dos logs
            # Fórmula simples: NPHI
            if 'nphi' in well:
                depth = well['depth']
                porosity = well['nphi']
                
                # Converte profundidade para coordenadas 3D
                # Simplificação: assume poço vertical no centro da área
                x = self.grid.dimensions[0] / 2
                y = self.grid.dimensions[1] / 2
                
                for d, p in zip(depth, porosity):
                    # Normaliza profundidade para índice z
                    z = d / self.grid.cell_size[2]
                    if 0 <= z < self.grid.dimensions[2]:
                        well_coords.append([x, y, z])
                        porosity_values.append(p)
        
        # Se não houver dados suficientes, cria modelo sintético
        if len(well_coords) < 10:
            self.logger.warning("Dados insuficientes, gerando modelo sintético")
            
            # Modelo de porosidade sintético com tendência de profundidade
            z_grid = np.linspace(0, 1, self.grid.dimensions[2])
            phi_trend = 0.25 - 0.15 * z_grid  # Decresce com profundidade
            
            # Adiciona variação lateral
            porosity = np.zeros(n_cells)
            for i in range(self.grid.dimensions[0]):
                for j in range(self.grid.dimensions[1]):
                    for k in range(self.grid.dimensions[2]):
                        idx = i + j*self.grid.dimensions[0] + k*self.grid.dimensions[0]*self.grid.dimensions[1]
                        porosity[idx] = phi_trend[k] + 0.03 * np.random.randn()
            
            # Limita valores entre 0.05 e 0.35
            porosity = np.clip(porosity, 0.05, 0.35)
            
            return porosity
        
        # Interpola dados para toda a grade
        # Obtém pontos da grade
        x = np.linspace(0, self.grid.dimensions[0]-1, self.grid.dimensions[0])
        y = np.linspace(0, self.grid.dimensions[1]-1, self.grid.dimensions[1])
        z = np.linspace(0, self.grid.dimensions[2]-1, self.grid.dimensions[2])
        
        grid_x, grid_y, grid_z = np.meshgrid(x, y, z)
        points = np.vstack((grid_x.flatten(), grid_y.flatten(), grid_z.flatten())).T
        
        # Interpola valores de porosidade
        porosity = griddata(np.array(well_coords), np.array(porosity_values), points, method='linear', fill_value=0.2)
        
        # Limita valores entre 0.05 e 0.35
        porosity = np.clip(porosity, 0.05, 0.35)
        
        return porosity
        
    def _calculate_permeability(self) -> np.ndarray:
        """
        Calcula permeabilidade.
        
        Returns:
            Array de permeabilidade
        """
        if not self.grid or 'porosity' not in self.properties:
            raise ValueError("Porosidade não calculada")
            
        # Calcula permeabilidade a partir da porosidade
        # Relação empírica: k = a * phi^b
        a = 0.1
        b = 3.5
        
        porosity = self.properties['porosity']
        permeability = a * (porosity * 100) ** b  # mD
        
        # Limita valores entre 0.1 e 1000 mD
        permeability = np.clip(permeability, 0.1, 1000)
        
        return permeability
        
    def _calculate_water_saturation(self) -> np.ndarray:
        """
        Calcula saturação de água.
        
        Returns:
            Array de saturação de água
        """
        if not self.grid:
            raise ValueError("Grade não criada")
            
        # Número de células
        n_cells = self.grid.dimensions[0] * self.grid.dimensions[1] * self.grid.dimensions[2]
        
        # Modelo simples baseado em profundidade (contato água-óleo)
        # Define profundidade de contato água-óleo (75% da altura total)
        contact_depth = int(0.75 * self.grid.dimensions[2])
        
        # Inicializa saturação
        sw = np.zeros(n_cells)
        
        # Preenche saturação
        for i in range(self.grid.dimensions[0]):
            for j in range(self.grid.dimensions[1]):
                for k in range(self.grid.dimensions[2]):
                    idx = i + j*self.grid.dimensions[0] + k*self.grid.dimensions[0]*self.grid.dimensions[1]
                    
                    if k < contact_depth:
                        # Acima do contato
                        sw[idx] = 0.2 + 0.05 * np.random.rand()
                    else:
                        # Abaixo do contato, transição
                        depth_ratio = (k - contact_depth) / (self.grid.dimensions[2] - contact_depth)
                        sw[idx] = 0.2 + 0.7 * depth_ratio + 0.05 * np.random.rand()
        
        # Limita valores entre 0.2 e 1.0
        sw = np.clip(sw, 0.2, 1.0)
        
        return sw
        
    def populate_properties(self):
        """Popula propriedades na grade."""
        if not self.grid:
            raise ValueError("Grade não criada")
            
        try:
            for prop_name, values in self.properties.items():
                self.grid.cell_data[prop_name] = values
                
            self.logger.info("Propriedades populadas na grade")
        except Exception as e:
            self.logger.error(f"Erro ao popular propriedades: {str(e)}")
            
    def visualize_model(self,
                       property_name: Optional[str] = None,
                       save_path: Optional[str] = None):
        """
        Visualiza modelo.
        
        Args:
            property_name: Nome da propriedade para visualizar
            save_path: Caminho para salvar figura
        """
        try:
            plotter = pv.Plotter()
            
            if property_name:
                plotter.add_mesh(self.grid, scalars=property_name)
            else:
                plotter.add_mesh(self.grid)
                
            if save_path:
                plotter.screenshot(save_path)
            else:
                plotter.show()
                
        except Exception as e:
            self.logger.error(f"Erro ao visualizar modelo: {str(e)}")
            
    def export_model(self, path: str):
        """
        Exporta modelo.
        
        Args:
            path: Caminho para salvar
        """
        try:
            self.grid.save(path)
            self.logger.info(f"Modelo exportado para {path}")
        except Exception as e:
            self.logger.error(f"Erro ao exportar modelo: {str(e)}") 