# Petrophysical Analysis — Implementation Steps

1. Criar ambiente virtual e instalar dependências:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r ../requirements.txt
pip install lasio
```

2. Colocar logs de exemplo em `data/example_logs.csv` (ou arquivos LAS em `data/`).
3. Executar:

```bash
python las_reader.py --file data/example.las
# ou adaptar para CSV e usar pandas
```

4. Calcular porosidade, gravidade, saturação; salvar `las_export.csv` e adicionar EDA em `notebooks/`.
