# Inspection Checklist — Implementation Steps

1. Criar ambiente virtual e instalar dependências:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r ../requirements.txt
pip install streamlit
```

2. (Opcional) Colocar `data/inspection_example.csv` para importar/exportar relatórios.
3. Rodar app:

```bash
cd "mini oil and gas projects/inspection_checklist_streamlit"
streamlit run checklist.py
```

4. Testar exportação CSV e integração com fotos (salvar em `assets/`).
