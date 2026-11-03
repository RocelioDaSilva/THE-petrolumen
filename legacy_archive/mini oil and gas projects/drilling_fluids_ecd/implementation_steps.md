# Drilling Fluids / ECD — Implementation Steps

1. Criar ambiente virtual e instalar dependências:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r ../requirements.txt
```

2. Colocar `data/ecd_example.csv` com `mud_weight_kg_m3,hole_depth_m,pump_rate_l_min`.
3. Executar:

```bash
python ecd_calc.py
```

4. Verificar resultados de pressão e ECD; adicionar cenários de velocidade anular e perda de carga.
