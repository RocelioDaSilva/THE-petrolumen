"""
Decline Curve Analysis - Streamlit app skeleton
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.optimize import curve_fit

st.set_page_config(page_title="Decline Curve App")

def exponential(t, qi, di):
    return qi * np.exp(-di * t)

def hyperbolic(t, qi, di, b):
    return qi / ((1 + b * di * t) ** (1 / b))

def harmonic(t, qi, di):
    return qi / (1 + di * t)

st.title("Decline Curve Analysis")
uploaded = st.file_uploader("Upload production CSV", type=["csv"]) 

if uploaded is not None:
    df = pd.read_csv(uploaded, parse_dates=[0], infer_datetime_format=True)
    st.write(df.head())
    # normalize time index
    if 'month' in df.columns:
        t = df['month'].to_numpy()
        q = df['production'].to_numpy()
    else:
        t = np.arange(len(df))
        q = df.iloc[:,1].to_numpy()

    model = st.selectbox('Modelo', ['exponential','hyperbolic','harmonic'])
    if st.button('Ajustar'):
        try:
            if model == 'exponential':
                popt, _ = curve_fit(exponential, t, q, p0=[q[0], 0.1])
                fit = exponential(t, *popt)
            elif model == 'hyperbolic':
                popt, _ = curve_fit(hyperbolic, t, q, p0=[q[0], 0.1, 0.5])
                fit = hyperbolic(t, *popt)
            else:
                popt, _ = curve_fit(harmonic, t, q, p0=[q[0], 0.1])
                fit = harmonic(t, *popt)

            fig = px.line()
            fig.add_scatter(x=t, y=q, name='Observado')
            fig.add_scatter(x=t, y=fit, name='Ajuste')
            st.plotly_chart(fig)

            st.success('Ajuste concluído. Parâmetros: {}'.format(popt))
        except Exception as e:
            st.error(f'Erro no ajuste: {e}')
