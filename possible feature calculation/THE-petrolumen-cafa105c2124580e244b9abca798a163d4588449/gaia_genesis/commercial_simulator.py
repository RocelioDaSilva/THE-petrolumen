import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit

class CommercialSimulator:
    def __init__(self, simulator_type: str = 'tNavigator'):
        """
        Inicializa o simulador comercial.
        
        Args:
            simulator_type: Tipo do simulador ('tNavigator', 'Eclipse', 'CMG', 'ECHELON', 'Nexus')
        """
        self.simulator_type = simulator_type
        self.grid = None
        self.wells = {}
        self.pvt_data = {}
        self.thermal_data = {}
        self.compositional_data = {}
        self.simulation_results = {}
        
    def create_static_model(self,
                          nx: int,
                          ny: int,
                          nz: int,
                          dx: float,
                          dy: float,
                          dz: float,
                          properties: Dict[str, np.ndarray]):
        """
        Cria modelo estático do reservatório.
        
        Args:
            nx, ny, nz: Dimensões da malha
            dx, dy, dz: Tamanho das células
            properties: Dicionário com propriedades petrofísicas
        """
        self.grid = {
            'nx': nx,
            'ny': ny,
            'nz': nz,
            'dx': dx,
            'dy': dy,
            'dz': dz,
            'properties': properties
        }
        
    def setup_pvt_model(self,
                       pvt_type: str = 'black_oil',
                       components: List[str] = None,
                       pvt_data: Dict = None):
        """
        Configura modelo PVT.
        
        Args:
            pvt_type: Tipo do modelo ('black_oil', 'compositional', 'thermal')
            components: Lista de componentes (para modelo composicional)
            pvt_data: Dados PVT
        """
        if pvt_type == 'compositional':
            self._setup_compositional_pvt(components, pvt_data)
        elif pvt_type == 'thermal':
            self._setup_thermal_pvt(pvt_data)
        else:
            self._setup_black_oil_pvt(pvt_data)
            
    def add_well(self,
                well_name: str,
                well_type: str,
                completion: List[Tuple[int, int, int]],
                constraints: Dict):
        """
        Adiciona poço ao modelo.
        
        Args:
            well_name: Nome do poço
            well_type: Tipo do poço ('producer', 'injector')
            completion: Lista de células de completação
            constraints: Restrições do poço
        """
        self.wells[well_name] = {
            'type': well_type,
            'completion': completion,
            'constraints': constraints
        }
        
    def run_simulation(self,
                      timesteps: int,
                      dt: float,
                      simulation_type: str = 'black_oil'):
        """
        Executa simulação.
        
        Args:
            timesteps: Número de passos de tempo
            dt: Tamanho do passo de tempo
            simulation_type: Tipo de simulação
        """
        if simulation_type == 'compositional':
            self._run_compositional_simulation(timesteps, dt)
        elif simulation_type == 'thermal':
            self._run_thermal_simulation(timesteps, dt)
        else:
            self._run_black_oil_simulation(timesteps, dt)
            
    def _setup_compositional_pvt(self, components: List[str], pvt_data: Dict):
        """Configura modelo PVT composicional."""
        self.compositional_data = {
            'components': components,
            'pvt_data': pvt_data,
            'eos': 'PR'  # Peng-Robinson EOS
        }
        
    def _setup_thermal_pvt(self, pvt_data: Dict):
        """Configura modelo PVT térmico."""
        self.thermal_data = {
            'pvt_data': pvt_data,
            'rock_heat_capacity': 0.2,  # Btu/lb-°F
            'rock_thermal_conductivity': 1.0  # Btu/ft-hr-°F
        }
        
    def _setup_black_oil_pvt(self, pvt_data: Dict):
        """Configura modelo PVT black-oil."""
        self.pvt_data = pvt_data
        
    def _run_compositional_simulation(self, timesteps: int, dt: float):
        """Executa simulação composicional usando EOS."""
        nx, ny, nz = self.grid['nx'], self.grid['ny'], self.grid['nz']
        components = self.compositional_data['components']
        nc = len(components)
        
        # Inicializar arrays
        pressure = np.zeros((nx, ny, nz))
        temperature = np.ones((nx, ny, nz)) * 180  # °F
        composition = np.zeros((nx, ny, nz, nc))
        saturation = np.zeros((nx, ny, nz, 2))  # óleo e gás
        
        # Propriedades do reservatório
        kx = self.grid['properties'].get('permeability_x', np.ones((nx, ny, nz)))
        ky = self.grid['properties'].get('permeability_y', np.ones((nx, ny, nz)))
        kz = self.grid['properties'].get('permeability_z', np.ones((nx, ny, nz)))
        phi = self.grid['properties'].get('porosity', np.ones((nx, ny, nz)) * 0.2)
        
        for t in range(timesteps):
            # Calcular equilíbrio de fases
            for i in range(nx):
                for j in range(ny):
                    for k in range(nz):
                        # Flash calculation usando EOS de Peng-Robinson
                        z = composition[i,j,k]
                        p = pressure[i,j,k]
                        T = temperature[i,j,k]
                        
                        # Calcular K-values
                        K = self._calculate_k_values(z, p, T)
                        
                        # Flash calculation
                        beta, x, y = self._flash_calculation(z, K)
                        
                        # Atualizar composições e saturações
                        composition[i,j,k] = z
                        saturation[i,j,k,0] = beta  # saturação de óleo
                        saturation[i,j,k,1] = 1 - beta  # saturação de gás
            
            # Calcular fluxos
            for i in range(1, nx-1):
                for j in range(1, ny-1):
                    for k in range(1, nz-1):
                        # Fluxos nas direções x, y, z
                        for c in range(nc):
                            qx = self._calculate_flux(
                                kx[i,j,k], pressure[i+1,j,k], pressure[i-1,j,k],
                                composition[i+1,j,k,c], composition[i-1,j,k,c],
                                saturation[i,j,k]
                            )
                            qy = self._calculate_flux(
                                ky[i,j,k], pressure[i,j+1,k], pressure[i,j-1,k],
                                composition[i,j+1,k,c], composition[i,j-1,k,c],
                                saturation[i,j,k]
                            )
                            qz = self._calculate_flux(
                                kz[i,j,k], pressure[i,j,k+1], pressure[i,j,k-1],
                                composition[i,j,k+1,c], composition[i,j,k-1,c],
                                saturation[i,j,k]
                            )
                            
                            # Atualizar composição
                            composition[i,j,k,c] += dt * (qx + qy + qz) / (phi[i,j,k])
            
            # Armazenar resultados
            self.simulation_results[f'timestep_{t}'] = {
                'pressure': pressure.copy(),
                'temperature': temperature.copy(),
                'composition': composition.copy(),
                'saturation': saturation.copy()
            }
            
    def _run_thermal_simulation(self, timesteps: int, dt: float):
        """Executa simulação térmica."""
        nx, ny, nz = self.grid['nx'], self.grid['ny'], self.grid['nz']
        
        # Inicializar arrays
        pressure = np.zeros((nx, ny, nz))
        temperature = np.ones((nx, ny, nz)) * 180  # °F
        saturation = np.zeros((nx, ny, nz, 3))  # água, óleo, vapor
        
        # Propriedades do reservatório
        kx = self.grid['properties'].get('permeability_x', np.ones((nx, ny, nz)))
        ky = self.grid['properties'].get('permeability_y', np.ones((nx, ny, nz)))
        kz = self.grid['properties'].get('permeability_z', np.ones((nx, ny, nz)))
        phi = self.grid['properties'].get('porosity', np.ones((nx, ny, nz)) * 0.2)
        
        # Propriedades térmicas
        rock_heat_capacity = self.thermal_data['rock_heat_capacity']
        rock_thermal_conductivity = self.thermal_data['rock_thermal_conductivity']
        
        for t in range(timesteps):
            # Calcular fluxos de calor
            for i in range(1, nx-1):
                for j in range(1, ny-1):
                    for k in range(1, nz-1):
                        # Condução de calor
                        qx = rock_thermal_conductivity * (
                            temperature[i+1,j,k] - 2*temperature[i,j,k] + temperature[i-1,j,k]
                        ) / self.grid['dx']**2
                        qy = rock_thermal_conductivity * (
                            temperature[i,j+1,k] - 2*temperature[i,j,k] + temperature[i,j-1,k]
                        ) / self.grid['dy']**2
                        qz = rock_thermal_conductivity * (
                            temperature[i,j,k+1] - 2*temperature[i,j,k] + temperature[i,j,k-1]
                        ) / self.grid['dz']**2
                        
                        # Atualizar temperatura
                        temperature[i,j,k] += dt * (qx + qy + qz) / (rock_heat_capacity * phi[i,j,k])
                        
                        # Calcular saturações
                        if temperature[i,j,k] > 212:  # Ponto de ebulição da água
                            # Vaporização
                            saturation[i,j,k,0] *= 0.9  # Reduzir água
                            saturation[i,j,k,2] += 0.1  # Aumentar vapor
                        else:
                            # Condensação
                            saturation[i,j,k,0] += 0.1  # Aumentar água
                            saturation[i,j,k,2] *= 0.9  # Reduzir vapor
                        
                        # Normalizar saturações
                        total = np.sum(saturation[i,j,k])
                        saturation[i,j,k] /= total
            
            # Armazenar resultados
            self.simulation_results[f'timestep_{t}'] = {
                'pressure': pressure.copy(),
                'temperature': temperature.copy(),
                'saturation': saturation.copy()
            }
            
    def _calculate_k_values(self, z: np.ndarray, p: float, T: float) -> np.ndarray:
        """
        Calcula K-values usando EOS de Peng-Robinson.
        
        Args:
            z: Composição global
            p: Pressão (psia)
            T: Temperatura (°F)
            
        Returns:
            Array com K-values
        """
        # Parâmetros críticos dos componentes
        Tc = np.array([343, 550, 666, 765, 847])  # Temperaturas críticas (°R)
        Pc = np.array([667, 708, 551, 482, 397])  # Pressões críticas (psia)
        omega = np.array([0.011, 0.099, 0.152, 0.201, 0.251])  # Fator acêntrico
        
        # Converter temperatura para Rankine
        Tr = T + 460
        
        # Calcular parâmetros da EOS
        kappa = 0.37464 + 1.54226 * omega - 0.26992 * omega**2
        alpha = (1 + kappa * (1 - np.sqrt(Tr/Tc)))**2
        
        a = 0.45724 * alpha * Pc / Tc**2
        b = 0.07780 * Pc / Tc
        
        # Calcular parâmetros de mistura
        a_mix = 0
        b_mix = 0
        for i in range(len(z)):
            for j in range(len(z)):
                a_mix += z[i] * z[j] * np.sqrt(a[i] * a[j])
            b_mix += z[i] * b[i]
            
        # Calcular K-values
        K = np.exp(np.log(Pc/p) + 5.373 * (1 + omega) * (1 - Tc/Tr))
        
        return K
        
    def _flash_calculation(self, z: np.ndarray, K: np.ndarray) -> Tuple[float, np.ndarray, np.ndarray]:
        """
        Realiza flash calculation para determinar composições das fases.
        
        Args:
            z: Composição global
            K: K-values
            
        Returns:
            Tuple com (beta, x, y) onde:
            - beta é a fração molar da fase líquida
            - x é a composição da fase líquida
            - y é a composição da fase vapor
        """
        # Valores iniciais
        beta = 0.5  # Fração molar da fase líquida
        max_iter = 100
        tol = 1e-6
        
        for i in range(max_iter):
            # Calcular composições das fases
            x = z / (1 + beta * (K - 1))
            y = K * x
            
            # Normalizar
            x = x / np.sum(x)
            y = y / np.sum(y)
            
            # Calcular função objetivo
            f = np.sum(z * (K - 1) / (1 + beta * (K - 1)))
            
            # Verificar convergência
            if abs(f) < tol:
                break
                
            # Atualizar beta usando método de Newton
            df = -np.sum(z * (K - 1)**2 / (1 + beta * (K - 1))**2)
            beta = beta - f/df
            
            # Garantir que beta está entre 0 e 1
            beta = max(0, min(1, beta))
            
        return beta, x, y
        
    def _calculate_flux(self, k: float, p1: float, p2: float, c1: float, c2: float, s: np.ndarray) -> float:
        """
        Calcula fluxo entre células.
        
        Args:
            k: Permeabilidade (md)
            p1, p2: Pressões nas células (psia)
            c1, c2: Composições nas células
            s: Saturações na célula atual
            
        Returns:
            Fluxo entre as células
        """
        # Propriedades dos fluidos
        mu_o = 1.0  # Viscosidade do óleo (cp)
        mu_g = 0.02  # Viscosidade do gás (cp)
        rho_o = 45  # Densidade do óleo (lb/ft³)
        rho_g = 0.05  # Densidade do gás (lb/ft³)
        
        # Calcular mobilidades
        kr_o = s[0]**2  # Permeabilidade relativa do óleo
        kr_g = s[1]**2  # Permeabilidade relativa do gás
        
        lambda_o = kr_o / mu_o
        lambda_g = kr_g / mu_g
        
        # Calcular fluxo
        dp = p1 - p2
        dx = self.grid['dx']
        
        # Fluxo de óleo
        q_o = 0.00633 * k * lambda_o * dp / dx
        
        # Fluxo de gás
        q_g = 0.00633 * k * lambda_g * dp / dx
        
        # Fluxo total
        q = q_o + q_g
        
        return q
        
    def _run_black_oil_simulation(self, timesteps: int, dt: float):
        """Executa simulação black-oil."""
        # Implementar simulação black-oil
        pass
        
    def export_to_simulator(self, file_path: str):
        """
        Exporta modelo para formato do simulador.
        
        Args:
            file_path: Caminho do arquivo de saída
        """
        if self.simulator_type == 'tNavigator':
            self._export_to_tnavigator(file_path)
        elif self.simulator_type == 'Eclipse':
            self._export_to_eclipse(file_path)
        elif self.simulator_type == 'CMG':
            self._export_to_cmg(file_path)
        elif self.simulator_type == 'ECHELON':
            self._export_to_echelon(file_path)
        elif self.simulator_type == 'Nexus':
            self._export_to_nexus(file_path)
            
    def _export_to_tnavigator(self, file_path: str):
        """Exporta modelo para formato tNavigator."""
        # Implementar exportação para tNavigator
        pass
        
    def _export_to_eclipse(self, file_path: str):
        """Exporta modelo para formato Eclipse."""
        # Implementar exportação para Eclipse
        pass
        
    def _export_to_cmg(self, file_path: str):
        """Exporta modelo para formato CMG."""
        # Implementar exportação para CMG
        pass
        
    def _export_to_echelon(self, file_path: str):
        """Exporta modelo para formato ECHELON."""
        # Implementar exportação para ECHELON
        pass
        
    def _export_to_nexus(self, file_path: str):
        """Exporta modelo para formato Nexus."""
        # Implementar exportação para Nexus
        pass
        
    def plot_results(self, property_name: str, timestep: int):
        """
        Plota resultados da simulação.
        
        Args:
            property_name: Nome da propriedade
            timestep: Passo de tempo
        """
        if property_name not in self.simulation_results:
            raise ValueError(f"Propriedade {property_name} não encontrada")
            
        data = self.simulation_results[property_name][timestep]
        
        plt.figure(figsize=(10, 8))
        plt.imshow(data, cmap='viridis')
        plt.colorbar(label=property_name)
        plt.title(f'{property_name} - Timestep {timestep}')
        
        # Plotar poços
        for well_name, well in self.wells.items():
            for i, j, k in well['completion']:
                plt.plot(j, i, 'ro')
                plt.text(j, i, well_name)
                
        return plt.gcf() 