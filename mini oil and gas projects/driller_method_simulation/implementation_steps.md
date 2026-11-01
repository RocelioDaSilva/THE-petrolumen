# Driller Method Simulation — Implementation Steps

1. Criar ambiente virtual e instalar dependências:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r ../requirements.txt
```

2. Colocar `data/driller_example.csv` (opcional) para parâmetros iniciais.
3. Executar simulação:

```bash
python driller_sim.py
```

4. Gerar gráficos MD vs tempo e ROP vs tempo; ajustar modelo de degradação do bit.
