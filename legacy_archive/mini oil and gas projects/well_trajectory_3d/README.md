Well Trajectory 3D

Objetivo
- Simular e visualizar trajetórias de poços em 3D usando `plotly`.

Pré-requisitos
- `pip install -r ../requirements.txt`
- `pip install pyproj` (opcional)

Passo-a-passo
1. Preparar perfil: CSV com colunas `md`, `inclination_deg`, `azimuth_deg`.
2. Converter para coordenadas cartesianas (x,y,z) com fórmula de sondagem.
3. Visualizar com `plotly.graph_objects` em 3D.

Arquivo principal: `trajectory.py`Well Trajectory 3D

Objetivo
- Calcular coordenadas (X,Y,Z) a partir de surveys MD/Inclinacao/Azimute usando o método de curvatura mínima e visualizar em 3D.

Pré-requisitos
- `pip install -r ../requirements.txt`

Passo-a-passo
1. Preparar CSV: colunas `MD`, `INC_deg`, `AZI_deg` (medidas em graus)
2. Implementar fórmula de curvatura mínima para segmentos consecutivos
3. Calcular X,Y,Z acumulados e salvar em CSV
4. Visualizar com `plotly` (scatter3d)

Arquivo principal: `well_trajectory_3d.py` (esqueleto incluso).