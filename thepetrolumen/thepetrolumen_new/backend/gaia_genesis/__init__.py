"""
Gaia Genesis - Biblioteca para Engenharia de Reservatórios de Petróleo

Módulos:
- reservoir_engineering: Engenharia de reservatórios
- data: Gerenciamento de dados
- geology: Geologia
- pvt: Propriedades de fluidos
"""

from gaia_genesis.reservoir_engineering import HistoryMatching  # Corrected class name

# Corrected import for StaticModeling:
from gaia_genesis.static_modeling import StaticModeling

# Corrected import for FlowSimulation:
from gaia_genesis.flow_simulation import FlowSimulation

__version__ = "0.1.0"
__author__ = "Gaia Genesis Team"

__all__ = [
    "StaticModeling",  # Use the correct class name
    "FlowSimulation",  # Use the correct class name
    # 'Geostatistics', # Class not found, removing from __all__
    "HistoryMatching",  # Corrected class name
]
