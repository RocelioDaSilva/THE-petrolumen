import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import norm
from scipy.optimize import minimize
from scipy.interpolate import interp1d
import streamlit as st
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

class PVTProperties:
    """Classe para cálculo de propriedades PVT."""
    
    def __init__(self):
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('PVTProperties')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def calculate_formation_volume_factor(self,
                                        pressure: float,
                                        temperature: float,
                                        fluid_type: str,
                                        api_gravity: Optional[float] = None,
                                        gas_specific_gravity: Optional[float] = None) -> float:
        """
        Calcula fator de volume de formação (Bo, Bg).
        
        Args:
            pressure: Pressão (psia)
            temperature: Temperatura (°F)
            fluid_type: Tipo de fluido ('oil' ou 'gas')
            api_gravity: Grau API do óleo
            gas_specific_gravity: Densidade do gás
            
        Returns:
            Fator de volume de formação
        """
        if fluid_type == 'oil':
            # Correlação de Standing para Bo
            rs = self.calculate_solution_gas_ratio(pressure, temperature, api_gravity, gas_specific_gravity)
            f = rs * (gas_specific_gravity/0.7)**0.5 + 1.25 * temperature
            bo = 0.972 + 0.000147 * f**1.175
            return bo
        else:  # gas
            # Correlação de Dranchuk-Abu-Kassem para Bg
            z = self.calculate_z_factor(pressure, temperature, gas_specific_gravity)
            bg = 0.02827 * z * temperature / pressure
            return bg
            
    def calculate_viscosity(self,
                          pressure: float,
                          temperature: float,
                          fluid_type: str,
                          api_gravity: Optional[float] = None,
                          gas_specific_gravity: Optional[float] = None) -> float:
        """
        Calcula viscosidade dos fluidos.
        
        Args:
            pressure: Pressão (psia)
            temperature: Temperatura (°F)
            fluid_type: Tipo de fluido ('oil' ou 'gas')
            api_gravity: Grau API do óleo
            gas_specific_gravity: Densidade do gás
            
        Returns:
            Viscosidade (cp)
        """
        if fluid_type == 'oil':
            # Correlação de Beggs-Robinson para viscosidade do óleo
            api = api_gravity
            t = temperature
            
            # Viscosidade do óleo morto
            a = 10**(0.43 + 8.33/api)
            mu_od = (0.32 + 1.8e7/api**4.53) * (360/(t + 200))**a
            
            # Viscosidade do óleo saturado
            rs = self.calculate_solution_gas_ratio(pressure, temperature, api_gravity, gas_specific_gravity)
            a = 10.715 * (rs + 100)**-0.515
            b = 5.44 * (rs + 150)**-0.338
            mu_o = a * mu_od**b
            
            return mu_o
        else:  # gas
            # Correlação de Lee-Gonzalez-Eakin para viscosidade do gás
            t = temperature + 460  # temperatura em Rankine
            mw = gas_specific_gravity * 28.97  # peso molecular
            rho = pressure * mw / (10.73 * t * self.calculate_z_factor(pressure, temperature, gas_specific_gravity))
            
            k = (9.4 + 0.02 * mw) * t**1.5 / (209 + 19 * mw + t)
            x = 3.5 + 986/t + 0.01 * mw
            y = 2.4 - 0.2 * x
            
            mu_g = 1e-4 * k * np.exp(x * rho**y)
            return mu_g
            
    def calculate_solution_gas_ratio(self,
                                   pressure: float,
                                   temperature: float,
                                   api_gravity: float,
                                   gas_specific_gravity: float) -> float:
        """
        Calcula relação gás-óleo em solução (Rs).
        
        Args:
            pressure: Pressão (psia)
            temperature: Temperatura (°F)
            api_gravity: Grau API do óleo
            gas_specific_gravity: Densidade do gás
            
        Returns:
            Relação gás-óleo (scf/stb)
        """
        # Correlação de Standing
        api = api_gravity
        t = temperature
        yg = gas_specific_gravity
        
        x = 0.0125 * api - 0.00091 * t
        rs = yg * (pressure/18.2 + 1.4) * 10**x
        return rs
        
    def calculate_z_factor(self,
                          pressure: float,
                          temperature: float,
                          gas_specific_gravity: float) -> float:
        """
        Calcula fator de compressibilidade (Z).
        
        Args:
            pressure: Pressão (psia)
            temperature: Temperatura (°F)
            gas_specific_gravity: Densidade do gás
            
        Returns:
            Fator de compressibilidade
        """
        # Correlação de Hall-Yarborough
        t = temperature + 460  # temperatura em Rankine
        tpc = 168 + 325 * gas_specific_gravity - 12.5 * gas_specific_gravity**2
        ppc = 677 + 15 * gas_specific_gravity - 37.5 * gas_specific_gravity**2
        
        tr = t / tpc
        pr = pressure / ppc
        
        t1 = 0.06125 * pr * np.exp(-1.2 * (1 - 1/tr)**2)
        t2 = 14.76 * tr - 9.76 * tr**2 + 4.58 * tr**3
        t3 = 90.7 * tr - 242.2 * tr**2 + 42.4 * tr**3
        t4 = 2.18 + 2.82 * tr
        
        y = t1 / (t2 + t3 + t4)
        
        z = 0.06125 * pr * np.exp(-1.2 * (1 - 1/tr)**2) / y
        return z

