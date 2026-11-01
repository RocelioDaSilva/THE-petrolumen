Petrophysical Analysis (LAS reader)

Objetivo
- Ler arquivos LAS, extrair logs e calcular porosidade, volume de argila, saturação (Sh/Sw) em abordagens simplificadas.

Pré-requisitos
- `pip install -r ../requirements.txt`
- `pip install lasio`

Passos
1. Colocar arquivos LAS em `data/`
2. Rodar `python las_reader.py --file data/example.las`
3. Ferramentas: `lasio`, `pandas`, `numpy`

Arquivo principal: `las_reader.py`