import pytest
from fastapi.testclient import TestClient
from main import app

def test_nodal_solve_endpoint(client, user_auth_headers):
    payload = {"p_res": 3000, "q_max": 1000, "p_wh": 500, "depth": 8000}
    response = client.post("/api/v1/gaia/nodal/solve", json=payload, headers=user_auth_headers)
    assert response.status_code == 200
    assert "operating_point" in response.json()

def test_reservoir_pz_endpoint(client, user_auth_headers):
    payload = {
        "pressure": [3000, 2500, 2000],
        "z": [0.85, 0.82, 0.80],
        "gp": [0, 100, 200]
    }
    response = client.post("/api/v1/gaia/reservoir/pz-analysis", json=payload, headers=user_auth_headers)
    assert response.status_code == 200
    assert "ogip" in response.json()

def test_simulation_run_endpoint(client, user_auth_headers):
    payload = {
        "nx": 5, "dx": 100, "dy": 100, "dz": 20,
        "dt": 1.0, "n_steps": 2,
        "wells": [{"cell_index": 2, "q_total": 500}]
    }
    response = client.post("/api/v1/gaia/simulation/run-oil-water", json=payload, headers=user_auth_headers)
    assert response.status_code == 200
    assert "pressure" in response.json()

def test_economics_run_endpoint(client, user_auth_headers):
    payload = {
        "forecast_time": [0, 1, 2],
        "forecast_rate": [1000, 900, 800],
        "oil_price": 70,
        "capex": 100000,
        "opex_fixed": 1000,
        "opex_var": 5,
        "discount_rate": 0.1
    }
    response = client.post("/api/v1/gaia/economics/run", json=payload, headers=user_auth_headers)
    assert response.status_code == 200
    assert "npv" in response.json()
