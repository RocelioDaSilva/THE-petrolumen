Event Detection (Anomaly / Kick Detection)

Objetivo
- Detectar eventos anômalos em séries temporais de perfuração (pressão, torque, flow).

Pré-requisitos
- `pip install -r ../requirements.txt`

Passos
1. Preparar dados: CSV com timestamp e sinais (pressure, flow, torque)
2. Aplicar filtros (rolling median) e detectar mudanças abruptas usando z-score ou IsolationForest
3. Produzir alertas com thresholds e geração de um relatório de eventos

Arquivo principal: `event_detection.py`