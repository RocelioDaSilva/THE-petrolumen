# Integrated Dashboard — Implementation Steps

1. Criar ambiente virtual e instalar dependências:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r ../requirements.txt
pip install streamlit
```

2. Colocar `data/sample_dashboard.csv` com colunas `date,production,ROP,pressure`.
3. Rodar app:

```bash
cd "mini oil and gas projects/integrated_dashboard_python"
streamlit run app.py
```

4. Integrar módulos `etl.py` e `models.py` com o `app.py` e adicionar exemplos no `assets/`.
