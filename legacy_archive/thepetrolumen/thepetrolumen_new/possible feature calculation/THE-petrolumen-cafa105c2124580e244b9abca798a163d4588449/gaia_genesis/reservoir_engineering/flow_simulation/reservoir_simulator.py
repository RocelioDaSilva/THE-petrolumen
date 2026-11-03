import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from typing import Dict, List, Optional, Tuple, Union
from scipy.interpolate import RegularGridInterpolator
from pathlib import Path
import json
try:
    import pyvista as pv
    PYVISTA_AVAILABLE = True
except ImportError:
    PYVISTA_AVAILABLE = False

class ReservoirSimulator:
    """
    Classe para modelagem, simulação e análise de reservatórios de petróleo.
    Implementa funcionalidades similares ao Navigator (Rock Flow Dynamics).
    """
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.grid = None
        self.properties = {}
        self.wells = {}
        self.fluids = {}
        self.simulation_results = {}
        self.faults = []
        self.connections = {}
        self.thermal_properties = {}
        self.compositional_data = {}
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('ReservoirSimulator')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    # ===============================
    # 1. Gerenciamento de Malhas
    # ===============================
    
    def create_structured_grid(self, nx: int, ny: int, nz: int, dx: float = 1.0, dy: float = 1.0, dz: float = 1.0):
        """
        Cria malha cartesiana regular.
        
        Args:
            nx: Número de células na direção X
            ny: Número de células na direção Y
            nz: Número de células na direção Z
            dx: Tamanho das células na direção X
            dy: Tamanho das células na direção Y
            dz: Tamanho das células na direção Z
        """
        self.grid = {
            'type': 'cartesian',
            'dims': (nx, ny, nz),
            'spacing': (dx, dy, dz),
            'cells': np.zeros((nx, ny, nz))
        }
        
        # Inicializa arrays de coordenadas para fácil plotagem
        x = np.linspace(0, nx * dx, nx + 1)
        y = np.linspace(0, ny * dy, ny + 1)
        z = np.linspace(0, nz * dz, nz + 1)
        
        self.grid['coords'] = {
            'x': x,
            'y': y,
            'z': z
        }
        
        self.logger.info(f"Malha estruturada criada: {nx}x{ny}x{nz}")
    
    def create_corner_point_grid(self, coordinates: Dict[str, np.ndarray]):
        """
        Cria malha corner-point para modelagem de estruturas complexas.
        
        Args:
            coordinates: Dicionário com arrays de coordenadas X, Y, Z
        """
        if not all(key in coordinates for key in ['x', 'y', 'z']):
            raise ValueError("Coordenadas devem conter arrays 'x', 'y' e 'z'")
            
        x, y, z = coordinates['x'], coordinates['y'], coordinates['z']
        
        # Verifica dimensões compatíveis
        nx, ny, nz = x.shape[0]-1, y.shape[0]-1, z.shape[0]-1
        
        self.grid = {
            'type': 'corner_point',
            'dims': (nx, ny, nz),
            'coords': coordinates,
            'cells': np.zeros((nx, ny, nz))
        }
        
        self.logger.info(f"Malha corner-point criada: {nx}x{ny}x{nz}")
    
    def import_model(self, filename: str, format_type: str = 'eclipse'):
        """
        Importa modelo de reservatório de arquivos externos.
        
        Args:
            filename: Caminho para o arquivo
            format_type: Formato do arquivo ('eclipse', 'vtk', 'csv')
        """
        file_path = Path(filename)
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo {filename} não encontrado")
            
        self.logger.info(f"Importando modelo de {filename} (formato: {format_type})")
        
        if format_type.lower() == 'eclipse':
            # Implementação simplificada para arquivos Eclipse (.GRDECL)
            self.logger.info("Importação de arquivos Eclipse não implementada completamente")
            # Aqui seria implementado o parser real para formatos Eclipse
            
        elif format_type.lower() == 'vtk':
            if not PYVISTA_AVAILABLE:
                raise ImportError("PyVista é necessário para importar arquivos VTK")
                
            grid = pv.read(filename)
            nx, ny, nz = grid.dimensions
            
            self.grid = {
                'type': 'vtk',
                'dims': (nx-1, ny-1, nz-1),
                'vtk_grid': grid
            }
            
        elif format_type.lower() == 'csv':
            # Implementação para arquivos CSV com propriedades
            pass
        
        else:
            raise ValueError(f"Formato {format_type} não suportado")
    
    def export_model(self, filename: str, format_type: str = 'eclipse'):
        """
        Exporta modelo de reservatório para arquivos externos.
        
        Args:
            filename: Caminho para o arquivo
            format_type: Formato do arquivo ('eclipse', 'vtk', 'json')
        """
        self.logger.info(f"Exportando modelo para {filename} (formato: {format_type})")
        
        if format_type.lower() == 'eclipse':
            # Implementação simplificada para arquivos Eclipse
            pass
            
        elif format_type.lower() == 'vtk':
            if not PYVISTA_AVAILABLE:
                raise ImportError("PyVista é necessário para exportar arquivos VTK")
                
            # Cria grid VTK
            nx, ny, nz = self.grid['dims']
            grid = pv.UniformGrid()
            grid.dimensions = [nx+1, ny+1, nz+1]
            
            # Adiciona propriedades
            for prop_name, prop_data in self.properties.items():
                grid.cell_data[prop_name] = prop_data.flatten(order='F')
                
            # Salva arquivo
            grid.save(filename)
            
        elif format_type.lower() == 'json':
            # Cria dicionário para exportação
            export_data = {
                'grid': {
                    'type': self.grid['type'],
                    'dims': self.grid['dims'],
                    'spacing': self.grid.get('spacing', [1, 1, 1])
                },
                'properties': {
                    # Converte arrays numpy para listas
                    name: prop.tolist() for name, prop in self.properties.items()
                },
                'wells': self.wells
            }
            
            # Salva como JSON
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
    
    # ===============================
    # 2. Propriedades Petrofísicas
    # ===============================
    
    def add_property(self, name: str, data: np.ndarray):
        """
        Adiciona propriedade petrofísica ao modelo.
        
        Args:
            name: Nome da propriedade
            data: Array com valores da propriedade
        """
        if self.grid is None:
            raise ValueError("Crie uma malha antes de adicionar propriedades")
            
        expected_shape = self.grid['dims']
        if data.shape != expected_shape:
            raise ValueError(f"Dimensões da propriedade {data.shape} incompatíveis com a malha {expected_shape}")
            
        self.properties[name] = data
        self.logger.info(f"Propriedade '{name}' adicionada com sucesso")
    
    def calculate_derived_property(self, name: str, formula: str, overwrite: bool = False):
        """
        Calcula propriedade derivada a partir de fórmula.
        
        Args:
            name: Nome da nova propriedade
            formula: Fórmula em termos de outras propriedades
            overwrite: Se deve sobrescrever propriedade existente
        """
        if name in self.properties and not overwrite:
            raise ValueError(f"Propriedade '{name}' já existe. Use overwrite=True para sobrescrever.")
            
        # Ambiente de execução seguro com as propriedades disponíveis
        env = {prop_name: prop_data for prop_name, prop_data in self.properties.items()}
        env.update({'np': np})
        
        try:
            result = eval(formula, {'__builtins__': {}}, env)
            self.properties[name] = result
            self.logger.info(f"Propriedade derivada '{name}' calculada com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao calcular propriedade derivada: {str(e)}")
            raise
    
    def add_fault(self, points: List[Tuple[float, float, float]], name: str = ""):
        """
        Define uma falha geológica no modelo.
        
        Args:
            points: Lista de pontos definindo o plano de falha
            name: Nome da falha
        """
        if len(points) < 3:
            raise ValueError("Uma falha requer pelo menos 3 pontos para definir um plano")
            
        self.faults.append({
            'points': points,
            'name': name
        })
        
        self.logger.info(f"Falha '{name}' adicionada com {len(points)} pontos")
    
    # ===============================
    # 3. Modelagem de Poços
    # ===============================
    
    def add_well(self, 
                name: str, 
                trajectory: List[Tuple[float, float, float]], 
                completions: Optional[List[Dict]] = None,
                schedule: Optional[List[Dict]] = None):
        """
        Adiciona poço com trajetória, completações e cronograma.
        
        Args:
            name: Nome do poço
            trajectory: Lista de pontos [(x1,y1,z1), (x2,y2,z2), ...] definindo a trajetória
            completions: Lista de dicionários definindo completações
            schedule: Lista de dicionários definindo o cronograma de produção/injeção
        """
        if not trajectory:
            raise ValueError("Trajetória deve conter pelo menos um ponto")
            
        # Conversão para array numpy
        trajectory_array = np.array(trajectory)
        
        # Inicializa completações se não fornecido
        if completions is None:
            completions = []
            
        # Inicializa cronograma se não fornecido
        if schedule is None:
            schedule = []
            
        # Adiciona o poço
        self.wells[name] = {
            'trajectory': trajectory_array,
            'completions': completions,
            'schedule': schedule,
            'type': 'producer'  # Padrão é produtor
        }
        
        self.logger.info(f"Poço '{name}' adicionado com {len(trajectory)} pontos")
    
    def set_well_schedule(self, 
                         well_name: str, 
                         schedule: List[Dict]):
        """
        Define cronograma de produção/injeção para um poço.
        
        Args:
            well_name: Nome do poço
            schedule: Lista de dicionários com cronograma
                Ex: [{'time': 0, 'control': 'rate', 'value': 1000, 'type': 'oil'}]
        """
        if well_name not in self.wells:
            raise ValueError(f"Poço '{well_name}' não existe")
            
        self.wells[well_name]['schedule'] = schedule
        self.logger.info(f"Cronograma atualizado para poço '{well_name}'")
    
    def set_well_completions(self, 
                           well_name: str, 
                           completions: List[Dict]):
        """
        Define completações para um poço.
        
        Args:
            well_name: Nome do poço
            completions: Lista de dicionários com completações
                Ex: [{'i': 5, 'j': 5, 'k': 3, 'diameter': 0.1, 'skin': 0}]
        """
        if well_name not in self.wells:
            raise ValueError(f"Poço '{well_name}' não existe")
            
        self.wells[well_name]['completions'] = completions
        self.logger.info(f"Completações atualizadas para poço '{well_name}'")
    
    def convert_well_type(self, 
                        well_name: str, 
                        well_type: str):
        """
        Converte tipo de poço (produtor/injetor).
        
        Args:
            well_name: Nome do poço
            well_type: Tipo do poço ('producer' ou 'injector')
        """
        if well_name not in self.wells:
            raise ValueError(f"Poço '{well_name}' não existe")
            
        valid_types = ['producer', 'injector']
        if well_type not in valid_types:
            raise ValueError(f"Tipo de poço inválido. Use {valid_types}")
            
        self.wells[well_name]['type'] = well_type
        self.logger.info(f"Poço '{well_name}' convertido para {well_type}")
    
    def calculate_well_indices(self, 
                             well_name: str) -> np.ndarray:
        """
        Calcula índices de poço para conexão com a malha.
        
        Args:
            well_name: Nome do poço
            
        Returns:
            Array com índices de poço
        """
        if well_name not in self.wells:
            raise ValueError(f"Poço '{well_name}' não existe")
            
        # Implementação simplificada para cálculo de índices
        # Em um simulador real, isto envolveria:
        # - Raio do poço
        # - Permeabilidade local
        # - Skin factor
        # - Geometria da célula
        
        return np.ones(len(self.wells[well_name]['completions']))
    
    # ===============================
    # 4. Simulação de Reservatórios
    # ===============================
    
    def setup_fluid_model(self, 
                        model_type: str, 
                        fluid_props: Dict):
        """
        Configura modelo de fluido para simulação.
        
        Args:
            model_type: Tipo de modelo ('black_oil', 'compositional', 'thermal')
            fluid_props: Dicionário com propriedades do fluido
        """
        valid_models = ['black_oil', 'compositional', 'thermal']
        if model_type not in valid_models:
            raise ValueError(f"Tipo de modelo inválido. Use {valid_models}")
            
        self.fluids = {
            'model_type': model_type,
            'properties': fluid_props
        }
        
        self.logger.info(f"Modelo de fluido '{model_type}' configurado")
    
    def setup_thermal_model(self, 
                          thermal_props: Dict):
        """
        Configura modelo térmico para simulação.
        
        Args:
            thermal_props: Dicionário com propriedades térmicas
        """
        self.thermal_properties = thermal_props
        self.logger.info("Modelo térmico configurado")
    
    def setup_compositional_model(self, 
                                components: List[Dict]):
        """
        Configura modelo composicional para simulação.
        
        Args:
            components: Lista de dicionários com propriedades dos componentes
        """
        self.compositional_data = {
            'components': components
        }
        
        self.logger.info(f"Modelo composicional configurado com {len(components)} componentes")
    
    def run_simulation(self, 
                     end_time: float, 
                     time_step: float,
                     output_interval: Optional[float] = None):
        """
        Executa simulação de reservatório.
        
        Args:
            end_time: Tempo final da simulação
            time_step: Passo de tempo
            output_interval: Intervalo de saída (se None, usa time_step)
        """
        if self.grid is None:
            raise ValueError("Malha não definida")
            
        if not self.properties:
            raise ValueError("Nenhuma propriedade definida")
            
        if not self.wells:
            self.logger.warning("Nenhum poço definido")
        
        # Usa time_step como output_interval se não especificado
        if output_interval is None:
            output_interval = time_step
            
        # Inicializa resultados
        times = np.arange(0, end_time + time_step, output_interval)
        num_steps = len(times)
        
        self.logger.info(f"Iniciando simulação com {num_steps} passos")
        
        # Inicializa resultados para cada poço
        results = {}
        for well_name, well_data in self.wells.items():
            # Simplificação: gera curvas de produção sintéticas
            # Em um simulador real, estes valores seriam calculados pela solução
            # do sistema de equações diferenciais do modelo
            
            if well_data['type'] == 'producer':
                # Simulação simplificada para poço produtor
                decay_factor = np.exp(-0.1 * times / 365)  # Decaimento exponencial
                
                # Adiciona um pouco de ruído para parecer mais realista
                noise = np.random.normal(1.0, 0.05, num_steps)
                
                # Taxas de produção iniciais
                initial_oil = 1000.0  # bbl/d
                initial_gas = 2000.0  # mscf/d
                initial_water = 200.0  # bbl/d
                
                oil_rate = initial_oil * decay_factor * noise
                gas_rate = initial_gas * decay_factor * noise * 1.1  # GOR aumentando levemente
                water_rate = initial_water * (2 - decay_factor) * noise  # Água aumentando com o tempo
                bhp = 2000.0 - 500.0 * (1 - decay_factor)  # Pressão caindo
                
            else:  # injector
                # Simulação simplificada para poço injetor
                water_rate = np.ones(num_steps) * 1500.0  # bbl/d constante
                oil_rate = np.zeros(num_steps)
                gas_rate = np.zeros(num_steps)
                bhp = 3000.0 + 1000.0 * (1 - np.exp(-0.2 * times / 365))  # Pressão aumentando
            
            results[well_name] = {
                'time': times,
                'oil_rate': oil_rate,
                'gas_rate': gas_rate,
                'water_rate': water_rate,
                'bhp': bhp
            }
            
        # Armazena resultados
        self.simulation_results = results
        
        self.logger.info("Simulação concluída com sucesso")
    
    # ===============================
    # 5. Visualização e Análise
    # ===============================
    
    def plot_property_slice(self, 
                          property_name: str, 
                          layer: Optional[int] = None, 
                          orientation: str = 'z',
                          ax: Optional[plt.Axes] = None,
                          cmap: str = 'jet',
                          save_path: Optional[str] = None) -> plt.Figure:
        """
        Visualiza fatia 2D de uma propriedade.
        
        Args:
            property_name: Nome da propriedade
            layer: Índice da camada (se None, usa camada central)
            orientation: Orientação ('x', 'y' ou 'z')
            ax: Eixo matplotlib para plotagem
            cmap: Mapa de cores
            save_path: Caminho para salvar figura
            
        Returns:
            Figura matplotlib
        """
        if property_name not in self.properties:
            raise ValueError(f"Propriedade '{property_name}' não encontrada")
            
        data = self.properties[property_name]
        nx, ny, nz = data.shape
        
        # Define camada padrão se não especificada
        if layer is None:
            if orientation == 'z':
                layer = nz // 2
            elif orientation == 'y':
                layer = ny // 2
            else:  # x
                layer = nx // 2
        
        # Extrai fatia na orientação correta
        if orientation == 'z':
            if layer >= nz:
                raise ValueError(f"Camada {layer} inválida para dimensão z ({nz})")
            slice_data = data[:, :, layer]
            extent = [0, nx, 0, ny]
            xlabel, ylabel = 'X', 'Y'
        elif orientation == 'y':
            if layer >= ny:
                raise ValueError(f"Camada {layer} inválida para dimensão y ({ny})")
            slice_data = data[:, layer, :]
            extent = [0, nx, 0, nz]
            xlabel, ylabel = 'X', 'Z'
        else:  # x
            if layer >= nx:
                raise ValueError(f"Camada {layer} inválida para dimensão x ({nx})")
            slice_data = data[layer, :, :]
            extent = [0, ny, 0, nz]
            xlabel, ylabel = 'Y', 'Z'
        
        # Cria figura se não fornecida
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 8))
        else:
            fig = ax.figure
        
        # Plota dados
        im = ax.imshow(slice_data.T, origin='lower', extent=extent, cmap=cmap)
        plt.colorbar(im, ax=ax, label=property_name)
        
        # Adiciona poços na visualização
        for well_name, well_data in self.wells.items():
            traj = well_data['trajectory']
            
            # Projeta trajetória no plano correto
            if orientation == 'z':
                ax.plot(traj[:, 0], traj[:, 1], 'r-', linewidth=2, label=well_name)
                # Marca perfurações na camada
                completions = well_data.get('completions', [])
                for comp in completions:
                    if comp.get('k') == layer:
                        ax.plot(comp.get('i'), comp.get('j'), 'ro', markersize=8)
            elif orientation == 'y':
                ax.plot(traj[:, 0], traj[:, 2], 'r-', linewidth=2, label=well_name)
            else:  # x
                ax.plot(traj[:, 1], traj[:, 2], 'r-', linewidth=2, label=well_name)
        
        # Adiciona título e labels
        ax.set_title(f"{property_name} - Camada {layer} ({orientation.upper()})")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        # Adiciona legenda se houver poços
        if self.wells:
            ax.legend()
        
        # Salva figura se caminho fornecido
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def plot_3d_model(self, 
                     property_name: Optional[str] = None,
                     opacity: float = 0.7,
                     show_wells: bool = True,
                     save_path: Optional[str] = None) -> None:
        """
        Visualização 3D interativa do modelo.
        
        Args:
            property_name: Nome da propriedade para colorir o modelo
            opacity: Opacidade do modelo (0-1)
            show_wells: Se deve mostrar os poços
            save_path: Caminho para salvar captura de tela
        """
        if not PYVISTA_AVAILABLE:
            raise ImportError("PyVista é necessário para visualização 3D")
            
        if self.grid is None:
            raise ValueError("Malha não definida")
            
        # Cria grid PyVista
        grid = pv.UniformGrid()
        nx, ny, nz = self.grid['dims']
        grid.dimensions = [nx+1, ny+1, nz+1]
        grid.spacing = self.grid.get('spacing', (1, 1, 1))
        
        # Adiciona propriedade para colorir
        if property_name is not None:
            if property_name not in self.properties:
                raise ValueError(f"Propriedade '{property_name}' não encontrada")
                
            grid.cell_data[property_name] = self.properties[property_name].flatten(order='F')
            scalars = property_name
        else:
            # Se não especificado, tenta usar porosidade ou primeira propriedade disponível
            if 'porosity' in self.properties:
                grid.cell_data['porosity'] = self.properties['porosity'].flatten(order='F')
                scalars = 'porosity'
            elif self.properties:
                first_prop = list(self.properties.keys())[0]
                grid.cell_data[first_prop] = self.properties[first_prop].flatten(order='F')
                scalars = first_prop
            else:
                # Sem propriedades, usa valores constantes
                grid.cell_data['dummy'] = np.ones(nx * ny * nz)
                scalars = 'dummy'
        
        # Inicializa visualizador
        plotter = pv.Plotter()
        
        # Adiciona malha
        plotter.add_mesh(grid, opacity=opacity, scalars=scalars, cmap='jet')
        
        # Adiciona poços
        if show_wells and self.wells:
            for well_name, well_data in self.wells.items():
                points = well_data['trajectory']
                
                # Cria linha 3D para trajetória
                line = pv.Line(points[0], points[-1])
                
                # Cor diferente para produtores e injetores
                if well_data.get('type') == 'producer':
                    color = 'red'
                else:
                    color = 'blue'
                
                plotter.add_mesh(line, color=color, line_width=5, label=well_name)
                
                # Adiciona texto com nome do poço
                plotter.add_point_labels(
                    [points[0]], [well_name], 
                    font_size=14, point_size=0,
                    always_visible=True
                )
        
        # Adiciona título
        plotter.add_title(f"Modelo 3D - {scalars}", font_size=16)
        
        # Salva captura de tela se caminho fornecido
        if save_path:
            plotter.screenshot(save_path, transparent_background=True)
        
        # Mostra visualização
        plotter.show()
    
    def plot_well_results(self, 
                        well_name: str,
                        ax: Optional[plt.Axes] = None,
                        save_path: Optional[str] = None) -> plt.Figure:
        """
        Plota resultados de produção para um poço.
        
        Args:
            well_name: Nome do poço
            ax: Eixo matplotlib para plotagem
            save_path: Caminho para salvar figura
            
        Returns:
            Figura matplotlib
        """
        if not self.simulation_results:
            raise ValueError("Execute uma simulação primeiro")
            
        if well_name not in self.simulation_results:
            raise ValueError(f"Resultados para poço '{well_name}' não encontrados")
            
        # Obtém resultados do poço
        results = self.simulation_results[well_name]
        
        # Cria figura se não fornecida
        if ax is None:
            fig, ax1 = plt.subplots(figsize=(12, 6))
        else:
            fig = ax.figure
            ax1 = ax
        
        # Plota taxas de produção/injeção
        time_days = results['time']
        
        # Eixo para taxas
        ax1.plot(time_days, results['oil_rate'], 'g-', label='Óleo')
        ax1.plot(time_days, results['water_rate'], 'b-', label='Água')
        ax1.plot(time_days, results['gas_rate'] / 10, 'r-', label='Gás (÷10)')
        ax1.set_xlabel('Tempo (dias)')
        ax1.set_ylabel('Taxa (bbl/d, mscf/d ÷10)')
        ax1.legend(loc='upper left')
        
        # Eixo secundário para pressão
        ax2 = ax1.twinx()
        ax2.plot(time_days, results['bhp'], 'k--', label='Pressão')
        ax2.set_ylabel('Pressão (psia)')
        ax2.legend(loc='upper right')
        
        # Adiciona título
        plt.title(f"Resultados de Produção - {well_name}")
        
        # Ajusta layout
        plt.tight_layout()
        
        # Salva figura se caminho fornecido
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def plot_field_results(self, 
                         save_path: Optional[str] = None) -> plt.Figure:
        """
        Plota resultados de produção para todo o campo.
        
        Args:
            save_path: Caminho para salvar figura
            
        Returns:
            Figura matplotlib
        """
        if not self.simulation_results:
            raise ValueError("Execute uma simulação primeiro")
            
        # Inicializa arrays para somatório de campo
        first_well = list(self.simulation_results.values())[0]
        time_days = first_well['time']
        num_steps = len(time_days)
        
        field_oil = np.zeros(num_steps)
        field_gas = np.zeros(num_steps)
        field_water = np.zeros(num_steps)
        
        # Soma contribuições de todos os poços
        for well_name, results in self.simulation_results.items():
            well_data = self.wells[well_name]
            
            if well_data.get('type') == 'producer':
                field_oil += results['oil_rate']
                field_gas += results['gas_rate']
                field_water += results['water_rate']
            else:  # injector
                field_water -= results['water_rate']  # Valores negativos para injeção
        
        # Cria figura
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Plota taxas de campo
        ax.plot(time_days, field_oil, 'g-', label='Óleo')
        ax.plot(time_days, field_water, 'b-', label='Água')
        ax.plot(time_days, field_gas / 10, 'r-', label='Gás (÷10)')
        
        # Calcula cumulativos
        cum_oil = np.cumsum(field_oil) * (time_days[1] - time_days[0]) / 365.25  # MBBL/ano
        
        # Adiciona cumulativo no eixo secundário
        ax2 = ax.twinx()
        ax2.plot(time_days, cum_oil, 'k--', label='Óleo Cumulativo')
        
        # Configurações de eixos
        ax.set_xlabel('Tempo (dias)')
        ax.set_ylabel('Taxa (bbl/d, mscf/d ÷10)')
        ax2.set_ylabel('Cumulativo (MBBL)')
        
        # Adiciona legendas
        ax.legend(loc='upper left')
        ax2.legend(loc='upper right')
        
        # Adiciona título
        plt.title("Resultados de Produção do Campo")
        
        # Ajusta layout
        plt.tight_layout()
        
        # Salva figura se caminho fornecido
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def analyze_simulation_results(self) -> Dict:
        """
        Analisa resultados de simulação.
        
        Returns:
            Dicionário com métricas de análise
        """
        if not self.simulation_results:
            raise ValueError("Execute uma simulação primeiro")
            
        # Inicializa dicionário de resultados
        analysis = {
            'wells': {},
            'field': {}
        }
        
        # Analisa cada poço
        for well_name, results in self.simulation_results.items():
            time_days = results['time']
            dt = time_days[1] - time_days[0]
            
            # Cálculo de cumulativos
            cum_oil = np.sum(results['oil_rate']) * dt / 365.25  # MBBL
            cum_gas = np.sum(results['gas_rate']) * dt / 365.25  # MMscf
            cum_water = np.sum(results['water_rate']) * dt / 365.25  # MBBL
            
            # Estatísticas
            max_oil_rate = np.max(results['oil_rate'])
            min_bhp = np.min(results['bhp'])
            
            # Armazena resultados
            analysis['wells'][well_name] = {
                'cum_oil': cum_oil,
                'cum_gas': cum_gas,
                'cum_water': cum_water,
                'max_oil_rate': max_oil_rate,
                'min_bhp': min_bhp
            }
        
        # Análise de campo
        field_cum_oil = sum(well['cum_oil'] for well in analysis['wells'].values())
        field_cum_gas = sum(well['cum_gas'] for well in analysis['wells'].values())
        
        analysis['field'] = {
            'cum_oil': field_cum_oil,
            'cum_gas': field_cum_gas,
            'recovery_factor': 0.0  # Seria calculado com OOIP
        }
        
        return analysis
    
    # ===============================
    # 6. Análise de Sensibilidade
    # ===============================
    
    def run_sensitivity_analysis(self,
                               parameter: str,
                               values: List[float],
                               metric: str = 'cum_oil') -> Dict:
        """
        Executa análise de sensibilidade variando um parâmetro.
        
        Args:
            parameter: Nome do parâmetro (ex: 'porosity')
            values: Lista de valores para testar
            metric: Métrica a analisar (ex: 'cum_oil', 'recovery_factor')
            
        Returns:
            Dicionário com resultados da análise
        """
        results = {}
        original_value = None
        
        # Verifica tipo de parâmetro
        if parameter in self.properties:
            # Salva valor original
            original_value = self.properties[parameter].copy()
            
            for value in values:
                # Cria propriedade com valor constante
                prop_array = np.ones(self.grid['dims']) * value
                self.properties[parameter] = prop_array
                
                # Executa simulação
                self.run_simulation(end_time=1825, time_step=30)  # 5 anos
                
                # Analisa resultados
                analysis = self.analyze_simulation_results()
                results[value] = analysis['field'].get(metric, 0.0)
                
            # Restaura valor original
            self.properties[parameter] = original_value
                
        else:
            self.logger.warning(f"Parâmetro '{parameter}' não encontrado para análise de sensibilidade")
        
        return results
    
    def plot_sensitivity_results(self,
                               sensitivity_results: Dict,
                               parameter: str,
                               metric: str,
                               ax: Optional[plt.Axes] = None,
                               save_path: Optional[str] = None) -> plt.Figure:
        """
        Plota resultados de análise de sensibilidade.
        
        Args:
            sensitivity_results: Resultados da análise
            parameter: Nome do parâmetro
            metric: Métrica analisada
            ax: Eixo matplotlib para plotagem
            save_path: Caminho para salvar figura
            
        Returns:
            Figura matplotlib
        """
        # Extrai valores e resultados
        values = list(sensitivity_results.keys())
        metrics = list(sensitivity_results.values())
        
        # Cria figura se não fornecida
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        else:
            fig = ax.figure
        
        # Plota resultados
        ax.plot(values, metrics, 'bo-', linewidth=2, markersize=8)
        
        # Adiciona linha de tendência
        z = np.polyfit(values, metrics, 1)
        p = np.poly1d(z)
        ax.plot(values, p(values), 'r--', linewidth=1)
        
        # Adiciona labels
        ax.set_xlabel(f"{parameter}")
        ax.set_ylabel(f"{metric}")
        ax.set_title(f"Análise de Sensibilidade - {parameter} vs {metric}")
        
        # Adiciona grade
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Ajusta layout
        plt.tight_layout()
        
        # Salva figura se caminho fornecido
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig

