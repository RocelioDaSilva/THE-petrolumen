import pytest
from fastapi.testclient import TestClient
from main import app
import json

def test_pvt_z_factor_endpoint(client, user_auth_headers):
    payload = {"pressure": 3000, "temperature": 160, "gamma_g": 0.65}
    response = client.post("/api/v1/gaia/pvt/z-factor", json=payload, headers=user_auth_headers)
    assert response.status_code == 200
    assert "z_factor" in response.json()

def test_dca_duong_endpoint(client, user_auth_headers):
    payload = {"time": [1, 2, 3, 4, 5], "rate": [500, 450, 410, 380, 350]}
    response = client.post("/api/v1/gaia/dca/duong", json=payload, headers=user_auth_headers)
    assert response.status_code == 200
    assert response.json()["model"] == "Duong"

def test_rta_fmb_gas_endpoint(client, user_auth_headers):
    payload = {
        "pwf": [3000, 2800, 2600],
        "gp": [0, 100, 200],
        "pi": 3200,
        "tf": 160,
        "gamma_g": 0.65
    }
    response = client.post("/api/v1/gaia/rta/fmb-gas", json=payload, headers=user_auth_headers)
    assert response.status_code == 200
    assert "ogip" in response.json()
