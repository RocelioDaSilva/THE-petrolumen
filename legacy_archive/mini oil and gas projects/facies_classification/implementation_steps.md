# Facies Classification — Implementation Steps

1. Criar ambiente virtual e instalar dependências:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r ../requirements.txt
```

2. Colocar `data/example_facies.csv` com colunas `depth,gamma,resistivity,density,porosity,facies`.
3. Rodar baseline:

```bash
python facies_classification.py --data data/example_facies.csv
```

4. Avaliar métricas, experimentar `RandomForest` e depois CNN (janelas) se tiver dados suficientes.
5. Adicionar `notebooks/` com EDA e pipeline de pré-processamento.
