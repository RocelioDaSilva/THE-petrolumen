# Event Detection — Implementation Steps

1. Criar ambiente virtual e instalar dependências:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r ../requirements.txt
```

2. Colocar `data/example_timeseries.csv` com `timestamp,pressure,flow,torque`.
3. Executar:

```bash
python event_detection.py --data data/example_timeseries.csv
```

4. Ajustar parâmetros de janela (`window`) e thresholds para aumentar sensibilidade/falso-positivos.
