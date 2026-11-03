Drilling Fluids ECD Calculator

Objetivo
- Calcular Equivalent Circulating Density (ECD) e pressão hidrostática para diferentes cenários de circulação e BHA.

Pré-requisitos
- `pip install -r ../requirements.txt`

Passo-a-passo
1. Preparar inputs: mud_weight_kg_m3, hole_depth_m, pump_rate_l_min, annular_velocity
2. Calcular ECD = mud_weight + (pressure_losses / (g * rho_ref)) — usar fórmulas simplificadas
3. Gerar relatório e salvar tabela CSV

Arquivo principal: `ecd_calc.py`