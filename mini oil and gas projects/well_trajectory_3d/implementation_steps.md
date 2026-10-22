# Well Trajectory 3D — Implementation Steps

1. Criar ambiente virtual e instalar dependências:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r ../requirements.txt
pip install pyproj
```

2. Colocar `data/example_survey.csv` com colunas `md,inc,azi`.
3. Executar:

```bash
python trajectory.py --data data/example_survey.csv
```

4. Visualizar a trajetória 3D com o `plotly` gerado.
