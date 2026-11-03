Nodal Analysis

Objetivo
- Implementar um fluxo simples de análise nodal: IPR (inflow) vs TPR (tubing performance) e encontrar o ponto de operação (interseção).

Pré-requisitos
- `pip install -r ../requirements.txt`

Passo-a-passo
1. Preparar dados: P_reservoir (psi), elasticidade do poço, parâmetros de poço/tubulação.
2. Implementar IPR (Vogel / Arps simplificado) e TPR (perda de carga na coluna) como funções Python.
3. Usar `scipy.optimize` para encontrar o ponto onde IPR(q) - TPR(q) = 0.
4. Plotar IPR/TPR e marcar o ponto de operação.

Arquivo principal: `nodal_analysis.py` (esqueleto incluso).