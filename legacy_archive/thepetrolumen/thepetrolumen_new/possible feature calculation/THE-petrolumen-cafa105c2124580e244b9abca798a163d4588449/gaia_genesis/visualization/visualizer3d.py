import numpy as np
import pyvista as pv
from typing import Dict, List, Optional, Tuple
import matplotlib.cm as cm
from pathlib import Path
import pandas as pd

class Visualizer3D:
    """Sistema de visualização 3D avançado estilo Petrel para reservatórios"""
    
    def __init__(self, theme: str = "document"):
        """
        Inicializa o visualizador 3D
        
        Args:
            theme: Tema de visualização ('document', 'dark', ou 'paraview')
        """
        # Configurar plotter com tema específico
        self.plotter = pv.Plotter()
        if theme == "dark":
            self.plotter.set_background('black')
            self.plotter.set_background_color('black')
        elif theme == "document":
            self.plotter.set_background('white')
            self.plotter.set_background_color('white')
        elif theme == "paraview":
            self.plotter.set_background('grey')
            self.plotter.set_background_color('grey')
            
        self.grid = None
        self.scalar_data = {}
        self.wells = []
        self.faults = []
        self.horizons = []
        self.cross_sections = []
        self.well_logs = {}
        
    def create_grid(self, nx: int, ny: int, nz: int,
                   dx: float, dy: float, dz: float,
                   origin: Tuple[float, float, float] = (0, 0, 0)):
        """Cria grid 3D estruturado"""
        self.grid = pv.UniformGrid(
            dimensions=(nx + 1, ny + 1, nz + 1),
            spacing=(dx, dy, dz),
            origin=origin
        )
    
    def add_property(self, name: str, values: np.ndarray):
        """Adiciona propriedade ao grid"""
        if values.size == np.prod(np.array(self.grid.dimensions) - 1):
            self.grid.cell_data[name] = values.flatten()
            self.scalar_data[name] = values
    
    def add_well(self, name: str, trajectory: np.ndarray,
                 perforation_intervals: Optional[List[Tuple[float, float]]] = None):
        """Adiciona poço com trajetória e intervalos perfurados"""
        well = {
            "name": name,
            "trajectory": trajectory,
            "perforations": perforation_intervals or []
        }
        self.wells.append(well)
        
        # Criar geometria do poço
        well_line = pv.Line(trajectory[0], trajectory[-1])
        self.plotter.add_mesh(well_line, color='black', line_width=3)
        
        # Adicionar perfurações
        if perforation_intervals:
            for start, end in perforation_intervals:
                perf = pv.Line(start, end)
                self.plotter.add_mesh(perf, color='red', line_width=5)
    
    def plot_property(self, property_name: str,
                     cmap: str = 'viridis',
                     clim: Optional[Tuple[float, float]] = None,
                     opacity: float = 1.0):
        """Plota propriedade no grid 3D"""
        if property_name in self.scalar_data:
            self.plotter.add_mesh(
                self.grid,
                scalars=self.scalar_data[property_name].flatten(),
                cmap=cmap,
                clim=clim,
                opacity=opacity,
                show_edges=True
            )
    
    def create_slice(self, normal: str = 'z',
                    position: float = 0.0):
        """Cria slice do modelo"""
        slc = self.grid.slice(normal=normal, origin=[0, 0, position])
        self.plotter.add_mesh(slc, show_edges=True)
    
    def create_threshold(self, property_name: str,
                        threshold_range: Tuple[float, float],
                        color: str = 'red'):
        """Cria visualização de threshold para uma propriedade"""
        if property_name in self.scalar_data:
            thresh = self.grid.threshold(
                threshold_range,
                scalars=self.scalar_data[property_name].flatten()
            )
            self.plotter.add_mesh(thresh, color=color, opacity=0.5)
    
    def add_streamlines(self, velocity_field: Dict[str, np.ndarray],
                       n_points: int = 100):
        """Adiciona linhas de fluxo"""
        # Combinar componentes de velocidade
        vectors = np.column_stack([
            velocity_field['vx'].flatten(),
            velocity_field['vy'].flatten(),
            velocity_field['vz'].flatten()
        ])
        
        self.grid.cell_data['vectors'] = vectors
        
        # Criar pontos de seed para streamlines
        seeds = self.grid.points[::n_points]
        
        streamlines = self.grid.streamlines(
            vectors='vectors',
            integration_direction='both',
            initial_step_length=0.1,
            max_steps=1000,
            start_position=seeds
        )
        
        self.plotter.add_mesh(streamlines, line_width=1, color='blue')
    
    def add_time_series(self, property_name: str,
                       time_data: List[np.ndarray]):
        """Adiciona série temporal de uma propriedade"""
        self.plotter.open_movie("animation.mp4")
        
        for time_step, data in enumerate(time_data):
            self.plotter.clear()
            self.add_property(f"{property_name}_t{time_step}", data)
            self.plot_property(f"{property_name}_t{time_step}")
            self.plotter.write_frame()
        
        self.plotter.close()
    
    def add_legend(self, title: str):
        """Adiciona legenda ao plot"""
        self.plotter.add_scalar_bar(title=title)
    
    def set_camera_position(self, position: Tuple[float, float, float]):
        """Define posição da câmera"""
        self.plotter.camera_position = position
    
    def show(self, interactive: bool = True):
        """Mostra visualização"""
        self.plotter.show(interactive=interactive)
    
    def save_screenshot(self, filename: str):
        """Salva screenshot da visualização"""
        self.plotter.screenshot(filename)
    
    def close(self):
        """Fecha visualizador"""
        self.plotter.close()
    
    def add_fault(self, points: np.ndarray, name: str = None):
        """Adiciona falha ao modelo"""
        fault_surface = pv.PolyData(points)
        fault_surface = fault_surface.delaunay_2d()
        
        self.faults.append({
            "name": name,
            "surface": fault_surface
        })
        
        self.plotter.add_mesh(
            fault_surface,
            style='surface',
            color='red',
            opacity=0.5,
            name=f"fault_{name}"
        )
    
    def add_horizon(self, points: np.ndarray, property_values: Optional[np.ndarray] = None,
                   name: str = None, cmap: str = 'viridis'):
        """Adiciona horizonte estratigráfico"""
        horizon_surface = pv.PolyData(points)
        horizon_surface = horizon_surface.delaunay_2d()
        
        if property_values is not None:
            horizon_surface.point_data["values"] = property_values
        
        self.horizons.append({
            "name": name,
            "surface": horizon_surface
        })
        
        self.plotter.add_mesh(
            horizon_surface,
            scalars="values" if property_values is not None else None,
            cmap=cmap,
            opacity=0.7,
            name=f"horizon_{name}"
        )
    
    def add_well_log(self, well_name: str, trajectory: np.ndarray,
                    log_data: Dict[str, np.ndarray]):
        """Adiciona perfil de poço com dados de log"""
        self.well_logs[well_name] = {
            "trajectory": trajectory,
            "logs": log_data
        }
        
        # Criar cilindro ao longo da trajetória
        well_tube = pv.Line(trajectory[0], trajectory[-1])
        tube = well_tube.tube(radius=1.0)
        
        # Adicionar dados de log como cores
        for log_name, values in log_data.items():
            tube.point_data[log_name] = np.interp(
                np.linspace(0, 1, tube.n_points),
                np.linspace(0, 1, len(values)),
                values
            )
        
        self.plotter.add_mesh(
            tube,
            scalars=list(log_data.keys())[0],
            name=f"well_log_{well_name}"
        )
    
    def create_cross_section(self, start_point: np.ndarray,
                           end_point: np.ndarray,
                           name: str = None):
        """Cria seção transversal do modelo"""
        if self.grid is None:
            raise ValueError("Grid não inicializado")
            
        # Criar plano de corte
        normal = np.cross(end_point - start_point, np.array([0, 0, 1]))
        normal = normal / np.linalg.norm(normal)
        
        # Extrair seção
        slice_data = self.grid.slice(normal=normal, origin=start_point)
        
        self.cross_sections.append({
            "name": name,
            "data": slice_data
        })
        
        # Adicionar à visualização
        self.plotter.add_mesh(
            slice_data,
            name=f"cross_section_{name}"
        )
    
    def add_property_filter(self, property_name: str,
                          min_value: float,
                          max_value: float):
        """Adiciona filtro de propriedade (similar ao filtro do Petrel)"""
        if property_name not in self.scalar_data:
            raise ValueError(f"Propriedade {property_name} não encontrada")
            
        threshold = self.grid.threshold(
            [min_value, max_value],
            scalars=property_name
        )
        
        self.plotter.add_mesh(
            threshold,
            scalars=property_name,
            name=f"filter_{property_name}"
        )
    
    def create_well_fence(self, well_name: str, distance: float = 50.0):
        """Cria cerca (fence) ao redor do poço para visualização"""
        if well_name not in [w["name"] for w in self.wells]:
            raise ValueError(f"Poço {well_name} não encontrado")
            
        well = next(w for w in self.wells if w["name"] == well_name)
        trajectory = well["trajectory"]
        
        # Criar planos perpendiculares à trajetória
        for i in range(len(trajectory) - 1):
            direction = trajectory[i+1] - trajectory[i]
            normal = np.cross(direction, np.array([0, 0, 1]))
            normal = normal / np.linalg.norm(normal)
            
            # Criar planos
            center = (trajectory[i] + trajectory[i+1]) / 2
            fence = self.grid.slice(normal=normal, origin=center)
            
            self.plotter.add_mesh(
                fence,
                opacity=0.7,
                name=f"fence_{well_name}_{i}"
            )
    
    def add_streamlines(self, velocity_field: Dict[str, np.ndarray],
                       density: int = 10):
        """Adiciona linhas de fluxo (similar ao Petrel)"""
        vectors = np.column_stack([
            velocity_field['vx'].flatten(),
            velocity_field['vy'].flatten(),
            velocity_field['vz'].flatten()
        ])
        
        self.grid.cell_data['vectors'] = vectors
        
        # Criar pontos de seed
        bounds = self.grid.bounds
        x = np.linspace(bounds[0], bounds[1], density)
        y = np.linspace(bounds[2], bounds[3], density)
        z = np.linspace(bounds[4], bounds[5], density)
        
        seeds = pv.StructuredGrid(x, y, z).points
        
        # Calcular streamlines
        streams = self.grid.streamlines(
            vectors='vectors',
            integration_direction='both',
            initial_step_length=0.1,
            max_steps=1000,
            start_position=seeds
        )
        
        self.plotter.add_mesh(streams, line_width=1, color='blue')
    
    def create_volume_rendering(self, property_name: str,
                              opacity_mapping: Optional[Dict[float, float]] = None):
        """Cria renderização volumétrica (similar ao Petrel)"""
        if property_name not in self.scalar_data:
            raise ValueError(f"Propriedade {property_name} não encontrada")
        
        # Configurar mapeamento de opacidade padrão se não fornecido
        if opacity_mapping is None:
            values = self.scalar_data[property_name].flatten()
            vmin, vmax = np.min(values), np.max(values)
            opacity_mapping = {
                vmin: 0.0,
                (vmin + vmax) / 2: 0.5,
                vmax: 1.0
            }
        
        # Criar função de transferência de opacidade
        opacity = [opacity_mapping[val] for val in sorted(opacity_mapping.keys())]
        
        self.plotter.add_volume(
            self.grid,
            scalars=property_name,
            opacity=opacity,
            name=f"volume_{property_name}"
        )
    
    def export_to_vtk(self, filename: str):
        """Exporta modelo para formato VTK"""
        if self.grid is not None:
            self.grid.save(filename)
    
    def create_property_histogram(self, property_name: str):
        """Cria histograma de propriedade"""
        if property_name not in self.scalar_data:
            raise ValueError(f"Propriedade {property_name} não encontrada")
            
        values = self.scalar_data[property_name].flatten()
        hist = np.histogram(values, bins=50)
        
        # Criar visualização do histograma
        bar_mesh = pv.Chart2D()
        bar_mesh.bar(hist[1][:-1], hist[0])
        
        self.plotter.add_chart(bar_mesh)
    
    def add_time_series_animation(self, property_name: str,
                                time_data: List[np.ndarray],
                                time_steps: List[float]):
        """Cria animação de série temporal"""
        self.plotter.open_movie("animation.mp4")
        
        for i, (data, time) in enumerate(zip(time_data, time_steps)):
            self.plotter.clear()
            self.add_property(f"{property_name}_t{i}", data)
            self.plot_property(f"{property_name}_t{i}")
            text = f"Time: {time:.2f} days"
            self.plotter.add_text(text, position='upper_left')
            self.plotter.write_frame()
            
        self.plotter.close()
