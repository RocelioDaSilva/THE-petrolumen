# Decline Curve App — Implementation Steps

1. Criar ambiente virtual e instalar dependências:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r ../requirements.txt
pip install scipy
```

2. Colocar um CSV de exemplo em `data/example_production.csv` (ex.: `date,production[,well]`).
3. Rodar o app:

```bash
cd "mini oil and gas projects/decline_curve_app"
streamlit run app.py
```

4. No app: carregar CSV, selecionar modelo (exponential/hyperbolic/harmonic), ajustar e exportar previsões.
5. Melhorias: adicionar `examples/` com CSVs de teste, adicionar testes unitários para funções de ajuste, e criar um notebook demonstrativo.
