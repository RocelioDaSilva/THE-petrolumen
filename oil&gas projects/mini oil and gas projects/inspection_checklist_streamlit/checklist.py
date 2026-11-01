"""
Simple Streamlit checklist app
Usage: streamlit run checklist.py
"""
import streamlit as st
import pandas as pd

st.title('Inspection Checklist')

if 'items' not in st.session_state:
    st.session_state['items'] = []

with st.form('new_item'):
    item = st.text_input('Item description')
    status = st.selectbox('Status', ['OK','NOK','NA'])
    notes = st.text_area('Notes')
    submitted = st.form_submit_button('Add')
    if submitted and item:
        st.session_state['items'].append({'item': item, 'status': status, 'notes': notes})

st.write(st.session_state['items'])
if st.button('Export CSV'):
    df = pd.DataFrame(st.session_state['items'])
    df.to_csv('inspection_report.csv', index=False)
    st.success('Exported inspection_report.csv')
