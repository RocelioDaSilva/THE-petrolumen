ROP Prediction (XGBoost)

Objetivo
- Prever Rate Of Penetration (ROP) usando features de perfuração (WOB, RPM, bit type, mud properties).

Pré-requisitos
- `pip install -r ../requirements.txt`

Passo-a-passo
1. Reunir dados de perfuração CSV com colunas: time, WOB, RPM, torque, mud_weight, bit_type, ROP
2. Feature engineering: rolling means, lag features, categorical encoding para bit_type
3. Treinar `xgboost.XGBRegressor`, avaliar com RMSE/MAE
4. Salvar modelo e preparar script de inferência para operações em tempo real

Arquivo principal: `rop_model.py` (esqueleto incluído `rop_prediction.py`).