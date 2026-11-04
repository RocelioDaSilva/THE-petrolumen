from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_production_economics_endpoint_success():
    payload = {
        "oil_price": 50.0,
        "gas_price": 2.0,
        "discount_rate": 10.0,
        "project_life": 2,
        "capex": {"development": 1000.0},
        "opex": {"fixed": 100.0},
        "tax_rate": 0.25,
        "water_disposal_cost_per_bbl": 1.0,
        "oil_production": [10.0, 20.0],
        "gas_production": [5.0, 10.0],
        "water_production": [2.0, 3.0],
    }
    response = client.post("/api/engine/production/economics", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "npv" in data
    assert "irr" in data
    assert "payout" in data
    assert "cashflow" in data
    assert "cumulative_cashflow" in data
    assert "cash_flow_details" in data
    assert len(data["cashflow"]) == 3
    assert data["cashflow"][0] == -1000.0
    assert data["cashflow"][1] == 408.0
    assert data["cashflow"][2] == 812.75
    assert abs(data["irr"] - 12.83) < 0.1
    assert abs(data["payout"] - 1.728) < 0.01


def test_production_economics_endpoint_validation_errors():
    payload = {
        "oil_price": 50.0,
        "gas_price": 2.0,
        "discount_rate": 10.0,
        "project_life": 2,
        "capex": {"development": 1000.0},
        "opex": {"fixed": 100.0},
        "tax_rate": 0.25,
        "water_disposal_cost_per_bbl": 1.0,
        "oil_production": [10.0],
        "gas_production": [5.0, 10.0],
        "water_production": [2.0, 3.0],
    }
    response = client.post("/api/engine/production/economics", json=payload)
    assert response.status_code == 422

    payload["oil_production"] = [10.0, 20.0]
    payload["oil_price"] = -50.0
    response = client.post("/api/engine/production/economics", json=payload)
    assert response.status_code == 422
