# PPES -- Petroleum Production Engineering Software

Python implementation of the calculation methods in:
Guo, Lyons & Ghalambor. Petroleum Production Engineering (Elsevier, 2007).

## Install
    pip install -e ".[dev,api,ui]"

## Test
    pytest -v

## CLI
    ppes pvt-oil --p 4475 --t 140 --api 35 --rs 600 --gamma-g 0.77

## API
    uvicorn ppes.api.main:app --reload
    # http://localhost:8000/docs

## UI
    streamlit run app/streamlit_app.py

## Coverage
- 18 chapters of the source book
- ~50 validation tests reproducing book worked examples
- 40+ REST endpoints
- 11-tab Streamlit UI

## Version
1.0.0
