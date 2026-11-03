Production Forecast with LSTM

Objetivo
- Treinar uma LSTM simples para previsão de produção (séries temporais).

Pré-requisitos
- `pip install -r ../requirements.txt`

Passos
1. Preparar série temporal de produção (daily/weekly) em CSV com colunas `date, production`
2. Normalizar, criar sequências (window) e dividir treino/teste
3. Treinar LSTM com `tensorflow.keras` e salvar modelo

Arquivo principal: `train_lstm.py`