class ReservoirSimulation:
    """Classe para simulação numérica de reservatórios."""
    
    def __init__(self, nx: int, ny: int, nz: int):
        """
        Inicializa o simulador.
        
        Args:
            nx: Número de blocos em x
            ny: Número de blocos em y
            nz: Número de blocos em z
        """
        self.nx = nx
        self.ny = ny
        self.nz = nz
        self.grid = self._initialize_grid()
        self.wells = {}
        self.pvt = PVTProperties()
        
    def _initialize_grid(self) -> Dict:
        """Inicializa a malha do reservatório."""
        return {
            'porosity': np.ones((self.nx, self.ny, self.nz)) * 0.2,
            'permeability': np.ones((self.nx, self.ny, self.nz)) * 100,
            'pressure': np.ones((self.nx, self.ny, self.nz)) * 3000,
            'saturation': np.ones((self.nx, self.ny, self.nz)) * 0.8
        }
        
    def add_well(self,
                name: str,
                i: int,
                j: int,
                k: int,
                well_type: str,
                rate: float = None,
                bhp: float = None):
        """
        Adiciona um poço ao modelo.
        
        Args:
            name: Nome do poço
            i, j, k: Índices do bloco
            well_type: Tipo do poço ('producer' ou 'injector')
            rate: Vazão (opcional)
            bhp: Pressão de fundo de poço (opcional)
        """
        self.wells[name] = {
            'position': (i, j, k),
            'type': well_type,
            'rate': rate,
            'bhp': bhp
        }
        
    def run_simulation(self,
                      timesteps: int,
                      dt: float,
                      simulation_type: str = 'transient'):
        """
        Executa a simulação.
        
        Args:
            timesteps: Número de passos de tempo
            dt: Tamanho do passo de tempo
            simulation_type: Tipo de simulação ('steady_state' ou 'transient')
        """
        if simulation_type == 'steady_state':
            self._run_steady_state()
        else:
            self._run_transient(timesteps, dt)
            
    def _run_steady_state(self):
        """Executa simulação em estado estacionário."""
        # Implementar solver para estado estacionário
        pass
        
    def _run_transient(self, timesteps: int, dt: float):
        """Executa simulação transiente."""
        # Implementar solver para estado transiente
        pass

class MaterialBalance:
    """Classe para análise de balanço de materiais."""
    
    def __init__(self):
        self.pvt = PVTProperties()
        
    def calculate_ogip(self,
                      pressure: np.ndarray,
                      production: np.ndarray,
                      temperature: float,
                      gas_specific_gravity: float) -> float:
        """
        Calcula OGIP usando balanço de materiais.
        
        Args:
            pressure: Array de pressões
            production: Array de produção acumulada
            temperature: Temperatura do reservatório
            gas_specific_gravity: Densidade do gás
            
        Returns:
            OGIP estimado
        """
        # Método de Havlena-Odeh
        p = pressure
        gp = production
        
        # Calcular Z médio
        z = np.array([self.pvt.calculate_z_factor(pi, temperature, gas_specific_gravity) for pi in p])
        
        # Calcular F e Eg
        f = gp
        eg = (p[0]/z[0] - p/z) * 1000  # 1000 para converter para scf
        
        # Regressão linear
        slope, _ = np.polyfit(eg, f, 1)
        
        return slope
        
    def calculate_stoiip(self,
                        pressure: np.ndarray,
                        production: np.ndarray,
                        temperature: float,
                        api_gravity: float,
                        gas_specific_gravity: float) -> float:
        """
        Calcula STOIIP usando balanço de materiais.
        
        Args:
            pressure: Array de pressões
            production: Array de produção acumulada
            temperature: Temperatura do reservatório
            api_gravity: Grau API do óleo
            gas_specific_gravity: Densidade do gás
            
        Returns:
            STOIIP estimado
        """
        # Método de Havlena-Odeh para óleo
        p = pressure
        np = production
        
        # Calcular Bo e Rs
        bo = np.array([self.pvt.calculate_formation_volume_factor(pi, temperature, 'oil', api_gravity, gas_specific_gravity) for pi in p])
        rs = np.array([self.pvt.calculate_solution_gas_ratio(pi, temperature, api_gravity, gas_specific_gravity) for pi in p])
        
        # Calcular F e Eo
        f = np * (bo + (rs[0] - rs) * self.pvt.calculate_formation_volume_factor(p[0], temperature, 'gas', None, gas_specific_gravity))
        eo = (bo - bo[0]) + (rs[0] - rs) * self.pvt.calculate_formation_volume_factor(p[0], temperature, 'gas', None, gas_specific_gravity)
        
        # Regressão linear
        slope, _ = np.polyfit(eo, f, 1)
        
        return slope

