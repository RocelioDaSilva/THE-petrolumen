import json

from fastapi.testclient import TestClient

from app.engines.pvt import mbal as mbal_module
from app.main import app

client = TestClient(app)


def test_mbal_gas_reservoir_endpoint():
    payload = {
        "reservoir_type": "gas",
        "pressure_history": [4000.0, 3200.0],
        "production_history": [
            {"oil_prod": 0.0, "gas_prod": 5000000.0, "water_prod": 100.0}
        ],
        "pvt_data": [
            {"pressure": 3200.0, "bo": 1.0, "bg": 0.0011, "rs": 0.0, "z": 0.84},
            {"pressure": 4000.0, "bo": 1.0, "bg": 0.00082, "rs": 0.0, "z": 0.89},
        ],
        "We": 500.0,
        "Wp": 100.0,
        "Bw": 1.0,
        "cw": 3e-6,
        "cf": 3e-6,
        "Swi": 0.2,
    }
    response = client.post("/api/engine/pvt/mbal", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "ooip_or_ogip" in data
    assert data["ooip_or_ogip"] > 0
    assert abs(data["ooip_or_ogip"] - 1314433.0) < 500.0
    assert "note" in data
    assert "drive indices not computed" in data["note"]


def test_mbal_endpoint_validation_error():
    payload = {
        "reservoir_type": "oil",
        "pressure_history": [4000.0],  # needs at least 2 points
        "production_history": [
            {"oil_prod": 500000.0}
        ],
    }
    response = client.post("/api/engine/pvt/mbal", json=payload)
    assert response.status_code == 422


def test_mbal_non_convergence_is_returned_as_validation_error(monkeypatch):
    monkeypatch.setattr(
        mbal_module,
        "fsolve",
        lambda *_args, **_kwargs: ([1_000_000.0], {}, 4, "iteration failed"),
    )
    payload = {
        "reservoir_type": "gas",
        "pressure_history": [4000.0, 3200.0],
        "production_history": [{"gas_prod": 5_000_000.0}],
        "pvt_data": [
            {"pressure": 3200.0, "bg": 0.0011, "z": 0.84},
            {"pressure": 4000.0, "bg": 0.00082, "z": 0.89},
        ],
    }

    response = client.post("/api/engine/pvt/mbal", json=payload)

    assert response.status_code == 422
    assert "did not converge" in response.json()["detail"]


def test_mbal_rejects_non_finite_pvt_values():
    payload = {
        "reservoir_type": "gas",
        "pressure_history": [4000.0, 3200.0],
        "production_history": [{"gas_prod": 5_000_000.0}],
        "pvt_data": [
            {"pressure": 3200.0, "bg": float("inf"), "z": 0.84},
            {"pressure": 4000.0, "bg": 0.00082, "z": 0.89},
        ],
    }

    response = client.post(
        "/api/engine/pvt/mbal",
        content=json.dumps(payload, allow_nan=True),
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422
