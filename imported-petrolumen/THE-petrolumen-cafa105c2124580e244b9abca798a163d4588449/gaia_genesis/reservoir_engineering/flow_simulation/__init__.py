"""
Módulo para simulação de fluxo multifásico.

Funcionalidades principais:
- Configuração de simulação
- Solução numérica com PETSc
- Cálculo de transmissibilidades e fluxos
- Visualização de resultados
- Exportação de resultados

Classes:
- FlowSimulator: Simulador de fluxo multifásico com resolução numérica
- ReservoirSimulator: Simulador completo com funcionalidades similares ao Navigator (Rock Flow Dynamics)
  incluindo modelagem de malhas complexas, visualização 3D e análise de sensibilidade
"""

from gaia_genesis.reservoir_engineering.flow_simulation.flow_simulator import FlowSimulator
from .reservoir_simulator import ReservoirSimulator

__all__ = ['FlowSimulator', 'ReservoirSimulator'] 