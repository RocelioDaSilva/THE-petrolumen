from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_eos_endpoint_calculates_peng_robinson_z_factor():
    response = client.post(
        "/api/engine/pvt/eos",
        json={
            "pressure": 5_000_000.0,
            "temperature": 250.0,
            "components": [
                {
                    "name": "methane",
                    "critical_pressure": 4_599_000.0,
                    "critical_temperature": 190.56,
                    "acentric_factor": 0.011,
                    "molecular_weight": 16.043,
                }
            ],
            "composition": {"methane": 1.0},
        },
    )

    assert response.status_code == 200
    assert response.json()["z_factor"] > 0


def test_trajectory_endpoint_returns_minimum_curvature_coordinates():
    response = client.post(
        "/api/engine/drilling/trajectory",
        json={
            "survey": [
                {"md": 0.0, "inc": 0.0, "azi": 0.0},
                {"md": 100.0, "inc": 0.0, "azi": 0.0},
            ]
        },
    )

    assert response.status_code == 200
    assert response.json()["survey"][-1] == {
        "md": 100.0,
        "inc": 0.0,
        "azi": 0.0,
        "x": 0.0,
        "y": 0.0,
        "z": 100.0,
    }


def test_geology_grid_endpoint_sums_variable_cell_volumes():
    response = client.post(
        "/api/engine/geology/grid",
        json={
            "nx": 2,
            "ny": 1,
            "nz": 1,
            "dx": [1.0, 2.0],
            "dy": 3.0,
            "dz": 4.0,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "shape": [2, 1, 1],
        "total_cells": 2,
        "bulk_volume": 36.0,
    }


def test_nodal_endpoint_finds_operating_rate_and_rejects_nonflowing_case():
    response = client.post(
        "/api/engine/reservoir/nodal",
        json={"qi": 5000.0, "pr": 3000.0, "p_surf": 1000.0},
    )
    invalid = client.post(
        "/api/engine/reservoir/nodal",
        json={"qi": 1000.0, "pr": 2000.0, "p_surf": 2500.0},
    )

    assert response.status_code == 200
    assert 0.0 < response.json()["operating_rate"] < 5000.0
    assert invalid.status_code == 422


def test_black_oil_defaults_return_200():
    response = client.post(
        "/api/simulate/black-oil",
        json={
            "grid": {"nx": 2, "ny": 2, "nz": 1, "dx": 50, "dy": 50, "dz": 10},
            "porosity": [0.2, 0.2, 0.2, 0.2],
            "permeability": [100, 100, 100, 100],
            "rock_compressibility": 0,
            "fluid_properties": {
                "water_viscosity": 1,
                "oil_viscosity": 2,
                "gas_viscosity": 0.02,
            },
            "initial_pressure": 3000,
            "initial_water_saturation": [0.2, 0.2, 0.2, 0.2],
            "initial_gas_saturation": [0, 0, 0, 0],
            "wells": [],
            "timesteps": [1],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert "pressure" in payload
    assert "saturations" in payload
    assert "wells" in payload
