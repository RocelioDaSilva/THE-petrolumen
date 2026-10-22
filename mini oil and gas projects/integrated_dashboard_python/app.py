"""
Integrated dashboard skeleton
Run: streamlit run app.py
"""
import streamlit as st
import pandas as pd

st.title('Integrated Oil & Gas Dashboard')

st.sidebar.title('Data')
uploaded = st.sidebar.file_uploader('Upload CSV', type=['csv'])
if uploaded is not None:
    df = pd.read_csv(uploaded)
    st.write(df.head())

st.sidebar.title('Models')
if st.sidebar.button('Run model demo'):
    st.info('Model demo placeholder')

st.write('Use the README to wire ETL and models.')
