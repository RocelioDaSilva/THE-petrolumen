import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
from scipy.optimize import curve_fit
import scipy.signal

class StaticModeling:
    def __init__(self):
        """Inicializa o módulo de modelagem estática."""
        self.grid = None
        self.well_data = {}
        self.seismic_data = None
        self.maps = {}
        self.properties = {}
        self.variograms = {}
        self.nmr_data = {}
        
    def create_3d_grid(self,
                      nx: int,
                      ny: int,
                      nz: int,
                      dx: float,
                      dy: float,
                      dz: float):
        """
        Cria malha 3D para modelagem.
        
        Args:
            nx, ny, nz: Dimensões da malha
            dx, dy, dz: Tamanho das células
        """
        self.grid = {
            'nx': nx,
            'ny': ny,
            'nz': nz,
            'dx': dx,
            'dy': dy,
            'dz': dz,
            'x': np.arange(0, nx*dx, dx),
            'y': np.arange(0, ny*dy, dy),
            'z': np.arange(0, nz*dz, dz)
        }
        
    def add_well_data(self,
                     well_name: str,
                     x: float,
                     y: float,
                     md: np.ndarray,
                     properties: Dict[str, np.ndarray]):
        """
        Adiciona dados de poço.
        
        Args:
            well_name: Nome do poço
            x, y: Coordenadas do poço
            md: Medidas de profundidade
            properties: Dicionário com propriedades
        """
        self.well_data[well_name] = {
            'x': x,
            'y': y,
            'md': md,
            'properties': properties
        }
        
    def add_seismic_data(self,
                        seismic_cube: np.ndarray,
                        x0: float,
                        y0: float,
                        dx: float,
                        dy: float):
        """
        Adiciona dados sísmicos.
        
        Args:
            seismic_cube: Cubo sísmico 3D
            x0, y0: Coordenadas de origem
            dx, dy: Resolução espacial
        """
        self.seismic_data = {
            'data': seismic_cube,
            'x0': x0,
            'y0': y0,
            'dx': dx,
            'dy': dy
        }
        
    def add_map(self,
               map_name: str,
               data: np.ndarray,
               x0: float,
               y0: float,
               dx: float,
               dy: float):
        """
        Adiciona mapa 2D.
        
        Args:
            map_name: Nome do mapa
            data: Dados do mapa
            x0, y0: Coordenadas de origem
            dx, dy: Resolução espacial
        """
        self.maps[map_name] = {
            'data': data,
            'x0': x0,
            'y0': y0,
            'dx': dx,
            'dy': dy
        }
        
    def calculate_variogram(self,
                          property_name: str,
                          direction: str = 'omnidirectional',
                          max_lag: float = None,
                          n_lags: int = 10):
        """
        Calcula variograma experimental.
        
        Args:
            property_name: Nome da propriedade
            direction: Direção do variograma
            max_lag: Distância máxima
            n_lags: Número de lags
        """
        # Coletar dados
        data = []
        locations = []
        for well_name, well in self.well_data.items():
            data.extend(well['properties'][property_name])
            for md in well['md']:
                locations.append([well['x'], well['y'], md])
                
        data = np.array(data)
        locations = np.array(locations)
        
        # Calcular distâncias
        n = len(locations)
        distances = np.zeros((n, n))
        for i in range(n):
            for j in range(i+1, n):
                if direction == 'omnidirectional':
                    distances[i,j] = distances[j,i] = np.sqrt(
                        (locations[i,0] - locations[j,0])**2 +
                        (locations[i,1] - locations[j,1])**2 +
                        (locations[i,2] - locations[j,2])**2
                    )
                else:
                    # Implementar cálculo direcional
                    pass
                    
        # Calcular variograma experimental
        if max_lag is None:
            max_lag = np.max(distances) / 2
            
        lags = np.linspace(0, max_lag, n_lags)
        gamma = np.zeros(n_lags)
        n_pairs = np.zeros(n_lags)
        
        for i in range(n):
            for j in range(i+1, n):
                d = distances[i,j]
                if d <= max_lag:
                    lag_idx = int(d / max_lag * (n_lags-1))
                    gamma[lag_idx] += (data[i] - data[j])**2
                    n_pairs[lag_idx] += 1
                    
        gamma = gamma / (2 * n_pairs)
        
        # Ajustar modelo teórico
        if variogram_model == 'spherical':
            def spherical_model(h, c0, c1, a):
                return c0 + c1 * (1.5*h/a - 0.5*(h/a)**3) * (h <= a) + c1 * (h > a)
                
            popt, _ = curve_fit(spherical_model, lags, gamma,
                              p0=[0, np.max(gamma), max_lag/2],
                              bounds=([0, 0, 0], [np.inf, np.inf, np.inf]))
                              
            model = spherical_model(lags, *popt)
            params = {'c0': popt[0], 'c1': popt[1], 'a': popt[2]}
            
        elif variogram_model == 'exponential':
            def exponential_model(h, c0, c1, a):
                return c0 + c1 * (1 - np.exp(-3*h/a))
                
            popt, _ = curve_fit(exponential_model, lags, gamma,
                              p0=[0, np.max(gamma), max_lag/2],
                              bounds=([0, 0, 0], [np.inf, np.inf, np.inf]))
                              
            model = exponential_model(lags, *popt)
            params = {'c0': popt[0], 'c1': popt[1], 'a': popt[2]}
            
        elif variogram_model == 'gaussian':
            def gaussian_model(h, c0, c1, a):
                return c0 + c1 * (1 - np.exp(-3*(h/a)**2))
                
            popt, _ = curve_fit(gaussian_model, lags, gamma,
                              p0=[0, np.max(gamma), max_lag/2],
                              bounds=([0, 0, 0], [np.inf, np.inf, np.inf]))
                              
            model = gaussian_model(lags, *popt)
            params = {'c0': popt[0], 'c1': popt[1], 'a': popt[2]}
            
        # Armazenar resultados
        self.variograms[property_name] = {
            'experimental': {
                'lags': lags,
                'gamma': gamma,
                'n_pairs': n_pairs
            },
            'model': model,
            'parameters': params
        }
        
    def kriging_interpolation(self,
                            property_name: str,
                            variogram_model: str = 'spherical'):
        """
        Realiza interpolação por krigagem.
        
        Args:
            property_name: Nome da propriedade
            variogram_model: Modelo de variograma
        """
        # Coletar dados
        points = []
        values = []
        for well_name, well in self.well_data.items():
            points.append([well['x'], well['y']])
            values.extend(well['properties'][property_name])
            
        # Criar grade de interpolação
        x = np.arange(self.grid['x0'], self.grid['x0'] + self.grid['nx']*self.grid['dx'], self.grid['dx'])
        y = np.arange(self.grid['y0'], self.grid['y0'] + self.grid['ny']*self.grid['dy'], self.grid['dy'])
        X, Y = np.meshgrid(x, y)
        
        # Realizar krigagem
        kernel = C(1.0, (1e-3, 1e3)) * RBF([1.0, 1.0], (1e-2, 1e2))
        gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)
        gp.fit(points, values)
        
        # Interpolar
        points_pred = np.vstack([X.ravel(), Y.ravel()]).T
        values_pred = gp.predict(points_pred)
        
        # Armazenar resultados
        self.properties[property_name] = values_pred.reshape(X.shape)
        
    def rock_physics_modeling(self,
                            property_name: str,
                            model_type: str = 'gassmann'):
        """
        Modelagem de física de rochas.
        
        Args:
            property_name: Nome da propriedade
            model_type: Tipo de modelo
        """
        if model_type == 'gassmann':
            # Parâmetros do modelo
            K_dry = 10  # Módulo de bulk da rocha seca (GPa)
            K_min = 37  # Módulo de bulk da matriz (GPa)
            K_fluid = 2.2  # Módulo de bulk do fluido (GPa)
            phi = 0.2  # Porosidade
            
            # Calcular módulo de bulk saturado
            K_sat = K_dry + (1 - K_dry/K_min)**2 / (phi/K_fluid + (1-phi)/K_min - K_dry/K_min**2)
            
            # Calcular velocidade P
            rho_bulk = 2.65 * (1-phi) + 1.0 * phi  # Densidade do bulk (g/cm³)
            Vp = np.sqrt((K_sat + 4/3*10) / rho_bulk)  # Velocidade P (km/s)
            
            # Armazenar resultados
            self.properties[f'{property_name}_rock_physics'] = {
                'K_sat': K_sat,
                'Vp': Vp,
                'rho_bulk': rho_bulk
            }
            
        elif model_type == 'hertz_mindlin':
            # Parâmetros do modelo
            K_min = 37  # Módulo de bulk da matriz (GPa)
            G_min = 44  # Módulo de cisalhamento da matriz (GPa)
            phi = 0.2  # Porosidade
            phi_c = 0.4  # Porosidade crítica
            P = 20  # Pressão efetiva (MPa)
            nu = 0.25  # Razão de Poisson
            
            # Calcular módulos de Hertz-Mindlin
            K_hm = (G_min**2 * (1-phi)**2 * P / (18 * np.pi**2 * (1-nu)**2))**(1/3)
            G_hm = (5-4*nu)/(5*(2-nu)) * (3*G_min**2 * (1-phi)**2 * P / (2 * np.pi**2 * (1-nu)**2))**(1/3)
            
            # Calcular módulos saturados
            K_sat = ((phi/phi_c)/(K_hm + 4/3*G_hm) + (1-phi/phi_c)/(K_min + 4/3*G_hm))**(-1) - 4/3*G_hm
            G_sat = ((phi/phi_c)/(G_hm + zeta) + (1-phi/phi_c)/(G_min + zeta))**(-1) - zeta
            zeta = G_hm/6 * (9*K_hm + 8*G_hm)/(K_hm + 2*G_hm)
            
            # Calcular velocidades
            rho_bulk = 2.65 * (1-phi) + 1.0 * phi  # Densidade do bulk (g/cm³)
            Vp = np.sqrt((K_sat + 4/3*G_sat) / rho_bulk)  # Velocidade P (km/s)
            Vs = np.sqrt(G_sat / rho_bulk)  # Velocidade S (km/s)
            
            # Armazenar resultados
            self.properties[f'{property_name}_rock_physics'] = {
                'K_sat': K_sat,
                'G_sat': G_sat,
                'Vp': Vp,
                'Vs': Vs,
                'rho_bulk': rho_bulk
            }
            
        else:
            raise ValueError(f"Modelo {model_type} não implementado")
            
    def analyze_nmr_data(self,
                        well_name: str,
                        t2_distribution: np.ndarray,
                        t2_times: np.ndarray):
        """
        Análise de dados de RMN.
        
        Args:
            well_name: Nome do poço
            t2_distribution: Distribuição T2
            t2_times: Tempos T2
        """
        # Calcular parâmetros de RMN
        t2_ml = np.sum(t2_distribution * t2_times) / np.sum(t2_distribution)
        bvi = np.sum(t2_distribution[t2_times < 33]) / np.sum(t2_distribution)
        ffv = np.sum(t2_distribution[t2_times > 33]) / np.sum(t2_distribution)
        
        # Calcular distribuição de tamanho de poros
        rho2 = 0.1  # Constante de relaxação superficial (μm/ms)
        pore_sizes = t2_times * rho2
        
        # Calcular distribuição de permeabilidade
        k_coates = (ffv/bvi)**2 * (t2_ml/10)**4  # Permeabilidade de Coates
        k_sdr = 4 * t2_ml**2  # Permeabilidade SDR
        
        # Calcular distribuição de capilaridade
        sigma = 72  # Tensão superficial (dyn/cm)
        theta = 0  # Ângulo de contato
        pc = 2 * sigma * np.cos(theta) / pore_sizes  # Pressão capilar (psi)
        
        # Armazenar resultados
        self.nmr_data[well_name] = {
            't2_ml': t2_ml,
            'bvi': bvi,
            'ffv': ffv,
            't2_distribution': t2_distribution,
            't2_times': t2_times,
            'pore_sizes': pore_sizes,
            'k_coates': k_coates,
            'k_sdr': k_sdr,
            'pc': pc
        }
        
    def plot_variogram(self, property_name: str):
        """
        Plota variograma.
        
        Args:
            property_name: Nome da propriedade
        """
        variogram = self.variograms[property_name]
        
        plt.figure(figsize=(10, 6))
        plt.plot(variogram['experimental']['lags'],
                variogram['experimental']['gamma'],
                'o', label='Experimental')
        plt.plot(variogram['experimental']['lags'],
                variogram['model'],
                '-', label='Modelo')
        plt.xlabel('Lag Distance')
        plt.ylabel('Semivariance')
        plt.title(f'Variograma - {property_name}')
        plt.legend()
        plt.grid(True)
        
        return plt.gcf()
        
    def plot_property_map(self, property_name: str):
        """
        Plota mapa de propriedade.
        
        Args:
            property_name: Nome da propriedade
        """
        data = self.properties[property_name]
        
        plt.figure(figsize=(10, 8))
        plt.imshow(data, cmap='viridis')
        plt.colorbar(label=property_name)
        plt.title(f'Mapa de {property_name}')
        
        # Plotar poços
        for well_name, well in self.well_data.items():
            plt.plot(well['x'], well['y'], 'ro')
            plt.text(well['x'], well['y'], well_name)
            
        return plt.gcf()
        
    def plot_nmr_analysis(self, well_name: str):
        """
        Plota análise de RMN.
        
        Args:
            well_name: Nome do poço
        """
        nmr_data = self.nmr_data[well_name]
        
        plt.figure(figsize=(15, 5))
        
        # Plotar distribuição T2
        plt.subplot(131)
        plt.semilogx(nmr_data['t2_times'],
                    nmr_data['t2_distribution'],
                    '-', label='Distribuição T2')
        plt.axvline(x=33, color='r', linestyle='--', label='BVI Cutoff')
        plt.xlabel('T2 (ms)')
        plt.ylabel('Amplitude')
        plt.title('Distribuição T2')
        plt.legend()
        plt.grid(True)
        
        # Plotar distribuição de tamanho de poros
        plt.subplot(132)
        plt.semilogx(nmr_data['pore_sizes'],
                    nmr_data['t2_distribution'],
                    '-', label='Distribuição de Poros')
        plt.xlabel('Tamanho de Poros (μm)')
        plt.ylabel('Amplitude')
        plt.title('Distribuição de Tamanho de Poros')
        plt.grid(True)
        
        # Plotar curva de pressão capilar
        plt.subplot(133)
        plt.semilogx(nmr_data['pc'],
                    nmr_data['t2_distribution'],
                    '-', label='Curva Capilar')
        plt.xlabel('Pressão Capilar (psi)')
        plt.ylabel('Amplitude')
        plt.title('Curva de Pressão Capilar')
        plt.grid(True)
        
        plt.suptitle(f'Análise de RMN - {well_name}')
        plt.tight_layout()
        
        return plt.gcf()

    def monte_carlo_simulation(self,
                             property_name: str,
                             n_realizations: int = 100,
                             seed: int = None):
        """
        Realiza simulação de Monte Carlo.
        
        Args:
            property_name: Nome da propriedade
            n_realizations: Número de realizações
            seed: Semente para reprodutibilidade
        """
        if seed is not None:
            np.random.seed(seed)
            
        # Obter parâmetros do variograma
        variogram = self.variograms[property_name]
        params = variogram['parameters']
        
        # Gerar realizações
        realizations = []
        for i in range(n_realizations):
            # Gerar campo aleatório gaussiano
            field = np.random.normal(0, 1, self.properties[property_name].shape)
            
            # Aplicar correlação espacial
            kernel = np.exp(-3 * np.sqrt(
                (np.arange(-5, 6)[:, np.newaxis] / params['a'])**2 +
                (np.arange(-5, 6)[np.newaxis, :] / params['a'])**2
            ))
            kernel = kernel / np.sum(kernel)
            
            field = scipy.signal.convolve2d(field, kernel, mode='same')
            
            # Transformar para distribuição desejada
            field = norm.ppf(norm.cdf(field))
            field = field * np.sqrt(params['c1']) + params['c0']
            
            realizations.append(field)
            
        # Armazenar realizações
        self.properties[f'{property_name}_realizations'] = realizations
        
    def calculate_uncertainty(self,
                            property_name: str,
                            confidence: float = 0.95):
        """
        Calcula incerteza das realizações.
        
        Args:
            property_name: Nome da propriedade
            confidence: Nível de confiança
        """
        realizations = self.properties[f'{property_name}_realizations']
        
        # Calcular estatísticas
        mean = np.mean(realizations, axis=0)
        std = np.std(realizations, axis=0)
        
        # Calcular intervalos de confiança
        z = norm.ppf((1 + confidence) / 2)
        lower = mean - z * std
        upper = mean + z * std
        
        # Armazenar resultados
        self.properties[f'{property_name}_uncertainty'] = {
            'mean': mean,
            'std': std,
            'lower': lower,
            'upper': upper
        }
        
    def plot_uncertainty(self, property_name: str):
        """
        Plota resultados da análise de incerteza.
        
        Args:
            property_name: Nome da propriedade
        """
        uncertainty = self.properties[f'{property_name}_uncertainty']
        
        plt.figure(figsize=(15, 5))
        
        # Plotar média
        plt.subplot(131)
        plt.imshow(uncertainty['mean'], cmap='viridis')
        plt.colorbar(label='Mean')
        plt.title('Mean')
        
        # Plotar desvio padrão
        plt.subplot(132)
        plt.imshow(uncertainty['std'], cmap='viridis')
        plt.colorbar(label='Standard Deviation')
        plt.title('Standard Deviation')
        
        # Plotar intervalo de confiança
        plt.subplot(133)
        plt.imshow(uncertainty['upper'] - uncertainty['lower'], cmap='viridis')
        plt.colorbar(label='Confidence Interval')
        plt.title('Confidence Interval')
        
        plt.suptitle(f'Uncertainty Analysis - {property_name}')
        plt.tight_layout()
        
        return plt.gcf() 