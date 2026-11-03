# Production LSTM — Implementation Steps

1. Criar ambiente virtual e instalar dependências:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r ../requirements.txt
pip install tensorflow
```

2. Colocar `data/example_production.csv` com `date,production`.
3. Treinar:

```bash
python train_lstm.py --data data/example_production.csv
```

4. Salvar modelo em `models/` e avaliar previsões; ajustar janela (`window`) e hiperparâmetros.
