import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import norm
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import streamlit as st

class ProductionAnalysis:
    def __init__(self):
        """Inicializa o analisador de produção."""
        self.historical_data = None
        self.dca_results = None
        self.mbal_results = None
        self.forecast_results = None
        self.uncertainty_results = None
        
    def load_historical_data(self, data: pd.DataFrame,
                           time_col: str,
                           rate_cols: Dict[str, str],
                           pressure_col: Optional[str] = None):
        """
        Carrega dados históricos de produção.
        
        Args:
            data: DataFrame com dados históricos
            time_col: Nome da coluna de tempo
            rate_cols: Dicionário com nomes das colunas de taxa para cada fase
            pressure_col: Nome da coluna de pressão (opcional)
        """
        self.historical_data = {
            'time': data[time_col].values,
            'rates': {phase: data[col].values for phase, col in rate_cols.items()}
        }
        
        if pressure_col:
            self.historical_data['pressure'] = data[pressure_col].values
            
    def fit_decline_curves(self, phase: str,
                          decline_type: str = 'hyperbolic',
                          n_samples: int = 1000) -> Dict:
        """
        Ajusta curvas de declínio para uma fase.
        
        Args:
            phase: Fase para ajuste ('oil', 'water', 'gas')
            decline_type: Tipo de declínio ('exponential', 'hyperbolic', 'harmonic')
            n_samples: Número de amostras para análise de incerteza
            
        Returns:
            Dicionário com resultados do ajuste
        """
        if self.historical_data is None:
            raise ValueError("Carregue os dados históricos primeiro")
            
        time = self.historical_data['time']
        rate = self.historical_data['rates'][phase]
        
        # Definir função de declínio
        if decline_type == 'exponential':
            def decline_func(t, qi, Di):
                return qi * np.exp(-Di * t)
            p0 = [np.max(rate), 0.1]  # Valores iniciais
        elif decline_type == 'hyperbolic':
            def decline_func(t, qi, Di, b):
                return qi * (1 + b * Di * t) ** (-1/b)
            p0 = [np.max(rate), 0.1, 0.5]  # Valores iniciais
        else:  # harmonic
            def decline_func(t, qi, Di):
                return qi / (1 + Di * t)
            p0 = [np.max(rate), 0.1]  # Valores iniciais
            
        # Ajustar curva
        popt, pcov = curve_fit(decline_func, time, rate, p0=p0)
        
        # Calcular incerteza
        if n_samples > 0:
            samples = np.random.multivariate_normal(popt, pcov, n_samples)
            predictions = np.array([decline_func(time, *params) for params in samples])
            uncertainty = {
                'mean': np.mean(predictions, axis=0),
                'std': np.std(predictions, axis=0),
                'p10': np.percentile(predictions, 10, axis=0),
                'p90': np.percentile(predictions, 90, axis=0)
            }
        else:
            uncertainty = None
            
        # Preparar resultados
        results = {
            'type': decline_type,
            'parameters': dict(zip(['qi', 'Di', 'b'][:len(popt)], popt)),
            'covariance': pcov,
            'uncertainty': uncertainty,
            'fit': decline_func(time, *popt)
        }
        
        self.dca_results = results
        return results
        
    def calculate_material_balance(self,
                                 pvt_data: pd.DataFrame,
                                 reservoir_type: str,
                                 initial_pressure: float,
                                 initial_temperature: float,
                                 initial_saturation: Dict[str, float],
                                 rock_properties: Dict[str, float]) -> Dict:
        """
        Calcula balanço de materiais.
        
        Args:
            pvt_data: DataFrame com dados PVT
            reservoir_type: Tipo de reservatório ('oil' ou 'gas')
            initial_pressure: Pressão inicial
            initial_temperature: Temperatura inicial
            initial_saturation: Saturações iniciais
            rock_properties: Propriedades da rocha
            
        Returns:
            Dicionário com resultados do balanço de materiais
        """
        if self.historical_data is None:
            raise ValueError("Carregue os dados históricos primeiro")
            
        # Interpolar propriedades PVT
        pressure = self.historical_data['pressure']
        pvt_props = {}
        for col in pvt_data.columns:
            if col != 'pressure':
                pvt_props[col] = np.interp(pressure, pvt_data['pressure'], pvt_data[col])
                
        # Calcular balanço de materiais
        if reservoir_type == 'oil':
            # Fator de volume de formação do óleo
            Bo = pvt_props['Bo']
            # Razão gás-óleo em solução
            Rs = pvt_props['Rs']
            # Fator de volume de formação do gás
            Bg = pvt_props['Bg']
            
            # Produção acumulada
            Np = np.cumsum(self.historical_data['rates']['oil'])
            Gp = np.cumsum(self.historical_data['rates']['gas'])
            Wp = np.cumsum(self.historical_data['rates']['water'])
            
            # Calcular OOIP
            F = Np * (Bo + (Gp/Np - Rs) * Bg) + Wp * pvt_props['Bw']
            Eo = Bo - rock_properties['Bo_initial'] + (Rs - rock_properties['Rs_initial']) * Bg
            Ew = rock_properties['Bw_initial'] * rock_properties['cw'] * (initial_pressure - pressure)
            Ef = rock_properties['cf'] * (initial_pressure - pressure)
            
            OOIP = F / (Eo + Ew + Ef)
            
            results = {
                'OOIP': OOIP,
                'F': F,
                'Eo': Eo,
                'Ew': Ew,
                'Ef': Ef
            }
            
        else:  # gas
            # Fator de volume de formação do gás
            Bg = pvt_props['Bg']
            
            # Produção acumulada
            Gp = np.cumsum(self.historical_data['rates']['gas'])
            Wp = np.cumsum(self.historical_data['rates']['water'])
            
            # Calcular OGIP
            F = Gp * Bg + Wp * pvt_props['Bw']
            Eg = Bg - rock_properties['Bg_initial']
            Ew = rock_properties['Bw_initial'] * rock_properties['cw'] * (initial_pressure - pressure)
            Ef = rock_properties['cf'] * (initial_pressure - pressure)
            
            OGIP = F / (Eg + Ew + Ef)
            
            results = {
                'OGIP': OGIP,
                'F': F,
                'Eg': Eg,
                'Ew': Ew,
                'Ef': Ef
            }
            
        self.mbal_results = results
        return results
        
    def forecast_with_uncertainty(self,
                                forecast_period: int,
                                dt: float,
                                n_samples: int = 1000) -> Dict:
        """
        Realiza previsão com análise de incerteza.
        
        Args:
            forecast_period: Período de previsão em dias
            dt: Passo de tempo em dias
            n_samples: Número de amostras para análise de incerteza
            
        Returns:
            Dicionário com resultados da previsão
        """
        if self.dca_results is None:
            raise ValueError("Execute o ajuste de curvas de declínio primeiro")
            
        # Gerar tempo de previsão
        time = np.arange(0, forecast_period + dt, dt)
        
        # Gerar amostras dos parâmetros
        samples = np.random.multivariate_normal(
            list(self.dca_results['parameters'].values()),
            self.dca_results['covariance'],
            n_samples
        )
        
        # Calcular previsões
        if self.dca_results['type'] == 'exponential':
            predictions = np.array([
                samples[:, 0] * np.exp(-samples[:, 1] * t)
                for t in time
            ]).T
        elif self.dca_results['type'] == 'hyperbolic':
            predictions = np.array([
                samples[:, 0] * (1 + samples[:, 2] * samples[:, 1] * t) ** (-1/samples[:, 2])
                for t in time
            ]).T
        else:  # harmonic
            predictions = np.array([
                samples[:, 0] / (1 + samples[:, 1] * t)
                for t in time
            ]).T
            
        # Calcular estatísticas
        forecast = {
            'time': time,
            'mean': np.mean(predictions, axis=0),
            'std': np.std(predictions, axis=0),
            'p10': np.percentile(predictions, 10, axis=0),
            'p90': np.percentile(predictions, 90, axis=0),
            'samples': predictions
        }
        
        self.forecast_results = forecast
        return forecast
        
    def compare_models(self, models: Dict[str, np.ndarray]) -> Dict:
        """
        Compara diferentes modelos com dados reais.
        
        Args:
            models: Dicionário com previsões de diferentes modelos
            
        Returns:
            Dicionário com métricas de comparação
        """
        if self.historical_data is None:
            raise ValueError("Carregue os dados históricos primeiro")
            
        results = {}
        for name, predictions in models.items():
            # Calcular métricas
            mse = np.mean((predictions - self.historical_data['rates']['oil'])**2)
            rmse = np.sqrt(mse)
            mae = np.mean(np.abs(predictions - self.historical_data['rates']['oil']))
            r2 = 1 - mse / np.var(self.historical_data['rates']['oil'])
            
            results[name] = {
                'MSE': mse,
                'RMSE': rmse,
                'MAE': mae,
                'R2': r2
            }
            
        return results
        
    def plot_decline_curves(self, phase: str) -> plt.Figure:
        """Plota curvas de declínio."""
        if self.dca_results is None:
            raise ValueError("Execute o ajuste de curvas de declínio primeiro")
            
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plotar dados históricos
        ax.scatter(self.historical_data['time'],
                  self.historical_data['rates'][phase],
                  label='Dados Históricos')
        
        # Plotar ajuste
        ax.plot(self.historical_data['time'],
                self.dca_results['fit'],
                'r-', label='Ajuste')
        
        # Plotar incerteza
        if self.dca_results['uncertainty']:
            ax.fill_between(
                self.historical_data['time'],
                self.dca_results['uncertainty']['p10'],
                self.dca_results['uncertainty']['p90'],
                alpha=0.2, label='Incerteza (P10-P90)'
            )
            
        ax.set_xlabel('Tempo (dias)')
        ax.set_ylabel(f'Taxa de {phase} (bbl/d)')
        ax.set_title(f'Curva de Declínio - {phase}')
        ax.grid(True)
        ax.legend()
        
        return fig
        
    def plot_material_balance(self) -> plt.Figure:
        """Plota resultados do balanço de materiais."""
        if self.mbal_results is None:
            raise ValueError("Execute o balanço de materiais primeiro")
            
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plotar F vs E
        ax.scatter(self.mbal_results['F'],
                  self.mbal_results['Eo'] + self.mbal_results['Ew'] + self.mbal_results['Ef'],
                  label='Dados')
        
        # Ajustar linha
        slope, _ = np.polyfit(
            self.mbal_results['Eo'] + self.mbal_results['Ew'] + self.mbal_results['Ef'],
            self.mbal_results['F'],
            1
        )
        
        x = np.array([0, np.max(self.mbal_results['F'])])
        ax.plot(x, slope * x, 'r-', label=f'Ajuste (OOIP = {slope:.0f} STB)')
        
        ax.set_xlabel('E')
        ax.set_ylabel('F')
        ax.set_title('Balanço de Materiais')
        ax.grid(True)
        ax.legend()
        
        return fig
        
    def plot_forecast(self) -> plt.Figure:
        """Plota resultados da previsão."""
        if self.forecast_results is None:
            raise ValueError("Execute a previsão primeiro")
            
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plotar dados históricos
        ax.scatter(self.historical_data['time'],
                  self.historical_data['rates']['oil'],
                  label='Dados Históricos')
        
        # Plotar previsão
        ax.plot(self.forecast_results['time'],
                self.forecast_results['mean'],
                'r-', label='Previsão')
        
        # Plotar incerteza
        ax.fill_between(
            self.forecast_results['time'],
            self.forecast_results['p10'],
            self.forecast_results['p90'],
            alpha=0.2, label='Incerteza (P10-P90)'
        )
        
        ax.set_xlabel('Tempo (dias)')
        ax.set_ylabel('Taxa de Óleo (bbl/d)')
        ax.set_title('Previsão de Produção')
        ax.grid(True)
        ax.legend()
        
        return fig
        
    def plot_model_comparison(self, models: Dict[str, np.ndarray]) -> plt.Figure:
        """Plota comparação entre modelos."""
        if self.historical_data is None:
            raise ValueError("Carregue os dados históricos primeiro")
            
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plotar dados históricos
        ax.scatter(self.historical_data['time'],
                  self.historical_data['rates']['oil'],
                  label='Dados Reais')
        
        # Plotar cada modelo
        for name, predictions in models.items():
            ax.plot(self.historical_data['time'],
                   predictions,
                   label=name)
            
        ax.set_xlabel('Tempo (dias)')
        ax.set_ylabel('Taxa de Óleo (bbl/d)')
        ax.set_title('Comparação de Modelos')
        ax.grid(True)
        ax.legend()
        
        return fig
        
    def export_results(self, filename: str):
        """
        Exporta resultados da análise.
        
        Args:
            filename: Nome do arquivo de saída
        """
        results = {
            'dca': self.dca_results,
            'mbal': self.mbal_results,
            'forecast': self.forecast_results
        }
        
        pd.DataFrame(results).to_csv(filename, index=False) 