class WellTesting:
    """Classe para análise de testes de pressão."""
    
    def __init__(self):
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('WellTesting')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def analyze_buildup(self,
                       time: np.ndarray,
                       pressure: np.ndarray,
                       rate: float,
                       viscosity: float,
                       compressibility: float,
                       porosity: float,
                       wellbore_radius: float) -> Dict:
        """
        Analisa teste de build-up.
        
        Args:
            time: Array de tempos
            pressure: Array de pressões
            rate: Vazão antes do build-up
            viscosity: Viscosidade do fluido
            compressibility: Compressibilidade total
            porosity: Porosidade
            wellbore_radius: Raio do poço
            
        Returns:
            Dicionário com resultados da análise
        """
        # Método de Horner
        tp = time[-1]  # tempo de produção
        dt = time - time[0]  # delta t
        tda = (tp + dt) / dt  # tempo de Horner
        
        # Regressão linear
        slope, intercept = np.polyfit(np.log(tda), pressure, 1)
        
        # Calcular parâmetros
        k = 162.6 * rate * viscosity / (slope * 1)  # permeabilidade
        skin = 1.151 * ((intercept - pressure[0])/slope - np.log10(k/(porosity * viscosity * compressibility * wellbore_radius**2)) + 3.23)
        
        return {
            'permeability': k,
            'skin': skin,
            'slope': slope,
            'intercept': intercept
        }
        
    def analyze_drawdown(self,
                        time: np.ndarray,
                        pressure: np.ndarray,
                        rate: float,
                        viscosity: float,
                        compressibility: float,
                        porosity: float,
                        wellbore_radius: float) -> Dict:
        """
        Analisa teste de drawdown.
        
        Args:
            time: Array de tempos
            pressure: Array de pressões
            rate: Vazão constante
            viscosity: Viscosidade do fluido
            compressibility: Compressibilidade total
            porosity: Porosidade
            wellbore_radius: Raio do poço
            
        Returns:
            Dicionário com resultados da análise
        """
        # Método de semilog
        dt = time - time[0]  # delta t
        
        # Regressão linear
        slope, intercept = np.polyfit(np.log(dt), pressure, 1)
        
        # Calcular parâmetros
        k = 162.6 * rate * viscosity / (slope * 1)  # permeabilidade
        skin = 1.151 * ((pressure[0] - intercept)/slope - np.log10(k/(porosity * viscosity * compressibility * wellbore_radius**2)) + 3.23)
        
        return {
            'permeability': k,
            'skin': skin,
            'slope': slope,
            'intercept': intercept
        }

class DeclineAnalysis:
    """Classe para análise de declínio de produção."""
    
    def __init__(self):
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('DeclineAnalysis')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def fit_arps(self,
                time: np.ndarray,
                rate: np.ndarray,
                method: str = 'hyperbolic') -> Dict:
        """
        Ajusta curva de declínio de Arps.
        
        Args:
            time: Array de tempos
            rate: Array de vazões
            method: Método de declínio ('exponential', 'harmonic' ou 'hyperbolic')
            
        Returns:
            Dicionário com parâmetros ajustados
        """
        if method == 'exponential':
            # q = qi * exp(-Di * t)
            log_rate = np.log(rate)
            slope, intercept = np.polyfit(time, log_rate, 1)
            di = -slope
            qi = np.exp(intercept)
            b = 0
            
        elif method == 'harmonic':
            # q = qi / (1 + Di * t)
            inv_rate = 1/rate
            slope, intercept = np.polyfit(time, inv_rate, 1)
            di = slope/intercept
            qi = 1/intercept
            b = 1
            
        else:  # hyperbolic
            # q = qi / (1 + b * Di * t)^(1/b)
            def objective(params):
                qi, di, b = params
                q_pred = qi / (1 + b * di * time)**(1/b)
                return np.sum((rate - q_pred)**2)
                
            # Otimização
            result = minimize(objective, [rate[0], 0.1, 0.5],
                            bounds=[(0, None), (0, None), (0, 1)])
            qi, di, b = result.x
            
        return {
            'qi': qi,
            'di': di,
            'b': b,
            'method': method
        }
        
    def forecast_production(self,
                          params: Dict,
                          time: np.ndarray) -> np.ndarray:
        """
        Gera previsão de produção.
        
        Args:
            params: Parâmetros do ajuste
            time: Array de tempos para previsão
            
        Returns:
            Array com vazões previstas
        """
        qi = params['qi']
        di = params['di']
        b = params['b']
        
        if params['method'] == 'exponential':
            rate = qi * np.exp(-di * time)
        elif params['method'] == 'harmonic':
            rate = qi / (1 + di * time)
        else:  # hyperbolic
            rate = qi / (1 + b * di * time)**(1/b)
            
        return rate
        
    def calculate_eur(self, params: Dict) -> float:
        """
        Calcula EUR (Estimated Ultimate Recovery).
        
        Args:
            params: Parâmetros do ajuste
            
        Returns:
            EUR estimado
        """
        qi = params['qi']
        di = params['di']
        b = params['b']
        
        if params['method'] == 'exponential':
            eur = qi/di
        elif params['method'] == 'harmonic':
            eur = qi/di * np.log(1 + di * 365 * 30)  # 30 anos
        else:  # hyperbolic
            eur = qi/((1-b)*di) * (1 - (1 + b * di * 365 * 30)**(1-1/b))  # 30 anos
            
        return eur

