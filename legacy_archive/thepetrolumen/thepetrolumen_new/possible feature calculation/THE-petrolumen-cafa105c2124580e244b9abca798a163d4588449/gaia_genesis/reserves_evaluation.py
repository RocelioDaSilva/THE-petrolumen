import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import norm
import streamlit as st
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

class ReserveCategory(Enum):
    PROVED = "P1"
    PROBABLE = "P2"
    POSSIBLE = "P3"

@dataclass
class ReservesEstimate:
    category: ReserveCategory
    oil_volume: float  # em bbl
    gas_volume: float  # em mscf
    confidence_level: float  # probabilidade de sucesso
    recovery_factor: float
    net_present_value: float
    date: datetime

class ReservesEvaluation:
    def __init__(self):
        """
        Inicializa o sistema de avaliação de reservas.
        """
        self.logger = self._setup_logger()
        self.production_data = None
        self.economic_data = None
        self.reserves = None
        self.economic_results = None
        
    def _setup_logger(self) -> logging.Logger:
        """
        Configura o logger para o módulo.
        """
        logger = logging.getLogger('ReservesEvaluation')
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

    def load_production_data(self, data: pd.DataFrame,
                           time_col: str,
                           rate_cols: Dict[str, str],
                           pressure_col: Optional[str] = None):
        """
        Carrega dados de produção.
        
        Args:
            data: DataFrame com dados de produção
            time_col: Nome da coluna de tempo
            rate_cols: Dicionário com nomes das colunas de taxa para cada fase
            pressure_col: Nome da coluna de pressão (opcional)
        """
        self.production_data = {
            'time': data[time_col].values,
            'rates': {phase: data[col].values for phase, col in rate_cols.items()}
        }
        
        if pressure_col:
            self.production_data['pressure'] = data[pressure_col].values
            
    def calculate_reserves(self,
                         petrophysical_data: pd.DataFrame,
                         production_data: pd.DataFrame,
                         economic_params: Dict,
                         confidence_levels: Dict[ReserveCategory, float] = None) -> Dict[ReserveCategory, ReservesEstimate]:
        """
        Calcula reservas P1/P2/P3 segundo normas internacionais (SPE-PRMS).
        
        Args:
            petrophysical_data: Dados petrofísicos (porosidade, saturação, etc.)
            production_data: Dados de produção histórica
            economic_params: Parâmetros econômicos (preços, custos, etc.)
            confidence_levels: Níveis de confiança para cada categoria
            
        Returns:
            Dicionário com estimativas de reservas por categoria
        """
        if confidence_levels is None:
            confidence_levels = {
                ReserveCategory.PROVED: 0.9,    # 90% de confiança
                ReserveCategory.PROBABLE: 0.5,  # 50% de confiança
                ReserveCategory.POSSIBLE: 0.1   # 10% de confiança
            }

        # Calcular volumes originais
        ooip = self._calculate_ooip(petrophysical_data)
        ogip = self._calculate_ogip(petrophysical_data)
        
        # Calcular fatores de recuperação
        oil_rf = self._calculate_recovery_factor(
            production_data,
            petrophysical_data,
            'oil'
        )
        gas_rf = self._calculate_recovery_factor(
            production_data,
            petrophysical_data,
            'gas'
        )
        
        # Calcular reservas por categoria
        reserves = {}
        for category in ReserveCategory:
            confidence = confidence_levels[category]
            
            # Ajustar volumes pela confiança
            oil_volume = ooip * oil_rf * confidence
            gas_volume = ogip * gas_rf * confidence
            
            # Calcular valor presente líquido
            npv = self._calculate_npv(
                oil_volume,
                gas_volume,
                economic_params
            )
            
            reserves[category] = ReservesEstimate(
                category=category,
                oil_volume=oil_volume,
                gas_volume=gas_volume,
                confidence_level=confidence,
                recovery_factor=oil_rf if category == ReserveCategory.PROVED else oil_rf * confidence,
                net_present_value=npv,
                date=datetime.now()
            )
            
        self.reserves = reserves
        return reserves

    def _calculate_ooip(self, petrophysical_data: pd.DataFrame) -> float:
        """
        Calcula o volume original de óleo (OOIP).
        
        Args:
            petrophysical_data: Dados petrofísicos
            
        Returns:
            Volume original de óleo em bbl
        """
        # Fórmula: OOIP = A * h * φ * (1-Sw) * N/G * Bo
        area = petrophysical_data['area'].mean()  # acres
        thickness = petrophysical_data['net_pay'].mean()  # ft
        porosity = petrophysical_data['porosity'].mean() / 100  # fração
        water_saturation = petrophysical_data['water_saturation'].mean() / 100  # fração
        net_gross = petrophysical_data['net_gross'].mean()  # fração
        formation_volume_factor = 1.2  # bbl/stb
        
        ooip = 7758 * area * thickness * porosity * (1 - water_saturation) * net_gross / formation_volume_factor
        
        return ooip

    def _calculate_ogip(self, petrophysical_data: pd.DataFrame) -> float:
        """
        Calcula o volume original de gás (OGIP).
        
        Args:
            petrophysical_data: Dados petrofísicos
            
        Returns:
            Volume original de gás em mscf
        """
        # Fórmula: OGIP = A * h * φ * (1-Sw) * N/G * Bg
        area = petrophysical_data['area'].mean()  # acres
        thickness = petrophysical_data['net_pay'].mean()  # ft
        porosity = petrophysical_data['porosity'].mean() / 100  # fração
        water_saturation = petrophysical_data['water_saturation'].mean() / 100  # fração
        net_gross = petrophysical_data['net_gross'].mean()  # fração
        formation_volume_factor = 0.005  # mscf/scf
        
        ogip = 43560 * area * thickness * porosity * (1 - water_saturation) * net_gross / formation_volume_factor
        
        return ogip

    def _calculate_recovery_factor(self,
                                 production_data: pd.DataFrame,
                                 petrophysical_data: pd.DataFrame,
                                 fluid_type: str) -> float:
        """
        Calcula o fator de recuperação.
        
        Args:
            production_data: Dados de produção
            petrophysical_data: Dados petrofísicos
            fluid_type: Tipo de fluido ('oil' ou 'gas')
            
        Returns:
            Fator de recuperação (fração)
        """
        if fluid_type == 'oil':
            # Método de Arps para óleo
            qi = production_data['oil_rate'].iloc[0]  # taxa inicial
            di = self._calculate_decline_rate(production_data, 'oil')
            b = 0.3  # fator de Arps
            
            # Calcular EUR
            eur = qi / ((1 - b) * di)
            
            # Calcular fator de recuperação
            ooip = self._calculate_ooip(petrophysical_data)
            rf = eur / ooip
            
        else:  # gas
            # Método de Arps para gás
            qi = production_data['gas_rate'].iloc[0]  # taxa inicial
            di = self._calculate_decline_rate(production_data, 'gas')
            b = 0.5  # fator de Arps
            
            # Calcular EUR
            eur = qi / ((1 - b) * di)
            
            # Calcular fator de recuperação
            ogip = self._calculate_ogip(petrophysical_data)
            rf = eur / ogip
            
        return min(rf, 1.0)  # limitar a 100%

    def _calculate_decline_rate(self,
                              production_data: pd.DataFrame,
                              fluid_type: str) -> float:
        """
        Calcula a taxa de declínio.
        
        Args:
            production_data: Dados de produção
            fluid_type: Tipo de fluido ('oil' ou 'gas')
            
        Returns:
            Taxa de declínio (fração/ano)
        """
        rate_col = f'{fluid_type}_rate'
        time_col = 'time'
        
        # Ajustar curva de declínio
        rates = production_data[rate_col].values
        times = production_data[time_col].values
        
        # Regressão linear no espaço log
        log_rates = np.log(rates)
        slope, _ = np.polyfit(times, log_rates, 1)
        
        # Taxa de declínio anual
        decline_rate = -slope * 365  # converter para base anual
        
        return decline_rate

    def _calculate_npv(self,
                      oil_volume: float,
                      gas_volume: float,
                      economic_params: Dict) -> float:
        """
        Calcula o valor presente líquido (NPV).
        
        Args:
            oil_volume: Volume de óleo (bbl)
            gas_volume: Volume de gás (mscf)
            economic_params: Parâmetros econômicos
            
        Returns:
            Valor presente líquido
        """
        # Parâmetros econômicos
        oil_price = economic_params.get('oil_price', 70)  # USD/bbl
        gas_price = economic_params.get('gas_price', 3)   # USD/mscf
        opex = economic_params.get('opex', 15)           # USD/bbl
        capex = economic_params.get('capex', 0)          # USD
        discount_rate = economic_params.get('discount_rate', 0.1)  # 10%
        
        # Receitas
        oil_revenue = oil_volume * oil_price
        gas_revenue = gas_volume * gas_price
        total_revenue = oil_revenue + gas_revenue
        
        # Custos
        total_opex = oil_volume * opex
        total_capex = capex
        
        # Fluxo de caixa
        cash_flow = total_revenue - total_opex - total_capex
        
        # NPV
        npv = cash_flow / (1 + discount_rate)
        
        return npv

    def calculate_economic_metrics(self,
                                 oil_price: float,
                                 gas_price: float,
                                 opex: float,
                                 capex: float,
                                 discount_rate: float,
                                 tax_rate: float = 0.34) -> Dict:
        """
        Calcula métricas econômicas.
        
        Args:
            oil_price: Preço do óleo ($/bbl)
            gas_price: Preço do gás ($/Mscf)
            opex: Custo operacional ($/bbl)
            capex: Investimento inicial ($)
            discount_rate: Taxa de desconto (%/ano)
            tax_rate: Taxa de impostos
            
        Returns:
            Dicionário com métricas econômicas
        """
        if self.reserves is None:
            raise ValueError("Calcule as reservas primeiro")
            
        # Calcular receita
        revenue = {
            'oil': self.reserves['P1']['oil'] * oil_price,
            'gas': self.reserves['P1']['gas'] * gas_price
        }
        total_revenue = sum(revenue.values())
        
        # Calcular custos
        total_production = self.reserves['P1']['oil'] + self.reserves['P1']['water']
        opex_total = total_production * opex
        
        # Calcular fluxo de caixa
        cash_flow = total_revenue - opex_total - capex
        
        # Calcular impostos
        taxes = cash_flow * tax_rate
        net_cash_flow = cash_flow - taxes
        
        # Calcular métricas
        npv = net_cash_flow / (1 + discount_rate/100)
        roi = (net_cash_flow - capex) / capex * 100
        payback = capex / net_cash_flow if net_cash_flow > 0 else float('inf')
        
        results = {
            'revenue': revenue,
            'total_revenue': total_revenue,
            'opex': opex_total,
            'capex': capex,
            'taxes': taxes,
            'net_cash_flow': net_cash_flow,
            'npv': npv,
            'roi': roi,
            'payback': payback
        }
        
        self.economic_results = results
        return results
        
    def run_scenario_analysis(self,
                            base_case: Dict,
                            scenarios: List[Dict]) -> Dict:
        """
        Executa análise de cenários.
        
        Args:
            base_case: Dicionário com parâmetros do caso base
            scenarios: Lista de dicionários com parâmetros dos cenários
            
        Returns:
            Dicionário com resultados dos cenários
        """
        results = {}
        
        # Caso base
        results['base'] = self.calculate_economic_metrics(**base_case)
        
        # Cenários
        for i, scenario in enumerate(scenarios):
            results[f'scenario_{i+1}'] = self.calculate_economic_metrics(**scenario)
            
        return results
        
    def generate_technical_report(self) -> str:
        """Gera relatório técnico."""
        if self.reserves is None or self.economic_results is None:
            raise ValueError("Execute as análises primeiro")
            
        report = []
        report.append("# Relatório Técnico de Reservas e Análise Econômica\n")
        
        # Reservas
        report.append("## Reservas\n")
        for category, phases in self.reserves.items():
            report.append(f"### {category}\n")
            for phase, value in phases.items():
                report.append(f"- {phase.capitalize()}: {value:,.0f} bbl/Mscf\n")
                
        # Métricas Econômicas
        report.append("## Análise Econômica\n")
        report.append("### Métricas Principais\n")
        report.append(f"- NPV: ${self.economic_results['npv']:,.2f}\n")
        report.append(f"- ROI: {self.economic_results['roi']:.1f}%\n")
        report.append(f"- Payback: {self.economic_results['payback']:.1f} anos\n")
        
        # Receitas e Custos
        report.append("### Receitas e Custos\n")
        report.append(f"- Receita Total: ${self.economic_results['total_revenue']:,.2f}\n")
        report.append(f"- OPEX: ${self.economic_results['opex']:,.2f}\n")
        report.append(f"- CAPEX: ${self.economic_results['capex']:,.2f}\n")
        report.append(f"- Impostos: ${self.economic_results['taxes']:,.2f}\n")
        
        return "\n".join(report)
        
    def generate_executive_summary(self) -> str:
        """Gera resumo executivo."""
        if self.reserves is None or self.economic_results is None:
            raise ValueError("Execute as análises primeiro")
            
        summary = []
        summary.append("# Resumo Executivo\n")
        
        # Reservas Proved
        summary.append("## Reservas Proved (P1)\n")
        for phase, value in self.reserves['P1'].items():
            summary.append(f"- {phase.capitalize()}: {value:,.0f} bbl/Mscf\n")
            
        # Métricas Econômicas
        summary.append("## Análise Econômica\n")
        summary.append(f"- NPV: ${self.economic_results['npv']:,.2f}\n")
        summary.append(f"- ROI: {self.economic_results['roi']:.1f}%\n")
        summary.append(f"- Payback: {self.economic_results['payback']:.1f} anos\n")
        
        return "\n".join(summary)
        
    def plot_reserves_distribution(self) -> plt.Figure:
        """Plota distribuição das reservas."""
        if self.reserves is None:
            raise ValueError("Calcule as reservas primeiro")
            
        fig, ax = plt.subplots(figsize=(10, 6))
        
        categories = list(self.reserves.keys())
        phases = list(self.reserves['P1'].keys())
        
        x = np.arange(len(phases))
        width = 0.25
        
        for i, category in enumerate(categories):
            values = [self.reserves[category][phase] for phase in phases]
            ax.bar(x + i*width, values, width, label=category)
            
        ax.set_xlabel('Fase')
        ax.set_ylabel('Reservas (bbl/Mscf)')
        ax.set_title('Distribuição de Reservas por Categoria')
        ax.set_xticks(x + width)
        ax.set_xticklabels(phases)
        ax.legend()
        
        return fig
        
    def plot_economic_metrics(self) -> plt.Figure:
        """Plota métricas econômicas."""
        if self.economic_results is None:
            raise ValueError("Calcule as métricas econômicas primeiro")
            
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Receitas e Custos
        labels = ['Receita', 'OPEX', 'CAPEX', 'Impostos']
        values = [
            self.economic_results['total_revenue'],
            self.economic_results['opex'],
            self.economic_results['capex'],
            self.economic_results['taxes']
        ]
        
        ax1.bar(labels, values)
        ax1.set_title('Receitas e Custos')
        ax1.set_ylabel('$')
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # Métricas
        metrics = ['NPV', 'ROI', 'Payback']
        values = [
            self.economic_results['npv'],
            self.economic_results['roi'],
            self.economic_results['payback']
        ]
        
        ax2.bar(metrics, values)
        ax2.set_title('Métricas Econômicas')
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        return fig

    def generate_reserves_report(self,
                               reserves: Dict[ReserveCategory, ReservesEstimate],
                               output_path: str):
        """
        Gera relatório de reservas.
        
        Args:
            reserves: Dicionário com estimativas de reservas
            output_path: Caminho para salvar o relatório
        """
        report = []
        report.append("RELATÓRIO DE RESERVAS")
        report.append("=" * 50)
        report.append(f"Data: {datetime.now().strftime('%Y-%m-%d')}")
        report.append("\n")
        
        # Tabela de reservas
        report.append("ESTIMATIVAS DE RESERVAS")
        report.append("-" * 50)
        report.append(f"{'Categoria':<10} {'Óleo (MMbbl)':<15} {'Gás (Bcf)':<15} {'NPV (MM$)':<15}")
        report.append("-" * 50)
        
        for category, estimate in reserves.items():
            report.append(
                f"{category.value:<10} "
                f"{estimate.oil_volume/1e6:>15.2f} "
                f"{estimate.gas_volume/1e3:>15.2f} "
                f"{estimate.net_present_value/1e6:>15.2f}"
            )
            
        # Salvar relatório
        with open(output_path, 'w') as f:
            f.write('\n'.join(report))
            
        self.logger.info(f"Relatório de reservas gerado: {output_path}") 