# ROP Prediction — Implementation Steps

1. Criar ambiente virtual e instalar dependências:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r ../requirements.txt
pip install xgboost
```

2. Colocar `data/example_rop.csv` com colunas `time,WOB,RPM,torque,mud_weight,bit_type,ROP`.
3. Rodar treino/avaliação:

```bash
python rop_prediction.py --data data/example_rop.csv
```

4. Salvar e versionar o modelo; preparar script de inferência em tempo real.
