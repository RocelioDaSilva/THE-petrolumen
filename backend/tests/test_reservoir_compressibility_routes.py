from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rock_compressibility_endpoint_returns_correlation_and_range_status():
    response = client.post(
        "/api/engine/reservoir/compressibility/rock",
        json={"phi": 0.2, "rock_type": "sandstone", "strict": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["cf_psi_inv"] > 0
    assert payload["in_validity_range"] is True
    assert payload["rock_type"] == "sandstone"


def test_rock_compressibility_endpoint_rejects_strict_out_of_range_porosity():
    response = client.post(
        "/api/engine/reservoir/compressibility/rock",
        json={"phi": 0.3, "rock_type": "sandstone", "strict": True},
    )

    assert response.status_code == 422


def test_gas_compressibility_endpoint_returns_z_derivative_and_value():
    response = client.post(
        "/api/engine/reservoir/compressibility/gas",
        json={"p_psia": 2500, "temperature_f": 150, "gas_sg": 0.9},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["z_at_p"] > 0
    assert payload["cg_psi_inv"] > 0
    assert payload["method"] == "central"
    assert payload["z_correlation"] == (
        "Hall-Yarborough with Sutton pseudocritical properties"
    )


def test_total_compressibility_endpoint_composes_rock_and_gas_terms():
    response = client.post(
        "/api/engine/reservoir/compressibility/total",
        json={
            "p_psia": 2500,
            "temperature_f": 150,
            "gas_sg": 0.9,
            "phi": 0.2,
            "rock_type": "sandstone",
            "co_psi_inv": 1.0e-5,
            "cw_psi_inv": 3.0e-6,
            "sg": 0.1,
            "so": 0.7,
            "sw": 0.2,
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ct_psi_inv"] > payload["cf_psi_inv"]
    assert payload["cg_psi_inv"] > 0
    assert payload["in_rock_validity_range"] is True


def test_total_compressibility_endpoint_rejects_invalid_saturation_sum():
    response = client.post(
        "/api/engine/reservoir/compressibility/total",
        json={
            "p_psia": 2500,
            "temperature_f": 150,
            "gas_sg": 0.9,
            "phi": 0.2,
            "rock_type": "sandstone",
            "co_psi_inv": 1.0e-5,
            "cw_psi_inv": 3.0e-6,
            "sg": 0.1,
            "so": 0.7,
            "sw": 0.1,
        },
    )

    assert response.status_code == 422
