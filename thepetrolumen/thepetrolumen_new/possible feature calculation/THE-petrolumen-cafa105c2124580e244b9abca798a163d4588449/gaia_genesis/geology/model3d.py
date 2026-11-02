import numpy as np
import pyvista as pv
import lasio
from scipy.interpolate import griddata
import pandas as pd

class GeologicalModel3D:
    def __init__(self):
        """
        Inicializa o modelo geológico 3D.
        """
        self.grid = None
        self.properties = {}
        self.wells = {}
        self.surfaces = {}
        
    def create_grid(self, nx, ny, nz, dx, dy, dz):
        """
        Cria uma malha 3D regular.
        
        Args:
            nx, ny, nz (int): Número de células em cada direção
            dx, dy, dz (float): Tamanho das células em cada direção
        """
        x = np.arange(0, nx * dx, dx)
        y = np.arange(0, ny * dy, dy)
        z = np.arange(0, nz * dz, dz)
        
        self.grid = pv.RectilinearGrid(x, y, z)
        
    def add_well(self, well_name, x, y, md, properties=None):
        """
        Adiciona um poço ao modelo.
        
        Args:
            well_name (str): Nome do poço
            x, y (float): Coordenadas do poço
            md (array): Medidas de profundidade
            properties (dict): Propriedades do poço (logs)
        """
        self.wells[well_name] = {
            'x': x,
            'y': y,
            'md': md,
            'properties': properties or {}
        }
        
    def load_well_log(self, well_name, las_file):
        """
        Carrega dados de log de um arquivo LAS.
        
        Args:
            well_name (str): Nome do poço
            las_file (str): Caminho do arquivo LAS
        """
        las = lasio.read(las_file)
        df = las.df()
        
        # Converter profundidade para coordenadas x, y, z
        x = self.wells[well_name]['x']
        y = self.wells[well_name]['y']
        z = df.index.values
        
        # Adicionar propriedades
        for col in df.columns:
            self.wells[well_name]['properties'][col] = df[col].values
            
    def interpolate_property(self, property_name, method='linear'):
        """
        Interpola uma propriedade para toda a malha.
        
        Args:
            property_name (str): Nome da propriedade a ser interpolada
            method (str): Método de interpolação ('linear', 'cubic', 'nearest')
        """
        if not self.grid:
            raise ValueError("Malha não criada. Use create_grid primeiro.")
            
        # Coletar pontos de dados
        points = []
        values = []
        
        for well_name, well_data in self.wells.items():
            if property_name in well_data['properties']:
                x = np.full_like(well_data['md'], well_data['x'])
                y = np.full_like(well_data['md'], well_data['y'])
                z = well_data['md']
                v = well_data['properties'][property_name]
                
                points.extend(list(zip(x, y, z)))
                values.extend(v)
                
        if not points:
            raise ValueError(f"Propriedade {property_name} não encontrada em nenhum poço")
            
        points = np.array(points)
        values = np.array(values)
        
        # Criar pontos da malha
        x, y, z = self.grid.points.T
        
        # Interpolar
        interpolated = griddata(points, values, (x, y, z), method=method)
        
        # Adicionar ao modelo
        self.properties[property_name] = interpolated
        self.grid.cell_data[property_name] = interpolated
        
    def add_surface(self, name, x, y, z):
        """
        Adiciona uma superfície ao modelo.
        
        Args:
            name (str): Nome da superfície
            x, y, z (array): Coordenadas da superfície
        """
        points = np.column_stack((x, y, z))
        self.surfaces[name] = pv.PolyData(points)
        
    def visualize(self, property_name=None, show_wells=True, show_surfaces=True):
        """
        Visualiza o modelo 3D.
        
        Args:
            property_name (str, optional): Propriedade a ser visualizada
            show_wells (bool): Se deve mostrar os poços
            show_surfaces (bool): Se deve mostrar as superfícies
        """
        plotter = pv.Plotter()
        
        # Adicionar malha
        if property_name and property_name in self.properties:
            plotter.add_mesh(self.grid, scalars=property_name, cmap='viridis')
        else:
            plotter.add_mesh(self.grid, color='white', opacity=0.3)
            
        # Adicionar poços
        if show_wells:
            for well_name, well_data in self.wells.items():
                points = np.column_stack((
                    np.full_like(well_data['md'], well_data['x']),
                    np.full_like(well_data['md'], well_data['y']),
                    well_data['md']
                ))
                well = pv.PolyData(points)
                plotter.add_mesh(well, color='red', point_size=10)
                
        # Adicionar superfícies
        if show_surfaces:
            for name, surface in self.surfaces.items():
                plotter.add_mesh(surface, color='blue', opacity=0.5)
                
        plotter.show()
        
    def export_to_vtk(self, filename):
        """
        Exporta o modelo para arquivo VTK.
        
        Args:
            filename (str): Nome do arquivo de saída
        """
        if not self.grid:
            raise ValueError("Malha não criada. Use create_grid primeiro.")
            
        self.grid.save(filename)
        
    def calculate_statistics(self, property_name):
        """
        Calcula estatísticas de uma propriedade.
        
        Args:
            property_name (str): Nome da propriedade
            
        Returns:
            dict: Estatísticas calculadas
        """
        if property_name not in self.properties:
            raise ValueError(f"Propriedade {property_name} não encontrada")
            
        data = self.properties[property_name]
        return {
            'mean': np.mean(data),
            'std': np.std(data),
            'min': np.min(data),
            'max': np.max(data),
            'median': np.median(data)
        } 