# ===============================
# 7. Exemplo de Uso
# ===============================

if __name__ == "__main__":
    # Exemplo de uso do ReservoirSimulator
    print("Demonstração do ReservoirSimulator")
    
    # Inicializa simulador
    simulator = ReservoirSimulator()
    
    # 1. Cria malha cartesiana
    simulator.create_structured_grid(20, 15, 10, dx=100, dy=100, dz=20)
    
    # 2. Gera propriedades petrofísicas
    nx, ny, nz = simulator.grid['dims']
    
    # Porosidade
    porosity = np.random.uniform(0.1, 0.3, (nx, ny, nz))
    simulator.add_property('porosity', porosity)
    
    # Permeabilidade correlacionada com porosidade
    permeability = porosity**3 * 1e4
    simulator.add_property('permeability', permeability)
    
    # 3. Adiciona poços
    # Poço produtor
    prod_traj = [(5, 5, 0), (5, 5, 5), (10, 10, 8)]
    completions = [{'i': 10, 'j': 10, 'k': 8, 'diameter': 0.1, 'skin': 0}]
    prod_schedule = [
        {'time': 0, 'control': 'rate', 'value': 1000, 'type': 'oil'},
        {'time': 180, 'control': 'bhp', 'value': 2000, 'type': 'oil'}
    ]
    simulator.add_well("PROD-01", prod_traj, completions, prod_schedule)
    
    # Poço injetor
    inj_traj = [(15, 12, 0), (15, 12, 8)]
    inj_completions = [{'i': 15, 'j': 12, 'k': 8, 'diameter': 0.1, 'skin': 0}]
    inj_schedule = [
        {'time': 0, 'control': 'rate', 'value': 1500, 'type': 'water'}
    ]
    simulator.add_well("INJ-01", inj_traj, inj_completions, inj_schedule)
    simulator.convert_well_type("INJ-01", "injector")
    
    # 4. Executa simulação
    simulator.run_simulation(end_time=1825, time_step=30)  # 5 anos
    
    # 5. Visualiza resultados
    try:
        # Visualização de propriedades
        simulator.plot_property_slice('porosity', layer=5)
        
        # Visualização 3D (requer ambiente gráfico)
        if PYVISTA_AVAILABLE:
            simulator.plot_3d_model()
        
        # Resultados de poço
        simulator.plot_well_results("PROD-01")
        
        # Resultados de campo
        simulator.plot_field_results()
        
    except Exception as e:
        print(f"Erro na visualização: {str(e)}")
        
    # 6. Análise de resultados
    analysis = simulator.analyze_simulation_results()
    print("\nResultados da simulação:")
    print(f"Óleo cumulativo: {analysis['field']['cum_oil']:.2f} MBBL")
    
    print("\nReservoirSimulator demonstração concluída!") 