Decline Curve Analysis App

Objetivo
- App interativo (Streamlit) para ajustar curvas de declínio (exponential, hyperbolic, harmonic) e exportar previsões.

Pré-requisitos
- Python 3.9+; virtualenv
- Instalar dependências: `pip install -r ../requirements.txt` e `pip install scipy`

Formato de dados esperado
- CSV com colunas: `date` (YYYY-MM-DD) ou `month_index`, `production` (bbl/day) e opcional `well`

Passo-a-passo
1. Criar ambiente virtual:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install scipy
```

2. Executar o app:

```bash
cd "mini oil and gas projects/decline_curve_app"
streamlit run app.py
```

3. No app: carregar CSV, escolher poço (se aplicável), escolher modelo (exponential/hyperbolic/harmonic), ajustar e visualizar curva.
4. Exportar previsões para CSV ou imagem.

Implementação (nível técnico)
- Use `scipy.optimize.curve_fit` para ajustar modelos paramétricos.
- Plots com `plotly` para interatividade.
- Calcular previsão acumulada e receita estimada se preço for fornecido.

Arquivo principal: `app.py` (esqueleto pronto).