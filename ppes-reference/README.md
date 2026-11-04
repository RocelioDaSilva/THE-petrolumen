# PPES â€” Petroleum Production Engineering Software

Python reference implementation of the calculation methods in:

> Guo, Boyun; Lyons, William C.; Ghalambor, Ali.
> *Petroleum Production Engineering: A Computer-Assisted Approach*.
> Elsevier Science & Technology Books, 2007. ISBN 0750682701.

## Install

    pip install -e ".[dev,api,ui]"

## Test

    pytest -v

## Run CLI

    ppes pvt-oil --p 4475 --t 140 --api 35 --rs 600 --gamma-g 0.77

## Run API

    uvicorn ppes.api:app --reload
    # http://localhost:8000/docs

## Run UI

    streamlit run app/streamlit_app.py

## Structure

Every chapter module (`src/ppes/chNN_*.py`) corresponds to one chapter of
the source book. Every function's docstring cites the book equation and
page number. Every test in `tests/test_book_examples.py` reproduces a
book worked example with the printed answer as the expected value.

Coverage:
- Ch. 2  PVT                     â€” full
- Ch. 3  IPR                     â€” full
- Ch. 4  TPR                     â€” partial (Chen, AverageTZ)
- Ch. 5  Choke                   â€” full
- Ch. 6  Nodal                   â€” stub
- Ch. 7  Forecast                â€” stub
- Ch. 8  Decline                 â€” full
- Ch. 9  Tubing                  â€” full (biaxial, landing tension)
- Ch. 10 Separation              â€” partial
- Ch. 11 Transport               â€” partial
- Ch. 12 Rod pump                â€” partial
- Ch. 13 Gas lift                â€” stub
- Ch. 14 Other lift              â€” stub
- Ch. 15 Diagnostics             â€” stub
- Ch. 16 Acidizing               â€” partial
- Ch. 17 Fracturing              â€” partial
- Ch. 18 Optimization            â€” stub

Functions marked with `NotImplementedError` include the full docstring
and reference; fill in following the pattern of the implemented modules.