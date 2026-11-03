import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution, minimize
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import streamlit as st

class ProductionOptimization:
    def __init__(self, flow_simulation):
        """
        Inicializa o otimizador de produção.
        
        Args:
            flow_simulation: Objeto de simulação de fluxo
        """
        self.sim = flow_simulation
        self.forecast_results = None
        self.scenario_results = None
        self.optimization_results = None
        self.eor_results = None
        
    def forecast_production(self, forecast_period: int, dt: float,
                          decline_curves: Optional[Dict] = None) -> Dict:
        """
        Previsão de produção usando simulação e/ou curvas de declínio.
        
        Args:
            forecast_period: Período de previsão em dias
            dt: Passo de tempo em dias
            decline_curves: Dicionário com parâmetros das curvas de declínio
            
        Returns:
            Dicionário com resultados da previsão
        """
        n_steps = int(forecast_period / dt)
        
        if decline_curves is not None:
            # Previsão usando curvas de declínio
            forecast = self._forecast_with_decline_curves(
                n_steps, dt, decline_curves
            )
        else:
            # Previsão usando simulação
            forecast = self._forecast_with_simulation(n_steps, dt)
            
        self.forecast_results = forecast
        return forecast
        
    def _forecast_with_decline_curves(self, n_steps: int, dt: float,
                                    decline_curves: Dict) -> Dict:
        """Previsão usando curvas de declínio."""
        time = np.arange(0, n_steps * dt, dt)
        forecast = {
            'time': time,
            'oil': np.zeros(n_steps),
            'water': np.zeros(n_steps),
            'gas': np.zeros(n_steps)
        }
        
        for phase in ['oil', 'water', 'gas']:
            if phase in decline_curves:
                qi = decline_curves[phase]['qi']
                Di = decline_curves[phase]['Di']
                b = decline_curves[phase].get('b', 0)
                
                if b == 0:  # Exponencial
                    forecast[phase] = qi * np.exp(-Di * time)
                else:  # Hiperbólico
                    forecast[phase] = qi * (1 + b * Di * time) ** (-1/b)
                    
        return forecast
        
    def _forecast_with_simulation(self, n_steps: int, dt: float) -> Dict:
        """Previsão usando simulação de fluxo."""
        results = self.sim.run_black_oil_simulation(dt, n_steps)
        
        forecast = {
            'time': np.arange(0, n_steps * dt, dt),
            'oil': results['production']['oil'],
            'water': results['production']['water'],
            'gas': results['production']['gas'],
            'pressure': [np.mean(p) for p in results['pressure']]
        }
        
        return forecast
        
    def run_scenario_analysis(self, scenarios: List[Dict]) -> Dict:
        """
        Simula diferentes cenários de desenvolvimento.
        
        Args:
            scenarios: Lista de cenários com suas configurações
            
        Returns:
            Dicionário com resultados dos cenários
        """
        results = {}
        
        for i, scenario in enumerate(scenarios):
            # Configurar cenário
            self._configure_scenario(scenario)
            
            # Executar simulação
            forecast = self.forecast_production(
                scenario['forecast_period'],
                scenario['dt']
            )
            
            # Calcular métricas
            metrics = self._calculate_scenario_metrics(forecast)
            
            results[f'scenario_{i+1}'] = {
                'forecast': forecast,
                'metrics': metrics
            }
            
        self.scenario_results = results
        return results
        
    def _configure_scenario(self, scenario: Dict):
        """Configura parâmetros do cenário."""
        # Configurar poços
        if 'wells' in scenario:
            self.sim.configure_wells(scenario['wells'])
            
        # Configurar mecanismos de empuxo
        if 'drive_mechanisms' in scenario:
            for mechanism, props in scenario['drive_mechanisms'].items():
                self.sim.set_drive_mechanism(mechanism, props)
                
        # Configurar EOR
        if 'eor' in scenario:
            self.sim.configure_eor(scenario['eor'])
            
    def _calculate_scenario_metrics(self, forecast: Dict) -> Dict:
        """Calcula métricas para o cenário."""
        metrics = {
            'cumulative_oil': np.sum(forecast['oil']),
            'cumulative_water': np.sum(forecast['water']),
            'cumulative_gas': np.sum(forecast['gas']),
            'water_cut': np.mean(forecast['water'] / 
                               (forecast['oil'] + forecast['water'])),
            'gas_oil_ratio': np.mean(forecast['gas'] / forecast['oil']),
            'recovery_factor': np.sum(forecast['oil']) / self.sim.ooip
        }
        
        return metrics
        
    def optimize_well_pattern(self, constraints: Dict) -> Dict:
        """
        Otimiza a malha de poços.
        
        Args:
            constraints: Restrições para otimização
            
        Returns:
            Dicionário com resultados da otimização
        """
        def objective(x):
            # x[0:n_wells]: posições x dos poços
            # x[n_wells:2*n_wells]: posições y dos poços
            # x[2*n_wells:3*n_wells]: tipos dos poços (0=produtor, 1=injetor)
            
            n_wells = len(x) // 3
            wells = []
            
            for i in range(n_wells):
                wells.append({
                    'x': x[i],
                    'y': x[n_wells + i],
                    'type': 'producer' if x[2*n_wells + i] < 0.5 else 'injector'
                })
                
            # Configurar poços
            self.sim.configure_wells(wells)
            
            # Executar simulação
            forecast = self.forecast_production(
                constraints['forecast_period'],
                constraints['dt']
            )
            
            # Calcular objetivo (NPV)
            npv = self._calculate_npv(forecast, constraints)
            
            return -npv  # Minimizar negativo do NPV
            
        # Definir limites
        bounds = []
        n_wells = constraints['n_wells']
        
        # Limites para posições x e y
        for _ in range(2 * n_wells):
            bounds.append((0, self.sim.mesh.dimensions[0]))
            
        # Limites para tipos de poços
        for _ in range(n_wells):
            bounds.append((0, 1))
            
        # Otimizar
        result = differential_evolution(
            objective,
            bounds=bounds,
            maxiter=constraints['max_iterations'],
            popsize=constraints['population_size']
        )
        
        # Preparar resultados
        n_wells = len(result.x) // 3
        wells = []
        
        for i in range(n_wells):
            wells.append({
                'x': result.x[i],
                'y': result.x[n_wells + i],
                'type': 'producer' if result.x[2*n_wells + i] < 0.5 else 'injector'
            })
            
        self.optimization_results = {
            'wells': wells,
            'npv': -result.fun,
            'success': result.success,
            'message': result.message
        }
        
        return self.optimization_results
        
    def _calculate_npv(self, forecast: Dict, constraints: Dict) -> float:
        """Calcula o Valor Presente Líquido (NPV)."""
        # Parâmetros econômicos
        oil_price = constraints['oil_price']
        gas_price = constraints['gas_price']
        water_cost = constraints['water_cost']
        discount_rate = constraints['discount_rate']
        
        # Calcular fluxo de caixa
        time = forecast['time']
        cash_flow = (
            oil_price * forecast['oil'] +
            gas_price * forecast['gas'] -
            water_cost * forecast['water']
        )
        
        # Calcular NPV
        npv = np.sum(cash_flow / (1 + discount_rate) ** (time/365))
        
        return npv
        
    def plan_eor(self, eor_type: str, constraints: Dict) -> Dict:
        """
        Planeja recuperação secundária ou terciária.
        
        Args:
            eor_type: Tipo de EOR ('waterflood', 'gas_injection', 'chemical', 'thermal')
            constraints: Restrições para planejamento
            
        Returns:
            Dicionário com resultados do planejamento
        """
        if eor_type == 'waterflood':
            results = self._plan_waterflood(constraints)
        elif eor_type == 'gas_injection':
            results = self._plan_gas_injection(constraints)
        elif eor_type == 'chemical':
            results = self._plan_chemical_eor(constraints)
        elif eor_type == 'thermal':
            results = self._plan_thermal_eor(constraints)
        else:
            raise ValueError(f"Tipo de EOR não suportado: {eor_type}")
            
        self.eor_results = results
        return results
        
    def _plan_waterflood(self, constraints: Dict) -> Dict:
        """Planeja injeção de água."""
        # Otimizar padrão de injeção
        well_pattern = self.optimize_well_pattern({
            **constraints,
            'n_wells': constraints['n_injectors'] + constraints['n_producers']
        })
        
        # Configurar injeção de água
        injection_rate = constraints['injection_rate']
        water_quality = constraints['water_quality']
        
        # Executar simulação
        forecast = self.forecast_production(
            constraints['forecast_period'],
            constraints['dt']
        )
        
        return {
            'well_pattern': well_pattern,
            'injection_rate': injection_rate,
            'water_quality': water_quality,
            'forecast': forecast,
            'metrics': self._calculate_scenario_metrics(forecast)
        }
        
    def _plan_gas_injection(self, constraints: Dict) -> Dict:
        """Planeja injeção de gás."""
        # Otimizar padrão de injeção
        well_pattern = self.optimize_well_pattern({
            **constraints,
            'n_wells': constraints['n_injectors'] + constraints['n_producers']
        })
        
        # Configurar injeção de gás
        injection_rate = constraints['injection_rate']
        gas_composition = constraints['gas_composition']
        
        # Executar simulação
        forecast = self.forecast_production(
            constraints['forecast_period'],
            constraints['dt']
        )
        
        return {
            'well_pattern': well_pattern,
            'injection_rate': injection_rate,
            'gas_composition': gas_composition,
            'forecast': forecast,
            'metrics': self._calculate_scenario_metrics(forecast)
        }
        
    def _plan_chemical_eor(self, constraints: Dict) -> Dict:
        """Planeja EOR químico."""
        # Otimizar padrão de injeção
        well_pattern = self.optimize_well_pattern({
            **constraints,
            'n_wells': constraints['n_injectors'] + constraints['n_producers']
        })
        
        # Configurar injeção química
        chemical_type = constraints['chemical_type']
        concentration = constraints['concentration']
        slug_size = constraints['slug_size']
        
        # Executar simulação
        forecast = self.forecast_production(
            constraints['forecast_period'],
            constraints['dt']
        )
        
        return {
            'well_pattern': well_pattern,
            'chemical_type': chemical_type,
            'concentration': concentration,
            'slug_size': slug_size,
            'forecast': forecast,
            'metrics': self._calculate_scenario_metrics(forecast)
        }
        
    def _plan_thermal_eor(self, constraints: Dict) -> Dict:
        """Planeja EOR térmico."""
        # Otimizar padrão de injeção
        well_pattern = self.optimize_well_pattern({
            **constraints,
            'n_wells': constraints['n_injectors'] + constraints['n_producers']
        })
        
        # Configurar injeção térmica
        steam_quality = constraints['steam_quality']
        injection_temperature = constraints['injection_temperature']
        injection_rate = constraints['injection_rate']
        
        # Executar simulação
        forecast = self.forecast_production(
            constraints['forecast_period'],
            constraints['dt']
        )
        
        return {
            'well_pattern': well_pattern,
            'steam_quality': steam_quality,
            'injection_temperature': injection_temperature,
            'injection_rate': injection_rate,
            'forecast': forecast,
            'metrics': self._calculate_scenario_metrics(forecast)
        }
        
    def plot_forecast(self):
        """Plota resultados da previsão."""
        if self.forecast_results is None:
            raise ValueError("Execute a previsão primeiro")
            
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Produção de óleo
        axes[0,0].plot(self.forecast_results['time'],
                      self.forecast_results['oil'],
                      'b-', label='Óleo')
        axes[0,0].set_title('Produção de Óleo')
        axes[0,0].set_xlabel('Tempo (dias)')
        axes[0,0].set_ylabel('Taxa (bbl/d)')
        axes[0,0].grid(True)
        axes[0,0].legend()
        
        # Produção de água
        axes[0,1].plot(self.forecast_results['time'],
                      self.forecast_results['water'],
                      'r-', label='Água')
        axes[0,1].set_title('Produção de Água')
        axes[0,1].set_xlabel('Tempo (dias)')
        axes[0,1].set_ylabel('Taxa (bbl/d)')
        axes[0,1].grid(True)
        axes[0,1].legend()
        
        # Produção de gás
        axes[1,0].plot(self.forecast_results['time'],
                      self.forecast_results['gas'],
                      'g-', label='Gás')
        axes[1,0].set_title('Produção de Gás')
        axes[1,0].set_xlabel('Tempo (dias)')
        axes[1,0].set_ylabel('Taxa (Mscf/d)')
        axes[1,0].grid(True)
        axes[1,0].legend()
        
        # Pressão
        if 'pressure' in self.forecast_results:
            axes[1,1].plot(self.forecast_results['time'],
                          self.forecast_results['pressure'],
                          'k-', label='Pressão')
            axes[1,1].set_title('Pressão Média')
            axes[1,1].set_xlabel('Tempo (dias)')
            axes[1,1].set_ylabel('Pressão (psia)')
            axes[1,1].grid(True)
            axes[1,1].legend()
            
        plt.tight_layout()
        return fig
        
    def plot_scenario_comparison(self):
        """Plota comparação entre cenários."""
        if self.scenario_results is None:
            raise ValueError("Execute a análise de cenários primeiro")
            
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Produção de óleo
        for name, results in self.scenario_results.items():
            axes[0,0].plot(results['forecast']['time'],
                          results['forecast']['oil'],
                          label=name)
        axes[0,0].set_title('Produção de Óleo')
        axes[0,0].set_xlabel('Tempo (dias)')
        axes[0,0].set_ylabel('Taxa (bbl/d)')
        axes[0,0].grid(True)
        axes[0,0].legend()
        
        # Produção de água
        for name, results in self.scenario_results.items():
            axes[0,1].plot(results['forecast']['time'],
                          results['forecast']['water'],
                          label=name)
        axes[0,1].set_title('Produção de Água')
        axes[0,1].set_xlabel('Tempo (dias)')
        axes[0,1].set_ylabel('Taxa (bbl/d)')
        axes[0,1].grid(True)
        axes[0,1].legend()
        
        # Produção de gás
        for name, results in self.scenario_results.items():
            axes[1,0].plot(results['forecast']['time'],
                          results['forecast']['gas'],
                          label=name)
        axes[1,0].set_title('Produção de Gás')
        axes[1,0].set_xlabel('Tempo (dias)')
        axes[1,0].set_ylabel('Taxa (Mscf/d)')
        axes[1,0].grid(True)
        axes[1,0].legend()
        
        # Fator de recuperação
        recovery_factors = {
            name: results['metrics']['recovery_factor']
            for name, results in self.scenario_results.items()
        }
        axes[1,1].bar(recovery_factors.keys(),
                     recovery_factors.values())
        axes[1,1].set_title('Fator de Recuperação')
        axes[1,1].set_xlabel('Cenário')
        axes[1,1].set_ylabel('Fator de Recuperação')
        axes[1,1].grid(True)
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        return fig
        
    def plot_well_pattern(self):
        """Plota malha de poços otimizada."""
        if self.optimization_results is None:
            raise ValueError("Execute a otimização primeiro")
            
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Plotar poços
        for well in self.optimization_results['wells']:
            if well['type'] == 'producer':
                ax.plot(well['x'], well['y'], 'ro', label='Produtor')
            else:
                ax.plot(well['x'], well['y'], 'bo', label='Injetor')
                
        ax.set_title('Malha de Poços Otimizada')
        ax.set_xlabel('X (ft)')
        ax.set_ylabel('Y (ft)')
        ax.grid(True)
        
        # Adicionar legenda
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys())
        
        return fig
        
    def export_results(self, filename: str):
        """
        Exporta resultados da análise.
        
        Args:
            filename: Nome do arquivo de saída
        """
        results = {
            'forecast': self.forecast_results,
            'scenarios': self.scenario_results,
            'optimization': self.optimization_results,
            'eor': self.eor_results
        }
        
        pd.DataFrame(results).to_csv(filename, index=False) 