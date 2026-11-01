# Volve Data Analysis — Implementation Steps

1. Criar ambiente virtual e instalar dependências:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r ../requirements.txt
```

2. Colocar dados do Volve em `data/` (ex.: `data/sample_volve.csv`).
3. Rodar EDA básico:

```bash
python volve_eda.py --data data/
```

4. Criar notebooks com análises replicáveis e salvar figuras em `notebooks/`.