class HistoryMatching:
    """Classe para ajuste de histórico."""
    
    def __init__(self, simulation: ReservoirSimulation):
        self.simulation = simulation
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('HistoryMatching')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def match_history(self,
                     historical_data: Dict[str, np.ndarray],
                     parameters: Dict[str, Tuple[float, float]],
                     objective_function: callable) -> Dict:
        """
        Realiza ajuste de histórico.
        
        Args:
            historical_data: Dicionário com dados históricos
            parameters: Dicionário com parâmetros a ajustar e seus limites
            objective_function: Função objetivo
            
        Returns:
            Dicionário com parâmetros otimizados
        """
        def objective(params):
            # Atualizar parâmetros do modelo
            for i, (param, _) in enumerate(parameters.items()):
                setattr(self.simulation, param, params[i])
                
            # Rodar simulação
            self.simulation.run_simulation(timesteps=len(historical_data['time']), dt=1)
            
            # Calcular erro
            error = objective_function(historical_data, self.simulation.grid)
            return error
            
        # Otimização
        initial_guess = [0.5 * (min_val + max_val) for _, (min_val, max_val) in parameters.items()]
        bounds = [bounds for _, bounds in parameters.items()]
        
        result = minimize(objective, initial_guess, bounds=bounds)
        
        # Retornar parâmetros otimizados
        optimized_params = {}
        for i, (param, _) in enumerate(parameters.items()):
            optimized_params[param] = result.x[i]
            
        return optimized_params

class ReservoirVisualization:
    """Classe para visualização do reservatório."""
    
    def __init__(self, simulation: ReservoirSimulation):
        self.simulation = simulation
        
    def plot_saturation_map(self,
                           layer: int,
                           time_step: int = -1) -> plt.Figure:
        """
        Plota mapa de saturação.
        
        Args:
            layer: Camada a ser plotada
            time_step: Passo de tempo
            
        Returns:
            Figura do matplotlib
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        saturation = self.simulation.grid['saturation'][:, :, layer]
        im = ax.imshow(saturation, cmap='jet')
        plt.colorbar(im, ax=ax, label='Saturação de Óleo')
        
        ax.set_title(f'Mapa de Saturação - Camada {layer}')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        
        return fig
        
    def plot_pressure_map(self,
                         layer: int,
                         time_step: int = -1) -> plt.Figure:
        """
        Plota mapa de pressão.
        
        Args:
            layer: Camada a ser plotada
            time_step: Passo de tempo
            
        Returns:
            Figura do matplotlib
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        pressure = self.simulation.grid['pressure'][:, :, layer]
        im = ax.imshow(pressure, cmap='jet')
        plt.colorbar(im, ax=ax, label='Pressão (psia)')
        
        ax.set_title(f'Mapa de Pressão - Camada {layer}')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        
        return fig
        
    def plot_well_performance(self,
                            well_name: str,
                            time: np.ndarray,
                            rate: np.ndarray,
                            pressure: np.ndarray) -> plt.Figure:
        """
        Plota performance do poço.
        
        Args:
            well_name: Nome do poço
            time: Array de tempos
            rate: Array de vazões
            pressure: Array de pressões
            
        Returns:
            Figura do matplotlib
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Vazão
        ax1.plot(time, rate, 'b-')
        ax1.set_xlabel('Tempo')
        ax1.set_ylabel('Vazão (bbl/d)')
        ax1.set_title(f'Performance do Poço {well_name}')
        
        # Pressão
        ax2.plot(time, pressure, 'r-')
        ax2.set_xlabel('Tempo')
        ax2.set_ylabel('Pressão (psia)')
        
        plt.tight_layout()
        return fig 