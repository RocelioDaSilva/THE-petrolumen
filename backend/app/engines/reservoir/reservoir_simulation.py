import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
import matplotlib.pyplot as plt
from scipy.special import exp1
from scipy.optimize import curve_fit
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import spsolve
import tensorflow as tf
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

class ReservoirSimulation:
    def __init__(self, model_type: str = 'black_oil'):
        """
        Inicializa o simulador de reservatÃ³rio.
        
        Args:
            model_type: Tipo do modelo ('black_oil', 'compositional', 'thermal')
        """
        self.model_type = model_type
        self.grid = None
        self.pvt_data = {}
        self.wells = {}
        self.initial_conditions = {}
        self.simulation_results = {}
        self.history_data = None
        self.gpu_available = tf.config.list_physical_devices('GPU')
        
    def create_grid(self,
                   nx: int,
                   ny: int,
                   nz: int,
                   dx: float,
                   dy: float,
                   dz: float,
                   grid_type: str = 'structured'):
        """
        Cria malha de simulaÃ§Ã£o.
        
        Args:
            nx, ny, nz: DimensÃµes da malha
            dx, dy, dz: Tamanho das cÃ©lulas
            grid_type: Tipo da malha ('structured', 'unstructured')
        """
        if grid_type == 'structured':
            self.grid = {
                'type': 'structured',
                'nx': nx,
                'ny': ny,
                'nz': nz,
                'dx': dx,
                'dy': dy,
                'dz': dz,
                'cells': nx * ny * nz,
                'x': np.arange(0, nx*dx, dx),
                'y': np.arange(0, ny*dy, dy),
                'z': np.arange(0, nz*dz, dz)
            }
        else:
            # Implementar malha nÃ£o estruturada
            pass
            
    def setup_pvt_model(self, pvt_data: Dict):
        """
        Configura modelo PVT.
        
        Args:
            pvt_data: Dados PVT
        """
        if self.model_type == 'black_oil':
            self._setup_black_oil_pvt(pvt_data)
        elif self.model_type == 'compositional':
            self._setup_compositional_pvt(pvt_data)
        elif self.model_type == 'thermal':
            self._setup_thermal_pvt(pvt_data)
            
    def _setup_black_oil_pvt(self, pvt_data: Dict):
        """Configura modelo PVT black-oil."""
        # Interpolar dados PVT
        self.pvt_data = {
            'pressure': pvt_data['pressure'],
            'rs': np.interp(pvt_data['pressure'], pvt_data['rs_p'], pvt_data['rs']),
            'bo': np.interp(pvt_data['pressure'], pvt_data['bo_p'], pvt_data['bo']),
            'bg': np.interp(pvt_data['pressure'], pvt_data['bg_p'], pvt_data['bg']),
            'bw': np.interp(pvt_data['pressure'], pvt_data['bw_p'], pvt_data['bw']),
            'muo': np.interp(pvt_data['pressure'], pvt_data['muo_p'], pvt_data['muo']),
            'mug': np.interp(pvt_data['pressure'], pvt_data['mug_p'], pvt_data['mug']),
            'muw': np.interp(pvt_data['pressure'], pvt_data['muw_p'], pvt_data['muw'])
        }
        
    def _setup_compositional_pvt(self, pvt_data: Dict):
        """Configura modelo PVT composicional."""
        # Configurar EOS
        self.pvt_data = {
            'components': pvt_data['components'],
            'critical_pressure': pvt_data['critical_pressure'],
            'critical_temperature': pvt_data['critical_temperature'],
            'acentric_factor': pvt_data['acentric_factor'],
            'molecular_weight': pvt_data['molecular_weight'],
            'binary_interaction': pvt_data['binary_interaction']
        }
        
    def _setup_thermal_pvt(self, pvt_data: Dict):
        """Configura modelo PVT tÃ©rmico."""
        self.pvt_data = {
            'temperature': pvt_data['temperature'],
            'pressure': pvt_data['pressure'],
            'oil_viscosity': pvt_data['oil_viscosity'],
            'water_viscosity': pvt_data['water_viscosity'],
            'steam_viscosity': pvt_data['steam_viscosity'],
            'oil_density': pvt_data['oil_density'],
            'water_density': pvt_data['water_density'],
            'steam_density': pvt_data['steam_density'],
            'oil_heat_capacity': pvt_data['oil_heat_capacity'],
            'water_heat_capacity': pvt_data['water_heat_capacity'],
            'steam_heat_capacity': pvt_data['steam_heat_capacity'],
            'rock_heat_capacity': pvt_data['rock_heat_capacity'],
            'rock_thermal_conductivity': pvt_data['rock_thermal_conductivity']
        }
        
    def add_well(self,
                well_name: str,
                well_type: str,
                completion: List[Tuple[int, int, int]],
                constraints: Dict):
        """
        Adiciona poÃ§o ao modelo.
        
        Args:
            well_name: Nome do poÃ§o
            well_type: Tipo do poÃ§o ('producer', 'injector')
            completion: Lista de cÃ©lulas de completaÃ§Ã£o
            constraints: RestriÃ§Ãµes do poÃ§o
        """
        self.wells[well_name] = {
            'type': well_type,
            'completion': completion,
            'constraints': constraints
        }
        
    def set_initial_conditions(self,
                             pressure: float,
                             temperature: float,
                             saturations: Dict[str, float]):
        """
        Define condiÃ§Ãµes iniciais.
        
        Args:
            pressure: PressÃ£o inicial
            temperature: Temperatura inicial
            saturations: SaturaÃ§Ãµes iniciais
        """
        self.initial_conditions = {
            'pressure': pressure,
            'temperature': temperature,
            'saturations': saturations
        }
        
    def run_simulation(self,
                      timesteps: int,
                      dt: float,
                      use_gpu: bool = False):
        """
        Executa simulaÃ§Ã£o.
        
        Args:
            timesteps: NÃºmero de passos de tempo
            dt: Tamanho do passo de tempo
            use_gpu: Usar GPU para simulaÃ§Ã£o
        """
        if use_gpu and self.gpu_available:
            self._run_gpu_simulation(timesteps, dt)
        else:
            if self.model_type == 'black_oil':
                self._run_black_oil_simulation(timesteps, dt)
            elif self.model_type == 'compositional':
                self._run_compositional_simulation(timesteps, dt)
            elif self.model_type == 'thermal':
                self._run_thermal_simulation(timesteps, dt)
                
    def _run_black_oil_simulation(self, timesteps: int, dt: float):
        """Executa simulaÃ§Ã£o black-oil."""
        nx, ny, nz = self.grid['nx'], self.grid['ny'], self.grid['nz']
        cells = self.grid['cells']
        
        # Inicializar arrays
        pressure = np.ones(cells) * self.initial_conditions['pressure']
        sw = np.ones(cells) * self.initial_conditions['saturations']['water']
        so = np.ones(cells) * self.initial_conditions['saturations']['oil']
        sg = np.ones(cells) * self.initial_conditions['saturations']['gas']
        
        # Propriedades do reservatÃ³rio
        kx = np.ones(cells) * 100  # md
        ky = np.ones(cells) * 100
        kz = np.ones(cells) * 10
        phi = np.ones(cells) * 0.2
        
        # Armazenar resultados
        self.simulation_results = {
            'pressure': np.zeros((timesteps, cells)),
            'sw': np.zeros((timesteps, cells)),
            'so': np.zeros((timesteps, cells)),
            'sg': np.zeros((timesteps, cells)),
            'time': np.zeros(timesteps)
        }
        
        # Loop temporal
        for t in range(timesteps):
            # Construir matriz de coeficientes
            A = self._build_black_oil_matrix(pressure, sw, so, sg, kx, ky, kz, phi)
            b = self._build_black_oil_rhs(pressure, sw, so, sg, dt)
            
            # Resolver sistema linear
            dp = spsolve(A, b)
            pressure += dp
            
            # Atualizar saturaÃ§Ãµes
            sw, so, sg = self._update_saturations(pressure, sw, so, sg, dt)
            
            # Armazenar resultados
            self.simulation_results['pressure'][t] = pressure
            self.simulation_results['sw'][t] = sw
            self.simulation_results['so'][t] = so
            self.simulation_results['sg'][t] = sg
            self.simulation_results['time'][t] = (t + 1) * dt
            
    def _run_compositional_simulation(self, timesteps: int, dt: float):
        """Executa simulaÃ§Ã£o composicional."""
        nx, ny, nz = self.grid['nx'], self.grid['ny'], self.grid['nz']
        cells = self.grid['cells']
        components = self.pvt_data['components']
        nc = len(components)
        
        # Inicializar arrays
        pressure = np.ones(cells) * self.initial_conditions['pressure']
        temperature = np.ones(cells) * self.initial_conditions['temperature']
        composition = np.zeros((cells, nc))
        saturation = np.zeros((cells, 2))  # Ã³leo e gÃ¡s
        
        # Propriedades do reservatÃ³rio
        kx = np.ones(cells) * 100  # md
        ky = np.ones(cells) * 100
        kz = np.ones(cells) * 10
        phi = np.ones(cells) * 0.2
        
        # Armazenar resultados
        self.simulation_results = {
            'pressure': np.zeros((timesteps, cells)),
            'temperature': np.zeros((timesteps, cells)),
            'composition': np.zeros((timesteps, cells, nc)),
            'saturation': np.zeros((timesteps, cells, 2)),
            'time': np.zeros(timesteps)
        }
        
        # Loop temporal
        for t in range(timesteps):
            # Calcular equilÃ­brio de fases
            for i in range(cells):
                # Flash calculation usando EOS
                z = composition[i]
                p = pressure[i]
                T = temperature[i]
                
                # Calcular K-values
                K = self._calculate_k_values(z, p, T)
                
                # Flash calculation
                beta, x, y = self._flash_calculation(z, K)
                
                # Atualizar composiÃ§Ãµes e saturaÃ§Ãµes
                composition[i] = z
                saturation[i,0] = beta  # saturaÃ§Ã£o de Ã³leo
                saturation[i,1] = 1 - beta  # saturaÃ§Ã£o de gÃ¡s
            
            # Construir matriz de coeficientes
            A = self._build_compositional_matrix(pressure, temperature, composition, saturation)
            b = self._build_compositional_rhs(pressure, temperature, composition, saturation, dt)
            
            # Resolver sistema linear
            dx = spsolve(A, b)
            
            # Atualizar variÃ¡veis
            pressure += dx[:cells]
            temperature += dx[cells:2*cells]
            composition += dx[2*cells:].reshape(cells, nc)
            
            # Armazenar resultados
            self.simulation_results['pressure'][t] = pressure
            self.simulation_results['temperature'][t] = temperature
            self.simulation_results['composition'][t] = composition
            self.simulation_results['saturation'][t] = saturation
            self.simulation_results['time'][t] = (t + 1) * dt
            
    def _run_thermal_simulation(self, timesteps: int, dt: float):
        """Executa simulaÃ§Ã£o tÃ©rmica."""
        nx, ny, nz = self.grid['nx'], self.grid['ny'], self.grid['nz']
        cells = self.grid['cells']
        
        # Inicializar arrays
        pressure = np.ones(cells) * self.initial_conditions['pressure']
        temperature = np.ones(cells) * self.initial_conditions['temperature']
        saturation = np.zeros((cells, 3))  # Ã¡gua, Ã³leo, vapor
        
        # Propriedades do reservatÃ³rio
        kx = np.ones(cells) * 100  # md
        ky = np.ones(cells) * 100
        kz = np.ones(cells) * 10
        phi = np.ones(cells) * 0.2
        
        # Propriedades tÃ©rmicas
        rock_heat_capacity = self.pvt_data['rock_heat_capacity']
        rock_thermal_conductivity = self.pvt_data['rock_thermal_conductivity']
        
        # Armazenar resultados
        self.simulation_results = {
            'pressure': np.zeros((timesteps, cells)),
            'temperature': np.zeros((timesteps, cells)),
            'saturation': np.zeros((timesteps, cells, 3)),
            'time': np.zeros(timesteps)
        }
        
        # Loop temporal
        for t in range(timesteps):
            # Calcular fluxos de calor
            for i in range(cells):
                # ConduÃ§Ã£o de calor
                qx = rock_thermal_conductivity * (
                    temperature[i+1] - 2*temperature[i] + temperature[i-1]
                ) / self.grid['dx']**2
                qy = rock_thermal_conductivity * (
                    temperature[i+nx] - 2*temperature[i] + temperature[i-nx]
                ) / self.grid['dy']**2
                qz = rock_thermal_conductivity * (
                    temperature[i+nx*ny] - 2*temperature[i] + temperature[i-nx*ny]
                ) / self.grid['dz']**2
                
                # Atualizar temperatura
                temperature[i] += dt * (qx + qy + qz) / (rock_heat_capacity * phi[i])
                
                # Calcular saturaÃ§Ãµes
                if temperature[i] > 212:  # Ponto de ebuliÃ§Ã£o da Ã¡gua
                    # VaporizaÃ§Ã£o
                    saturation[i,0] *= 0.9  # Reduzir Ã¡gua
                    saturation[i,2] += 0.1  # Aumentar vapor
                else:
                    # CondensaÃ§Ã£o
                    saturation[i,0] += 0.1  # Aumentar Ã¡gua
                    saturation[i,2] *= 0.9  # Reduzir vapor
                
                # Normalizar saturaÃ§Ãµes
                total = np.sum(saturation[i])
                saturation[i] /= total
            
            # Construir matriz de coeficientes
            A = self._build_thermal_matrix(pressure, temperature, saturation)
            b = self._build_thermal_rhs(pressure, temperature, saturation, dt)
            
            # Resolver sistema linear
            dx = spsolve(A, b)
            
            # Atualizar variÃ¡veis
            pressure += dx[:cells]
            temperature += dx[cells:2*cells]
            saturation += dx[2*cells:].reshape(cells, 3)
            
            # Armazenar resultados
            self.simulation_results['pressure'][t] = pressure
            self.simulation_results['temperature'][t] = temperature
            self.simulation_results['saturation'][t] = saturation
            self.simulation_results['time'][t] = (t + 1) * dt
            
    def _run_gpu_simulation(self, timesteps: int, dt: float):
        """Executa simulaÃ§Ã£o usando GPU."""
        # Converter dados para tensores
        if self.model_type == 'black_oil':
            pressure = tf.convert_to_tensor(self.initial_conditions['pressure'])
            sw = tf.convert_to_tensor(self.initial_conditions['saturations']['water'])
            so = tf.convert_to_tensor(self.initial_conditions['saturations']['oil'])
            sg = tf.convert_to_tensor(self.initial_conditions['saturations']['gas'])
            
            # Propriedades do reservatÃ³rio
            kx = tf.convert_to_tensor(np.ones(self.grid['cells']) * 100)
            ky = tf.convert_to_tensor(np.ones(self.grid['cells']) * 100)
            kz = tf.convert_to_tensor(np.ones(self.grid['cells']) * 10)
            phi = tf.convert_to_tensor(np.ones(self.grid['cells']) * 0.2)
            
            # Loop temporal
            for t in range(timesteps):
                # Calcular fluxos
                qx = self._calculate_flux_gpu(pressure, kx, self.grid['dx'])
                qy = self._calculate_flux_gpu(pressure, ky, self.grid['dy'])
                qz = self._calculate_flux_gpu(pressure, kz, self.grid['dz'])
                
                # Atualizar pressÃ£o
                pressure += dt * (qx + qy + qz) / phi
                
                # Atualizar saturaÃ§Ãµes
                sw, so, sg = self._update_saturations_gpu(pressure, sw, so, sg, dt)
                
                # Armazenar resultados
                self.simulation_results['pressure'][t] = pressure.numpy()
                self.simulation_results['sw'][t] = sw.numpy()
                self.simulation_results['so'][t] = so.numpy()
                self.simulation_results['sg'][t] = sg.numpy()
                self.simulation_results['time'][t] = (t + 1) * dt
                
    def history_matching(self,
                        history_data: pd.DataFrame,
                        parameters: List[str],
                        bounds: Dict[str, Tuple[float, float]]):
        """
        Realiza ajuste de histÃ³rico.
        
        Args:
            history_data: Dados histÃ³ricos
            parameters: Lista de parÃ¢metros a ajustar
            bounds: Limites dos parÃ¢metros
        """
        self.history_data = history_data
        
        # Preparar dados
        X = history_data[parameters].values
        y = history_data['target'].values
        
        # Dividir dados
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        # Treinar modelo
        model = RandomForestRegressor(n_estimators=100)
        model.fit(X_train, y_train)
        
        # Avaliar modelo
        score = model.score(X_test, y_test)
        print(f"RÂ² score: {score:.3f}")
        
        # Otimizar parÃ¢metros
        best_params = {}
        for param in parameters:
            param_range = np.linspace(bounds[param][0], bounds[param][1], 100)
            scores = []
            for value in param_range:
                X_test_copy = X_test.copy()
                X_test_copy[:, parameters.index(param)] = value
                score = model.score(X_test_copy, y_test)
                scores.append(score)
            best_params[param] = param_range[np.argmax(scores)]
            
        return best_params
        
    def plot_results(self,
                    property_name: str,
                    timestep: int = -1,
                    well_name: Optional[str] = None):
        """
        Plota resultados da simulaÃ§Ã£o.
        
        Args:
            property_name: Nome da propriedade
            timestep: Passo de tempo
            well_name: Nome do poÃ§o
        """
        if well_name is not None:
            # Plotar histÃ³rico do poÃ§o
            well_data = self.simulation_results[property_name][:, self.wells[well_name]['completion']]
            time = self.simulation_results['time']
            
            plt.figure(figsize=(10, 6))
            plt.plot(time, well_data)
            plt.xlabel('Time')
            plt.ylabel(property_name)
            plt.title(f'{property_name} - {well_name}')
            plt.grid(True)
            
        else:
            # Plotar mapa 2D
            data = self.simulation_results[property_name][timestep].reshape(
                self.grid['nx'], self.grid['ny']
            )
            
            plt.figure(figsize=(10, 8))
            plt.imshow(data, cmap='viridis')
            plt.colorbar(label=property_name)
            plt.title(f'{property_name} - Timestep {timestep}')
            
            # Plotar poÃ§os
            for well_name, well in self.wells.items():
                for i, j, k in well['completion']:
                    plt.plot(j, i, 'ro')
                    plt.text(j, i, well_name)
                    
        return plt.gcf()

    def _build_black_oil_matrix(self,
                              pressure: np.ndarray,
                              sw: np.ndarray,
                              so: np.ndarray,
                              sg: np.ndarray,
                              kx: np.ndarray,
                              ky: np.ndarray,
                              kz: np.ndarray,
                              phi: np.ndarray) -> csr_matrix:
        """ConstrÃ³i matriz de coeficientes para simulaÃ§Ã£o black-oil."""
        nx, ny, nz = self.grid['nx'], self.grid['ny'], self.grid['nz']
        cells = self.grid['cells']
        
        # Propriedades dos fluidos
        mu_o = self.pvt_data['muo']
        mu_w = self.pvt_data['muw']
        mu_g = self.pvt_data['mug']
        bo = self.pvt_data['bo']
        bw = self.pvt_data['bw']
        bg = self.pvt_data['bg']
        
        # Calcular mobilidades
        krw = sw**2
        kro = so**2
        krg = sg**2
        
        lambda_w = krw / (mu_w * bw)
        lambda_o = kro / (mu_o * bo)
        lambda_g = krg / (mu_g * bg)
        lambda_t = lambda_w + lambda_o + lambda_g
        
        # Construir matriz esparsa
        rows = []
        cols = []
        data = []
        
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    idx = i + j*nx + k*nx*ny
                    
                    # Termos de transmissibilidade
                    if i > 0:
                        tx = 0.00633 * kx[idx] * self.grid['dy'] * self.grid['dz'] / self.grid['dx']
                        rows.append(idx)
                        cols.append(idx-1)
                        data.append(-tx * lambda_t[idx])
                        
                    if i < nx-1:
                        tx = 0.00633 * kx[idx] * self.grid['dy'] * self.grid['dz'] / self.grid['dx']
                        rows.append(idx)
                        cols.append(idx+1)
                        data.append(-tx * lambda_t[idx])
                        
                    if j > 0:
                        ty = 0.00633 * ky[idx] * self.grid['dx'] * self.grid['dz'] / self.grid['dy']
                        rows.append(idx)
                        cols.append(idx-nx)
                        data.append(-ty * lambda_t[idx])
                        
                    if j < ny-1:
                        ty = 0.00633 * ky[idx] * self.grid['dx'] * self.grid['dz'] / self.grid['dy']
                        rows.append(idx)
                        cols.append(idx+nx)
                        data.append(-ty * lambda_t[idx])
                        
                    if k > 0:
                        tz = 0.00633 * kz[idx] * self.grid['dx'] * self.grid['dy'] / self.grid['dz']
                        rows.append(idx)
                        cols.append(idx-nx*ny)
                        data.append(-tz * lambda_t[idx])
                        
                    if k < nz-1:
                        tz = 0.00633 * kz[idx] * self.grid['dx'] * self.grid['dy'] / self.grid['dz']
                        rows.append(idx)
                        cols.append(idx+nx*ny)
                        data.append(-tz * lambda_t[idx])
                        
                    # Diagonal principal
                    rows.append(idx)
                    cols.append(idx)
                    data.append(phi[idx] / dt)
                    
        return csr_matrix((data, (rows, cols)), shape=(cells, cells))
        
    def _build_black_oil_rhs(self,
                            pressure: np.ndarray,
                            sw: np.ndarray,
                            so: np.ndarray,
                            sg: np.ndarray,
                            dt: float) -> np.ndarray:
        """ConstrÃ³i vetor de termos independentes para simulaÃ§Ã£o black-oil."""
        cells = self.grid['cells']
        b = np.zeros(cells)
        
        # Adicionar termos fonte (poÃ§os)
        for well_name, well in self.wells.items():
            for i, j, k in well['completion']:
                idx = i + j*self.grid['nx'] + k*self.grid['nx']*self.grid['ny']
                if well['type'] == 'producer':
                    b[idx] = -well['constraints']['rate']
                else:
                    b[idx] = well['constraints']['rate']
                    
        return b
        
    def _update_saturations(self,
                          pressure: np.ndarray,
                          sw: np.ndarray,
                          so: np.ndarray,
                          sg: np.ndarray,
                          dt: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Atualiza saturaÃ§Ãµes para simulaÃ§Ã£o black-oil."""
        # Calcular mobilidades
        krw = sw**2
        kro = so**2
        krg = sg**2
        
        mu_w = self.pvt_data['muw']
        mu_o = self.pvt_data['muo']
        mu_g = self.pvt_data['mug']
        
        lambda_w = krw / mu_w
        lambda_o = kro / mu_o
        lambda_g = krg / mu_g
        lambda_t = lambda_w + lambda_o + lambda_g
        
        # Atualizar saturaÃ§Ãµes
        sw_new = sw + dt * lambda_w / lambda_t
        so_new = so + dt * lambda_o / lambda_t
        sg_new = 1 - sw_new - so_new
        
        return sw_new, so_new, sg_new
        
    def _build_compositional_matrix(self,
                                  pressure: np.ndarray,
                                  temperature: np.ndarray,
                                  composition: np.ndarray,
                                  saturation: np.ndarray) -> csr_matrix:
        """ConstrÃ³i matriz de coeficientes para simulaÃ§Ã£o composicional."""
        nx, ny, nz = self.grid['nx'], self.grid['ny'], self.grid['nz']
        cells = self.grid['cells']
        nc = composition.shape[1]
        
        # Propriedades do reservatÃ³rio
        kx = np.ones(cells) * 100  # md
        ky = np.ones(cells) * 100
        kz = np.ones(cells) * 10
        phi = np.ones(cells) * 0.2
        
        # Construir matriz esparsa
        rows = []
        cols = []
        data = []
        
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    idx = i + j*nx + k*nx*ny
                    
                    # Termos de transmissibilidade
                    if i > 0:
                        tx = 0.00633 * kx[idx] * self.grid['dy'] * self.grid['dz'] / self.grid['dx']
                        rows.append(idx)
                        cols.append(idx-1)
                        data.append(-tx)
                        
                    if i < nx-1:
                        tx = 0.00633 * kx[idx] * self.grid['dy'] * self.grid['dz'] / self.grid['dx']
                        rows.append(idx)
                        cols.append(idx+1)
                        data.append(-tx)
                        
                    if j > 0:
                        ty = 0.00633 * ky[idx] * self.grid['dx'] * self.grid['dz'] / self.grid['dy']
                        rows.append(idx)
                        cols.append(idx-nx)
                        data.append(-ty)
                        
                    if j < ny-1:
                        ty = 0.00633 * ky[idx] * self.grid['dx'] * self.grid['dz'] / self.grid['dy']
                        rows.append(idx)
                        cols.append(idx+nx)
                        data.append(-ty)
                        
                    if k > 0:
                        tz = 0.00633 * kz[idx] * self.grid['dx'] * self.grid['dy'] / self.grid['dz']
                        rows.append(idx)
                        cols.append(idx-nx*ny)
                        data.append(-tz)
                        
                    if k < nz-1:
                        tz = 0.00633 * kz[idx] * self.grid['dx'] * self.grid['dy'] / self.grid['dz']
                        rows.append(idx)
                        cols.append(idx+nx*ny)
                        data.append(-tz)
                        
                    # Diagonal principal
                    rows.append(idx)
                    cols.append(idx)
                    data.append(phi[idx])
                    
        return csr_matrix((data, (rows, cols)), shape=(cells, cells))
        
    def _build_compositional_rhs(self,
                               pressure: np.ndarray,
                               temperature: np.ndarray,
                               composition: np.ndarray,
                               saturation: np.ndarray,
                               dt: float) -> np.ndarray:
        """ConstrÃ³i vetor de termos independentes para simulaÃ§Ã£o composicional."""
        cells = self.grid['cells']
        nc = composition.shape[1]
        b = np.zeros(cells * (2 + nc))
        
        # Adicionar termos fonte (poÃ§os)
        for well_name, well in self.wells.items():
            for i, j, k in well['completion']:
                idx = i + j*self.grid['nx'] + k*self.grid['nx']*self.grid['ny']
                if well['type'] == 'producer':
                    b[idx] = -well['constraints']['rate']
                else:
                    b[idx] = well['constraints']['rate']
                    
        return b
        
    def _build_thermal_matrix(self,
                            pressure: np.ndarray,
                            temperature: np.ndarray,
                            saturation: np.ndarray) -> csr_matrix:
        """ConstrÃ³i matriz de coeficientes para simulaÃ§Ã£o tÃ©rmica."""
        nx, ny, nz = self.grid['nx'], self.grid['ny'], self.grid['nz']
        cells = self.grid['cells']
        
        # Propriedades tÃ©rmicas
        rock_thermal_conductivity = self.pvt_data['rock_thermal_conductivity']
        
        # Construir matriz esparsa
        rows = []
        cols = []
        data = []
        
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    idx = i + j*nx + k*nx*ny
                    
                    # Termos de conduÃ§Ã£o de calor
                    if i > 0:
                        tx = rock_thermal_conductivity * self.grid['dy'] * self.grid['dz'] / self.grid['dx']
                        rows.append(idx)
                        cols.append(idx-1)
                        data.append(-tx)
                        
                    if i < nx-1:
                        tx = rock_thermal_conductivity * self.grid['dy'] * self.grid['dz'] / self.grid['dx']
                        rows.append(idx)
                        cols.append(idx+1)
                        data.append(-tx)
                        
                    if j > 0:
                        ty = rock_thermal_conductivity * self.grid['dx'] * self.grid['dz'] / self.grid['dy']
                        rows.append(idx)
                        cols.append(idx-nx)
                        data.append(-ty)
                        
                    if j < ny-1:
                        ty = rock_thermal_conductivity * self.grid['dx'] * self.grid['dz'] / self.grid['dy']
                        rows.append(idx)
                        cols.append(idx+nx)
                        data.append(-ty)
                        
                    if k > 0:
                        tz = rock_thermal_conductivity * self.grid['dx'] * self.grid['dy'] / self.grid['dz']
                        rows.append(idx)
                        cols.append(idx-nx*ny)
                        data.append(-tz)
                        
                    if k < nz-1:
                        tz = rock_thermal_conductivity * self.grid['dx'] * self.grid['dy'] / self.grid['dz']
                        rows.append(idx)
                        cols.append(idx+nx*ny)
                        data.append(-tz)
                        
                    # Diagonal principal
                    rows.append(idx)
                    cols.append(idx)
                    data.append(1.0)
                    
        return csr_matrix((data, (rows, cols)), shape=(cells, cells))
        
    def _build_thermal_rhs(self,
                          pressure: np.ndarray,
                          temperature: np.ndarray,
                          saturation: np.ndarray,
                          dt: float) -> np.ndarray:
        """ConstrÃ³i vetor de termos independentes para simulaÃ§Ã£o tÃ©rmica."""
        cells = self.grid['cells']
        b = np.zeros(cells * 3)  # pressÃ£o, temperatura, saturaÃ§Ãµes
        
        # Adicionar termos fonte (poÃ§os)
        for well_name, well in self.wells.items():
            for i, j, k in well['completion']:
                idx = i + j*self.grid['nx'] + k*self.grid['nx']*self.grid['ny']
                if well['type'] == 'producer':
                    b[idx] = -well['constraints']['rate']
                else:
                    b[idx] = well['constraints']['rate']
                    
        return b
        
    def _calculate_flux_gpu(self,
                          pressure: tf.Tensor,
                          k: tf.Tensor,
                          dx: float) -> tf.Tensor:
        """Calcula fluxo usando GPU."""
        # Calcular gradiente de pressÃ£o
        dp = tf.pad(pressure[1:] - pressure[:-1], [[0, 1]])
        
        # Calcular fluxo
        q = -0.00633 * k * dp / dx
        
        return q
        
    def _update_saturations_gpu(self,
                              pressure: tf.Tensor,
                              sw: tf.Tensor,
                              so: tf.Tensor,
                              sg: tf.Tensor,
                              dt: float) -> Tuple[tf.Tensor, tf.Tensor, tf.Tensor]:
        """Atualiza saturaÃ§Ãµes usando GPU."""
        # Calcular mobilidades
        krw = tf.square(sw)
        kro = tf.square(so)
        krg = tf.square(sg)
        
        mu_w = tf.constant(self.pvt_data['muw'])
        mu_o = tf.constant(self.pvt_data['muo'])
        mu_g = tf.constant(self.pvt_data['mug'])
        
        lambda_w = krw / mu_w
        lambda_o = kro / mu_o
        lambda_g = krg / mu_g
        lambda_t = lambda_w + lambda_o + lambda_g
        
        # Atualizar saturaÃ§Ãµes
        sw_new = sw + dt * lambda_w / lambda_t
        so_new = so + dt * lambda_o / lambda_t
        sg_new = 1 - sw_new - so_new
        
        return sw_new, so_new, sg_new
        
    def _calculate_k_values(self,
                          z: np.ndarray,
                          p: float,
                          T: float) -> np.ndarray:
        """
        Calcula K-values usando EOS de Peng-Robinson.
        
        Args:
            z: ComposiÃ§Ã£o global
            p: PressÃ£o (psia)
            T: Temperatura (Â°R)
            
        Returns:
            Array com K-values
        """
        # ParÃ¢metros crÃ­ticos
        pc = self.pvt_data['critical_pressure']
        Tc = self.pvt_data['critical_temperature']
        omega = self.pvt_data['acentric_factor']
        
        # Constantes
        R = 10.73  # Constante dos gases (psia.ftÂ³/lbmol.Â°R)
        
        # Calcular parÃ¢metros da EOS
        kappa = 0.37464 + 1.54226*omega - 0.26992*omega**2
        alpha = (1 + kappa*(1 - np.sqrt(T/Tc)))**2
        
        a = 0.45724 * R**2 * Tc**2 * alpha / pc
        b = 0.07780 * R * Tc / pc
        
        # Calcular parÃ¢metros de mistura
        a_mix = 0
        b_mix = 0
        for i in range(len(z)):
            for j in range(len(z)):
                a_mix += z[i]*z[j]*np.sqrt(a[i]*a[j])*(1 - self.pvt_data['binary_interaction'][i,j])
            b_mix += z[i]*b[i]
            
        # Calcular K-values
        K = np.zeros_like(z)
        for i in range(len(z)):
            # Calcular fugacidade
            A = a_mix*p/(R**2*T**2)
            B = b_mix*p/(R*T)
            
            # Coeficientes da equaÃ§Ã£o cÃºbica
            c2 = B - 1
            c1 = A - 2*B - 3*B**2
            c0 = -A*B + B**2 + B**3
            
            # Resolver equaÃ§Ã£o cÃºbica
            roots = np.roots([1, c2, c1, c0])
            Z = np.max(roots[roots.imag == 0].real)
            
            # Calcular fugacidade
            ln_phi = (Z - 1) - np.log(Z - B) - A/(2*np.sqrt(2)*B)*np.log((Z + (1 + np.sqrt(2))*B)/(Z + (1 - np.sqrt(2))*B))
            
            # Calcular K-value
            K[i] = np.exp(ln_phi)
            
        return K
        
    def _flash_calculation(self,
                          z: np.ndarray,
                          K: np.ndarray,
                          tol: float = 1e-6,
                          max_iter: int = 100) -> Tuple[float, np.ndarray, np.ndarray]:
        """
        Realiza cÃ¡lculo de flash.
        
        Args:
            z: ComposiÃ§Ã£o global
            K: K-values
            tol: TolerÃ¢ncia para convergÃªncia
            max_iter: NÃºmero mÃ¡ximo de iteraÃ§Ãµes
            
        Returns:
            Tuple com fraÃ§Ã£o molar da fase lÃ­quida (beta),
            composiÃ§Ã£o da fase lÃ­quida (x) e composiÃ§Ã£o da fase vapor (y)
        """
        # Valores iniciais
        beta = 0.5  # FraÃ§Ã£o molar da fase lÃ­quida
        x = z.copy()  # ComposiÃ§Ã£o da fase lÃ­quida
        y = K * x  # ComposiÃ§Ã£o da fase vapor
        
        # IteraÃ§Ã£o de Rachford-Rice
        for i in range(max_iter):
            # Calcular funÃ§Ã£o objetivo
            f = np.sum(z * (K - 1) / (1 + beta * (K - 1)))
            
            # Calcular derivada
            df = -np.sum(z * (K - 1)**2 / (1 + beta * (K - 1))**2)
            
            # Atualizar beta
            beta_new = beta - f/df
            
            # Verificar convergÃªncia
            if abs(beta_new - beta) < tol:
                break
                
            beta = beta_new
            
            # Atualizar composiÃ§Ãµes
            x = z / (1 + beta * (K - 1))
            y = K * x
            
            # Normalizar
            x = x / np.sum(x)
            y = y / np.sum(y)
            
        return beta, x, y
        
    def _calculate_flux(self,
                       k: np.ndarray,
                       p1: float,
                       p2: float,
                       c1: np.ndarray,
                       c2: np.ndarray,
                       s: np.ndarray) -> float:
        """
        Calcula fluxo entre cÃ©lulas.
        
        Args:
            k: Permeabilidade
            p1, p2: PressÃµes nas cÃ©lulas
            c1, c2: ComposiÃ§Ãµes nas cÃ©lulas
            s: SaturaÃ§Ãµes
            
        Returns:
            Fluxo entre as cÃ©lulas
        """
        # Propriedades dos fluidos
        mu_o = self.pvt_data['muo']
        mu_w = self.pvt_data['muw']
        mu_g = self.pvt_data['mug']
        
        # Calcular mobilidades
        krw = s[0]**2
        kro = s[1]**2
        krg = s[2]**2
        
        lambda_w = krw / mu_w
        lambda_o = kro / mu_o
        lambda_g = krg / mu_g
        lambda_t = lambda_w + lambda_o + lambda_g
        
        # Calcular fluxo
        q = -0.00633 * k * lambda_t * (p2 - p1)
        
        return q 
