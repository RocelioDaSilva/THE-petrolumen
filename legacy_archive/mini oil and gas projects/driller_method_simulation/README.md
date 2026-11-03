Driller Method Simulation

Objetivo
- Simular um poço perfurando segundo o método do perfurador, modelando avanço MD por tempo, WOB, RPM e consumo de bit.

Prerequisitos
- `pip install -r ../requirements.txt`

Passos
1. Definir um loop de tempo com dt e atualizar ROP baseado em WOB/RPM/bit_efficiency
2. Registrar consumo de bit e degradacao
3. Gerar gráficos de MD vs tempo, ROP vs tempo

Arquivo principal: `driller_sim.py`