"""
Módulo de Engenharia de Reservatórios.

Este módulo contém funcionalidades para:
- Modelagem estática e dinâmica de reservatórios
- Simulação de fluxo multifásico
- Ajuste de histórico e análise de incertezas
- Caracterização geológica e geoestatística
- Predição de produção futura
"""

from .pvt import PVTProperties
from .simulation import (
    ReservoirSimulation,
    CompositionalSimulation,
    ThermalSimulation
)
from .material_balance import MaterialBalance
from .well_testing import WellTesting
from .decline_analysis import DeclineAnalysis
from .history_matching import HistoryMatching
from .visualization import ReservoirVisualization
from .geological_integration import GeologicalData
from .economics import EconomicAnalysis
from gaia_genesis.reservoir_engineering.static_modeling.static_model import StaticModel
from gaia_genesis.reservoir_engineering.flow_simulation.flow_simulator import FlowSimulator
from gaia_genesis.reservoir_engineering.geostatistics.geostatistics import Geostatistics
from gaia_genesis.reservoir_engineering.history_matching.history_matcher import HistoryMatcher

__all__ = [
    'PVTProperties',
    'ReservoirSimulation',
    'CompositionalSimulation',
    'ThermalSimulation',
    'MaterialBalance',
    'WellTesting',
    'DeclineAnalysis',
    'HistoryMatching',
    'ReservoirVisualization',
    'GeologicalData',
    'EconomicAnalysis',
    'StaticModel',
    'FlowSimulator',
    'Geostatistics',
    'HistoryMatcher'
] 