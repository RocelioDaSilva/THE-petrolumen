import json

import pytest
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


def test_eos_endpoint_calculates_srk_z_factor():
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
                }
            ],
            "composition": {"methane": 1.0},
            "eos_type": "SRK",
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["z_factor"] > 0


def test_flash_endpoint_returns_two_phase_compositions():
    response = client.post(
        "/api/engine/pvt/flash",
        json={
            "pressure": 5_000_000.0,
            "temperature": 250.0,
            "components": [
                {
                    "name": "methane",
                    "critical_pressure": 4_599_000.0,
                    "critical_temperature": 190.56,
                    "acentric_factor": 0.011,
                },
                {
                    "name": "propane",
                    "critical_pressure": 4_248_000.0,
                    "critical_temperature": 369.83,
                    "acentric_factor": 0.152,
                },
            ],
            "composition": {"methane": 0.5, "propane": 0.5},
            "initial_k_values": [2.0, 0.5],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["phase"] == "two_phase"
    assert payload["vapor_fraction"] == 0.5
    for component, overall in {"methane": 0.5, "propane": 0.5}.items():
        recovered = (
            (1 - payload["vapor_fraction"])
            * payload["liquid_composition"][component]
            + payload["vapor_fraction"] * payload["vapor_composition"][component]
        )
        assert recovered == pytest.approx(overall)


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


def test_grid_chart_returns_png():
    response = client.post(
        "/api/engine/geology/grid/chart",
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
    payload = response.json()
    assert payload["content_type"] == "image/png"
    assert len(payload["image_base64"]) > 2000


def test_eos_chart_returns_png():
    response = client.post(
        "/api/engine/pvt/eos/chart",
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
    payload = response.json()
    assert payload["content_type"] == "image/png"
    assert len(payload["image_base64"]) > 2000


def test_nodal_chart_returns_png():
    response = client.post(
        "/api/engine/reservoir/nodal/chart",
        json={"qi": 5000.0, "pr": 3000.0, "p_surf": 1000.0},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["content_type"] == "image/png"
    assert len(payload["image_base64"]) > 2000


def test_trajectory_chart_returns_png():
    response = client.post(
        "/api/engine/drilling/trajectory/chart",
        json={
            "survey": [
                {"md": 0.0, "inc": 0.0, "azi": 0.0},
                {"md": 100.0, "inc": 0.0, "azi": 0.0},
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["content_type"] == "image/png"
    assert len(payload["image_base64"]) > 2000


def test_health_endpoint_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


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


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("porosity", [float("nan"), 0.2, 0.2, 0.2]),
        ("permeability", [100, float("inf"), 100, 100]),
        ("porosity", [-0.1, 0.2, 0.2, 0.2]),
        ("timesteps", [float("inf")]),
    ],
)
def test_black_oil_rejects_non_finite_and_negative_numeric_inputs(field, value):
    payload = {
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
    }
    payload[field] = value

    response = client.post(
        "/api/simulate/black-oil",
        content=json.dumps(payload, allow_nan=True),
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "archie_params",
    [
        {"a": float("nan"), "m": 2.0, "n": 2.0, "Rw": 0.1},
        {"a": 1.0, "m": -1.0, "n": 2.0, "Rw": 0.1},
        {"a": 1.0, "m": 2.0, "n": 0.0, "Rw": 0.1},
        {"a": 1.0, "m": 2.0, "n": 2.0, "Rw": -0.1},
    ],
)
def test_ooip_run_rejects_invalid_archie_parameters(archie_params):
    response = client.post(
        "/api/workflow/ooip/run",
        content=json.dumps(
            {
                "session_id": "unused",
                "area_acres": 100.0,
                "archie_params": archie_params,
            },
            allow_nan=True,
        ),
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "route", ["/api/simulate/compositional", "/api/simulate/thermal"]
)
def test_unimplemented_simulation_rejects_oversized_grid(route):
    payload = {
        "grid": {"nx": 513, "ny": 1, "nz": 1, "dx": 50, "dy": 50, "dz": 10},
        "components": [
            {
                "name": "methane",
                "mw": 16.043,
                "tc": 190.56,
                "pc": 4599000,
                "omega": 0.011,
            }
        ],
        "rock_properties": {"porosity": 0.2},
        "wells": [],
        "initial_composition": {"methane": 1.0},
        "timesteps": [1],
    }
    if route.endswith("thermal"):
        payload["thermal_properties"] = {
            "rock_heat_capacity": 900,
            "thermal_conductivity": 2,
            "fluid_heat_capacity": 4200,
        }
        payload["initial_temperature"] = 350

    response = client.post(route, json=payload)

    assert response.status_code == 422


def test_black_oil_with_bhp_control_returns_well_results():
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
            "wells": [
                {
                    "name": "PROD-1",
                    "i": 0,
                    "j": 0,
                    "perforation_layers": [0],
                    "well_type": "producer",
                    "controls": {"bhp": 2000.0},
                }
            ],
            "timesteps": [1],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["wells"][0]["name"] == "PROD-1"
    assert payload["pressure"][0] == 2000.0


def test_black_oil_water_injector_updates_saturation():
    base_payload = {
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
        "timesteps": [1],
    }
    baseline = client.post(
        "/api/simulate/black-oil",
        json={**base_payload, "wells": []},
    )
    injected = client.post(
        "/api/simulate/black-oil",
        json={
            **base_payload,
            "wells": [
                {
                    "name": "INJ-1",
                    "i": 0,
                    "j": 0,
                    "perforation_layers": [0],
                    "well_type": "injector",
                    "controls": {"water_rate": 100.0},
                }
            ],
        },
    )

    assert baseline.status_code == 200, baseline.text
    assert injected.status_code == 200, injected.text
    assert injected.json()["saturations"]["water"][0] > baseline.json()[
        "saturations"
    ]["water"][0]


def test_compositional_route_is_marked_unimplemented():
    response = client.post(
        "/api/simulate/compositional",
        json={
            "grid": {"nx": 1, "ny": 1, "nz": 1, "dx": 50, "dy": 50, "dz": 10},
            "components": [{"name": "methane", "mw": 16.043, "tc": 190.56, "pc": 4599000, "omega": 0.011}],
            "rock_properties": {"porosity": 0.2},
            "wells": [],
            "initial_composition": {"methane": 1.0},
            "timesteps": [1],
        },
    )
    assert response.status_code == 501
    payload = response.json()
    assert "detail" in payload
    body = payload["detail"] if isinstance(payload["detail"], dict) else payload
    assert "detail" in body
    assert "tracking" in body
    assert len(body["detail"]) > 0
    assert len(body["tracking"]) > 0


def test_thermal_route_is_marked_unimplemented():
    response = client.post(
        "/api/simulate/thermal",
        json={
            "grid": {"nx": 1, "ny": 1, "nz": 1, "dx": 50, "dy": 50, "dz": 10},
            "components": [{"name": "methane", "mw": 16.043, "tc": 190.56, "pc": 4599000, "omega": 0.011}],
            "rock_properties": {"porosity": 0.2},
            "wells": [],
            "initial_composition": {"methane": 1.0},
            "timesteps": [1],
            "thermal_properties": {"rock_heat_capacity": 900, "thermal_conductivity": 2, "fluid_heat_capacity": 4200},
            "initial_temperature": 350,
        },
    )
    assert response.status_code == 501
    payload = response.json()
    assert "detail" in payload
    body = payload["detail"] if isinstance(payload["detail"], dict) else payload
    assert "detail" in body
    assert "tracking" in body
    assert len(body["detail"]) > 0
    assert len(body["tracking"]) > 0


def test_root_endpoint_redirects_to_docs():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"
