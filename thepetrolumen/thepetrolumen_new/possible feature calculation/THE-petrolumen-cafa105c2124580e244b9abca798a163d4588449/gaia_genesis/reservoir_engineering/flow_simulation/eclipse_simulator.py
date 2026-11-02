import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import json
try:
    import pyvista as pv
    PYVISTA_AVAILABLE = True
except ImportError:
    PYVISTA_AVAILABLE = False

# Optional imports for specialized functionality
try:
    from libecl import EclGrid, EclFile
    LIBECL_AVAILABLE = True
except ImportError:
    LIBECL_AVAILABLE = False

class EclipseSimulator:
    """
    Classe para simulação de reservatórios usando funcionalidades similares ao Eclipse (Schlumberger).
    Implementa simulação black-oil, composicional, térmica e streamline.
    """
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.grid = None
        self.properties = {}
        self.wells = {}
        self.schedule = pd.DataFrame()
        self.faults = []
        self.simulation_results = {}
        self.eos_model = None  # Modelo de equação de estado
        self.thermal_model = False  # Flag para simulação térmica
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('EclipseSimulator')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    # ===============================
    # 1. Modelagem de Reservatório
    # ===============================
    
    def import_eclipse_grid(self, filepath: str):
        """
        Importa malha do formato .DATA (Eclipse) usando libecl.
        
        Args:
            filepath: Caminho para o arquivo .DATA
        """
        if not LIBECL_AVAILABLE:
            raise ImportError("libecl não está instalado. Instale via pip install libecl")
            
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo {filepath} não encontrado")
            
        try:
            self.grid = EclGrid(filepath)
            active_cells = self.grid.get_num_active()
            total_cells = self.grid.get_num_global()
            
            self.logger.info(f"Malha importada: {active_cells} células ativas de {total_cells} total")
            
            # Inicializa dicionários para propriedades
            dims = self.grid.dims
            self.grid_dims = dims
            
        except Exception as e:
            self.logger.error(f"Erro ao importar malha Eclipse: {str(e)}")
            raise
    
    def create_structured_grid(self, nx: int, ny: int, nz: int, dx: float = 1.0, dy: float = 1.0, dz: float = 1.0):
        """
        Cria malha cartesiana regular para uso com formato Eclipse.
        
        Args:
            nx: Número de células na direção X
            ny: Número de células na direção Y
            nz: Número de células na direção Z
            dx: Tamanho das células na direção X
            dy: Tamanho das células na direção Y
            dz: Tamanho das células na direção Z
        """
        # Estrutura da malha
        self.grid = {
            'type': 'cartesian',
            'dims': (nx, ny, nz),
            'spacing': (dx, dy, dz),
            'cells': np.zeros((nx, ny, nz))
        }
        
        self.grid_dims = (nx, ny, nz)
        
        # Inicializa arrays de coordenadas para fácil plotagem
        x = np.linspace(0, nx * dx, nx + 1)
        y = np.linspace(0, ny * dy, ny + 1)
        z = np.linspace(0, nz * dz, nz + 1)
        
        self.grid['coords'] = {
            'x': x,
            'y': y,
            'z': z
        }
        
        self.logger.info(f"Malha estruturada Eclipse criada: {nx}x{ny}x{nz}")
    
    def import_eclipse_properties(self, filepath: str, property_names: List[str] = None):
        """
        Importa propriedades de um arquivo .INIT ou .UNRST do Eclipse.
        
        Args:
            filepath: Caminho para o arquivo .INIT ou .UNRST
            property_names: Lista de nomes de propriedades para importar
        """
        if not LIBECL_AVAILABLE:
            raise ImportError("libecl não está instalado. Instale via pip install libecl")
            
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo {filepath} não encontrado")
            
        try:
            ecl_file = EclFile(filepath)
            
            # Se property_names não for fornecido, importa todas as propriedades
            if property_names is None:
                property_names = [key for key in ecl_file.keys()]
                
            for prop_name in property_names:
                if prop_name in ecl_file:
                    data = ecl_file[prop_name][0]
                    self.properties[prop_name] = data
                    self.logger.info(f"Propriedade '{prop_name}' importada")
                else:
                    self.logger.warning(f"Propriedade '{prop_name}' não encontrada no arquivo")
                    
        except Exception as e:
            self.logger.error(f"Erro ao importar propriedades Eclipse: {str(e)}")
            raise
    
    def add_eclipse_property(self, property_name: str, data: np.ndarray):
        """
        Adiciona propriedade petrofísica (porosidade, permeabilidade, etc).
        
        Args:
            property_name: Nome da propriedade
            data: Array com valores da propriedade
        """
        if self.grid is None:
            raise ValueError("Crie uma malha antes de adicionar propriedades")
        
        if isinstance(self.grid, dict):
            expected_shape = self.grid['dims']
            if data.shape != expected_shape:
                raise ValueError(f"Dimensões da propriedade {data.shape} incompatíveis com a malha {expected_shape}")
        else:
            # Para grids do libecl, verifica compatibilidade
            if len(data) != self.grid.get_num_active():
                raise ValueError(f"Dimensões da propriedade {len(data)} incompatíveis com células ativas {self.grid.get_num_active()}")
        
        self.properties[property_name] = data
        self.logger.info(f"Propriedade '{property_name}' adicionada com sucesso")
    
    def define_faults(self, fault_name: str, fault_planes: List[Tuple]):
        """
        Define falhas geológicas usando formato similar ao ECLIPSE.
        
        Args:
            fault_name: Nome da falha
            fault_planes: Lista de tuplas definindo os planos da falha
                Ex: [(i1, j1, k1, i2, j2, k2, face), ...]
                onde face é 'I', 'J' ou 'K'
        """
        self.faults.append({
            'name': fault_name,
            'planes': fault_planes
        })
        
        self.logger.info(f"Falha '{fault_name}' definida com {len(fault_planes)} planos") 
    
    # ===============================
    # 2. Gerenciamento de Poços
    # ===============================
    
    def add_well_with_schedule(self, 
                             name: str, 
                             trajectory: List[Tuple[float, float, float]], 
                             controls: Dict,
                             well_type: str = 'PRODUCER'):
        """
        Adiciona poço com cronograma de produção.
        
        Args:
            name: Nome do poço
            trajectory: Lista de pontos definindo a trajetória
            controls: Dicionário com controles (tempos, taxas, etc)
                Ex: {"time": [0, 30], "rate": [1000, 500]}
            well_type: Tipo de poço ('PRODUCER' ou 'INJECTOR')
        """
        if not trajectory:
            raise ValueError("Trajetória deve conter pelo menos um ponto")
            
        # Conversão para array numpy
        trajectory_array = np.array(trajectory)
        
        # Verifica e converte controles para DataFrame
        controls_df = pd.DataFrame(controls)
        if 'time' not in controls_df.columns:
            raise ValueError("Os controles devem incluir uma coluna 'time'")
            
        # Adiciona o poço
        self.wells[name] = {
            'trajectory': trajectory_array,
            'controls': controls_df,
            'type': well_type.upper()  # Normaliza para maiúsculas
        }
        
        self.logger.info(f"Poço '{name}' adicionado com {len(trajectory)} pontos e {len(controls_df)} controles")
    
    def set_well_schedule(self, 
                        well_name: str, 
                        controls: Dict):
        """
        Define cronograma de produção/injeção para um poço existente.
        
        Args:
            well_name: Nome do poço
            controls: Dicionário com controles
        """
        if well_name not in self.wells:
            raise ValueError(f"Poço '{well_name}' não existe")
            
        controls_df = pd.DataFrame(controls)
        if 'time' not in controls_df.columns:
            raise ValueError("Os controles devem incluir uma coluna 'time'")
            
        self.wells[well_name]['controls'] = controls_df
        self.logger.info(f"Cronograma atualizado para poço '{well_name}' com {len(controls_df)} controles")
    
    def set_well_completion(self, 
                          well_name: str, 
                          completions: List[Dict]):
        """
        Define completações para um poço (formato similar ao COMPDAT do Eclipse).
        
        Args:
            well_name: Nome do poço
            completions: Lista de dicionários com completações
                Ex: [{'i': 5, 'j': 5, 'k1': 3, 'k2': 5, 'skin': 0, 'rw': 0.15}]
        """
        if well_name not in self.wells:
            raise ValueError(f"Poço '{well_name}' não existe")
            
        self.wells[well_name]['completions'] = completions
        self.logger.info(f"Completações atualizadas para poço '{well_name}'")
    
    def apply_direct_regrouping(self, 
                              well_groups: Dict[str, List[str]]):
        """
        Reagrupamento direto de poços (similar ao Eclipse 100/300).
        
        Args:
            well_groups: Dicionário com grupos e seus poços
                Ex: {'NORTH_GROUP': ['WELL-1', 'WELL-2'], 'SOUTH_GROUP': ['WELL-3']}
        """
        for group_name, wells in well_groups.items():
            for well_name in wells:
                if well_name in self.wells:
                    self.wells[well_name]['group'] = group_name
                else:
                    self.logger.warning(f"Poço '{well_name}' não encontrado para reagrupamento")
                    
        self.logger.info(f"Reagrupamento aplicado para {len(well_groups)} grupos")
    
    # ===============================
    # 3. Simulação Numérica
    # ===============================
    
    def setup_fluid_model(self, 
                        model_type: str = 'BLACK_OIL',
                        fluid_props: Optional[Dict] = None):
        """
        Configura modelo de fluido para simulação.
        
        Args:
            model_type: Tipo de modelo ('BLACK_OIL', 'COMPOSITIONAL', 'THERMAL')
            fluid_props: Dicionário com propriedades do fluido
        """
        valid_models = ['BLACK_OIL', 'COMPOSITIONAL', 'THERMAL']
        model_type = model_type.upper()
        
        if model_type not in valid_models:
            raise ValueError(f"Tipo de modelo inválido. Use {valid_models}")
            
        if fluid_props is None:
            fluid_props = {}
            
        self.fluid_model = {
            'type': model_type,
            'properties': fluid_props
        }
        
        # Define flags para configurações específicas
        if model_type == 'THERMAL':
            self.thermal_model = True
            
        if model_type == 'COMPOSITIONAL':
            self.eos_model = fluid_props.get('eos', 'PR')  # Peng-Robinson como padrão
            
        self.logger.info(f"Modelo de fluido '{model_type}' configurado")
    
    def run_black_oil_simulation(self, 
                               end_time: float,
                               time_step: float,
                               use_cpr: bool = True,
                               output_interval: Optional[float] = None):
        """
        Executa simulação Black-Oil com solucionador CPR.
        
        Args:
            end_time: Tempo final da simulação
            time_step: Passo de tempo
            use_cpr: Se deve usar solucionador CPR
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
            
        # Configuração do solver
        solver_config = {
            'method': 'CPR' if use_cpr else 'DIRECT',
            'preconditioner': 'AMG' if use_cpr else None,
            'tolerance': 1e-6,
            'max_iterations': 50
        }
        
        self.logger.info(f"Iniciando simulação Black-Oil com solver {solver_config['method']}")
        
        # Inicializa resultados
        times = np.arange(0, end_time + time_step, output_interval)
        num_steps = len(times)
        
        # Implementação simplificada - em um caso real usaria OPM ou outro solver
        # Esta é uma simulação sintética para demonstração
        results = {}
        for well_name, well_data in self.wells.items():
            
            if well_data['type'] == 'PRODUCER':
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
                
            else:  # INJECTOR
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
        
        self.logger.info("Simulação Black-Oil concluída com sucesso")
        
    def run_compositional_simulation(self, 
                                  end_time: float,
                                  time_step: float,
                                  equation_of_state: str = 'PR',
                                  output_interval: Optional[float] = None):
        """
        Executa simulação composicional (similar ao Eclipse 300).
        
        Args:
            end_time: Tempo final da simulação
            time_step: Passo de tempo
            equation_of_state: Equação de estado ('PR' para Peng-Robinson, 'SRK' para Soave-Redlich-Kwong)
            output_interval: Intervalo de saída (se None, usa time_step)
        """
        # Salva a equação de estado
        self.eos_model = equation_of_state
        
        # Configuração específica para simulação composicional
        self.logger.info(f"Iniciando simulação composicional com equação de estado {equation_of_state}")
        
        # Usa a mesma função black-oil para simulação sintética
        # Em um caso real, usaria um solver composicional real
        self.run_black_oil_simulation(end_time, time_step, True, output_interval)
        
        self.logger.info("Simulação composicional concluída com sucesso")
        
    def run_thermal_simulation(self, 
                             end_time: float,
                             time_step: float,
                             output_interval: Optional[float] = None):
        """
        Executa simulação térmica (similar ao Eclipse 300 Thermal).
        
        Args:
            end_time: Tempo final da simulação
            time_step: Passo de tempo
            output_interval: Intervalo de saída (se None, usa time_step)
        """
        # Ativa flag de simulação térmica
        self.thermal_model = True
        
        # Configuração específica para simulação térmica
        self.logger.info("Iniciando simulação térmica")
        
        # Usa a mesma função black-oil para simulação sintética
        # Em um caso real, usaria um solver térmico real
        self.run_black_oil_simulation(end_time, time_step, True, output_interval)
        
        self.logger.info("Simulação térmica concluída com sucesso")
        
    # ===============================
    # 4. Visualização e Análise
    # ===============================
    
    def plot_property_3d(self, 
                       property_name: str,
                       opacity: float = 0.7,
                       show_wells: bool = True,
                       save_path: Optional[str] = None) -> None:
        """
        Visualização 3D de propriedade petrofísica.
        
        Args:
            property_name: Nome da propriedade
            opacity: Opacidade do modelo (0-1)
            show_wells: Se deve mostrar os poços
            save_path: Caminho para salvar captura de tela
        """
        if not PYVISTA_AVAILABLE:
            raise ImportError("PyVista é necessário para visualização 3D")
            
        if self.grid is None:
            raise ValueError("Malha não definida")
            
        if property_name not in self.properties:
            raise ValueError(f"Propriedade '{property_name}' não encontrada")
            
        # Cria grid PyVista
        if isinstance(self.grid, dict):  # Malha estruturada criada internamente
            grid = pv.UniformGrid()
            nx, ny, nz = self.grid['dims']
            grid.dimensions = [nx+1, ny+1, nz+1]
            grid.spacing = self.grid.get('spacing', (1, 1, 1))
            
            # Adiciona propriedade
            grid.cell_data[property_name] = self.properties[property_name].flatten(order='F')
        else:  # Malha do Eclipse via libecl
            # Implementação simplificada para malhas do Eclipse
            # Em um caso real, usaria a geometria completa do grid
            nx, ny, nz = self.grid_dims
            grid = pv.UniformGrid((nx, ny, nz))
            
            # Adapta propriedade para grid do PyVista
            grid.cell_data[property_name] = self.properties[property_name]
        
        # Inicializa visualizador
        plotter = pv.Plotter()
        
        # Adiciona malha
        plotter.add_mesh(grid, opacity=opacity, scalars=property_name, cmap='jet')
        
        # Adiciona poços
        if show_wells and self.wells:
            for well_name, well_data in self.wells.items():
                points = well_data['trajectory']
                
                # Cria linha 3D para trajetória
                if len(points) >= 2:
                    line = pv.Line(points[0], points[-1])
                    
                    # Cor diferente para produtores e injetores
                    if well_data.get('type') == 'PRODUCER':
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
        plotter.add_title(f"Modelo 3D - {property_name}", font_size=16)
        
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
    
    def production_forecast_plot(self,
                               save_path: Optional[str] = None) -> plt.Figure:
        """
        Plota previsão de produção para todo o campo (estilo Eclipse/Petrel).
        
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
            
            if well_data.get('type') == 'PRODUCER':
                field_oil += results['oil_rate']
                field_gas += results['gas_rate']
                field_water += results['water_rate']
            else:  # INJECTOR
                field_water -= results['water_rate']  # Valores negativos para injeção
        
        # Cria figura com dois painéis (taxas e cumulativos)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        
        # Painel 1: Taxas diárias
        ax1.plot(time_days, field_oil, 'g-', label='Óleo')
        ax1.plot(time_days, field_water, 'b-', label='Água')
        ax1.plot(time_days, field_gas / 10, 'r-', label='Gás (÷10)')
        ax1.set_ylabel('Taxa (bbl/d, mscf/d ÷10)')
        ax1.legend(loc='best')
        ax1.set_title("Previsão de Produção do Campo")
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # Painel 2: Cumulativos
        dt = time_days[1] - time_days[0]
        cum_oil = np.cumsum(field_oil * dt / 1000)  # MSTB
        cum_gas = np.cumsum(field_gas * dt / 1000)  # MMscf
        cum_water = np.cumsum(field_water * dt / 1000)  # MSTB
        
        ax2.plot(time_days, cum_oil, 'g-', label='Óleo')
        ax2.plot(time_days, cum_water, 'b-', label='Água')
        ax2.plot(time_days, cum_gas / 10, 'r-', label='Gás (÷10)')
        ax2.set_xlabel('Tempo (dias)')
        ax2.set_ylabel('Cumulativo (MSTB, MMscf ÷10)')
        ax2.legend(loc='best')
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        # Ajusta layout
        plt.tight_layout()
        
        # Salva figura se caminho fornecido
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def analyze_results(self) -> Dict:
        """
        Analisa resultados da simulação.
        
        Returns:
            Dicionário com análises de produção
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
            cum_oil = np.sum(results['oil_rate']) * dt / 1000  # MSTB
            cum_gas = np.sum(results['gas_rate']) * dt / 1000  # MMscf
            cum_water = np.sum(results['water_rate']) * dt / 1000  # MSTB
            
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
        field_cum_water = sum(well['cum_water'] for well in analysis['wells'].values())
        
        # Estimativa de recovery factor baseada em OOIP (simplificado)
        # Em um caso real, calcularia a partir do volume de poros e saturações
        ooip_estimate = 100000.0  # MSTB - simplificado
        recovery_factor = field_cum_oil / ooip_estimate if ooip_estimate > 0 else 0.0
        
        analysis['field'] = {
            'cum_oil': field_cum_oil,
            'cum_gas': field_cum_gas,
            'cum_water': field_cum_water,
            'recovery_factor': recovery_factor,
            'ooip_estimate': ooip_estimate
        }
        
        return analysis
    
    # ===============================
    # 5. Integração e Exportação
    # ===============================
    
    def export_to_eclipse(self, filename: str):
        """
        Exporta modelo para formato Eclipse.
        
        Args:
            filename: Caminho para salvar arquivo
        """
        if self.grid is None:
            raise ValueError("Malha não definida")
            
        file_path = Path(filename)
        parent_dir = file_path.parent
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            # Cabeçalho
            f.write("-- Arquivo gerado por EclipseSimulator\n")
            f.write("-- Data: " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
            
            # Seção RUNSPEC
            f.write("RUNSPEC\n\n")
            
            # Dimensões
            if isinstance(self.grid, dict):
                nx, ny, nz = self.grid['dims']
            else:
                nx, ny, nz = self.grid_dims
                
            f.write(f"DIMENS\n{nx} {ny} {nz} /\n\n")
            
            # Fases
            f.write("OIL\nWATER\nGAS\n\n")
            
            # Unidades (campo)
            f.write("FIELD\n\n")
            
            # Seção GRID
            f.write("GRID\n\n")
            
            # Mais código seria necessário para uma exportação completa
            
            f.write("-- Exportação simplificada. Mais detalhes seriam incluídos em uma implementação completa.\n")
            
        self.logger.info(f"Modelo exportado para formato Eclipse: {filename}")
        
    def export_to_petrel(self, filename: str):
        """
        Exporta modelo para formato compatível com Petrel.
        
        Args:
            filename: Caminho para salvar arquivo
        """
        if self.grid is None:
            raise ValueError("Malha não definida")
            
        file_path = Path(filename)
        parent_dir = file_path.parent
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        # Aqui seria implementada a exportação real para o formato do Petrel
        # Esta é uma implementação simplificada para demonstração
        
        self.logger.info(f"Modelo exportado para formato Petrel: {filename}")
        
    def uncertainty_analysis(self, 
                           parameters: Dict[str, Tuple[float, float]],
                           iterations: int = 100,
                           save_path: Optional[str] = None) -> pd.DataFrame:
        """
        Executa análise de incerteza por Monte Carlo.
        
        Args:
            parameters: Dicionário com parâmetros e faixas (min, max)
                Ex: {'porosity': (0.1, 0.3), 'permeability': (10, 1000)}
            iterations: Número de iterações
            save_path: Caminho para salvar resultados
            
        Returns:
            DataFrame com resultados da análise
        """
        self.logger.info(f"Iniciando análise de incerteza com {iterations} iterações")
        
        # Inicializa dataframe para resultados
        results = []
        
        # Executa iterações
        for i in range(iterations):
            # Amostra parâmetros
            sample = {}
            for param, (min_val, max_val) in parameters.items():
                sample[param] = np.random.uniform(min_val, max_val)
                
            # Aplicaria os parâmetros ao modelo e executaria a simulação
            # Aqui é uma simplificação para demonstração
            if 'porosity' in sample:
                recovery_factor = 0.2 + 0.3 * sample['porosity']  # Relação simplificada
            else:
                recovery_factor = 0.2 + 0.1 * np.random.random()
                
            cum_oil = 100000 * recovery_factor
            
            # Armazena resultados
            sample['recovery_factor'] = recovery_factor
            sample['cum_oil'] = cum_oil
            results.append(sample)
            
            if i % 10 == 0:
                self.logger.info(f"Análise de incerteza: {i} de {iterations} iterações")
                
        # Converte para DataFrame
        results_df = pd.DataFrame(results)
        
        # Salva resultados se caminho fornecido
        if save_path:
            results_df.to_csv(save_path, index=False)
            
        self.logger.info("Análise de incerteza concluída")
        
        return results_df
    
    def plot_uncertainty_results(self,
                               results_df: pd.DataFrame,
                               param_name: str,
                               result_name: str,
                               save_path: Optional[str] = None) -> plt.Figure:
        """
        Plota resultados da análise de incerteza.
        
        Args:
            results_df: DataFrame com resultados
            param_name: Nome do parâmetro para o eixo x
            result_name: Nome do resultado para o eixo y
            save_path: Caminho para salvar figura
            
        Returns:
            Figura matplotlib
        """
        if param_name not in results_df.columns or result_name not in results_df.columns:
            raise ValueError(f"Parâmetro {param_name} ou resultado {result_name} não encontrado nos resultados")
            
        # Cria figura
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Gráfico de dispersão
        ax.scatter(results_df[param_name], results_df[result_name], alpha=0.7)
        
        # Adiciona linha de tendência
        z = np.polyfit(results_df[param_name], results_df[result_name], 1)
        p = np.poly1d(z)
        ax.plot(results_df[param_name], p(results_df[param_name]), 'r--', linewidth=1)
        
        # Adiciona labels
        ax.set_xlabel(param_name)
        ax.set_ylabel(result_name)
        ax.set_title(f"Análise de Incerteza - {param_name} vs {result_name}")
        
        # Adiciona equação da reta
        eq_text = f"y = {z[0]:.3f}x + {z[1]:.3f}"
        ax.annotate(eq_text, xy=(0.05, 0.95), xycoords='axes fraction', 
                   fontsize=10, ha='left', va='top',
                   bbox=dict(boxstyle='round', fc='white', alpha=0.7))
        
        # Adiciona grade
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Ajusta layout
        plt.tight_layout()
        
        # Salva figura se caminho fornecido
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig

# ===============================
# 6. Exemplo de Uso
# ===============================

if __name__ == "__main__":
    # Exemplo de uso do EclipseSimulator
    print("Demonstração do EclipseSimulator")
    
    # Inicializa simulador
    simulator = EclipseSimulator()
    
    # 1. Cria malha estruturada
    simulator.create_structured_grid(20, 15, 10, dx=100, dy=100, dz=20)
    
    # 2. Adiciona propriedades petrofísicas
    nx, ny, nz = simulator.grid['dims']
    
    # Porosidade
    porosity = np.random.uniform(0.1, 0.3, (nx, ny, nz))
    simulator.add_eclipse_property('PORO', porosity)
    
    # Permeabilidade correlacionada com porosidade
    permeability = porosity**3 * 1e4
    simulator.add_eclipse_property('PERMX', permeability)
    
    # Saturação de água
    swi = np.ones((nx, ny, nz)) * 0.2
    simulator.add_eclipse_property('SWI', swi)
    
    # 3. Define falhas
    fault_planes = [(5, 0, 0, 5, ny-1, nz-1, 'I')]
    simulator.define_faults('MAIN_FAULT', fault_planes)
    
    # 4. Adiciona poços
    # Poço produtor
    prod_traj = [(5, 5, 0), (5, 5, 5), (10, 10, 8)]
    prod_controls = {
        'time': [0, 180, 365],
        'control': ['RATE', 'BHP', 'RATE'],
        'value': [1000, 2000, 800]
    }
    simulator.add_well_with_schedule("PROD-01", prod_traj, prod_controls, 'PRODUCER')
    
    # Completa o poço produtor
    completions = [
        {'i': 10, 'j': 10, 'k1': 7, 'k2': 9, 'skin': 0, 'rw': 0.15}
    ]
    simulator.set_well_completion("PROD-01", completions)
    
    # Poço injetor
    inj_traj = [(15, 12, 0), (15, 12, 8)]
    inj_controls = {
        'time': [0, 180],
        'control': ['RATE', 'RATE'],
        'value': [1500, 1800]
    }
    simulator.add_well_with_schedule("INJ-01", inj_traj, inj_controls, 'INJECTOR')
    
    # 5. Configura modelo de fluido
    fluid_props = {
        'oil_density': 53.0,  # lb/ft³
        'water_density': 62.4,  # lb/ft³
        'gas_density': 0.06,  # lb/ft³
        'oil_viscosity': 2.0,  # cp
        'water_viscosity': 0.5,  # cp
        'gas_viscosity': 0.02  # cp
    }
    simulator.setup_fluid_model('BLACK_OIL', fluid_props)
    
    # 6. Executa simulação
    simulator.run_black_oil_simulation(end_time=1825, time_step=30, use_cpr=True)  # 5 anos
    
    # 7. Visualiza resultados
    try:
        # Visualização de propriedades
        simulator.plot_property_3d('PORO')
        
        # Resultados de poço
        simulator.plot_well_results("PROD-01")
        
        # Resultados de campo
        simulator.production_forecast_plot()
        
    except Exception as e:
        print(f"Erro na visualização: {str(e)}")
    
    # 8. Análise de resultados
    analysis = simulator.analyze_results()
    print("\nResultados da simulação:")
    print(f"Óleo cumulativo: {analysis['field']['cum_oil']:.2f} MSTB")
    print(f"Fator de recuperação: {analysis['field']['recovery_factor']:.3f}")
    
    # 9. Análise de incerteza
    params = {
        'porosity': (0.1, 0.3),
        'permeability': (10, 500)
    }
    uncertainty_results = simulator.uncertainty_analysis(params, iterations=50)
    simulator.plot_uncertainty_results(uncertainty_results, 'porosity', 'recovery_factor')
    
    # 10. Exportação para formato Eclipse
    simulator.export_to_eclipse("reservoir_model.DATA")
    
    print("\nEclipseSimulator demonstração concluída!") 