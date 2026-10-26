def test_nodal_solve_endpoint(client, user_auth_headers):
    payload = {"p_res": 3000, "q_max": 1000, "p_wh": 500, "depth": 8000}
    response = client.post(
        "/api/v1/gaia/nodal/solve", json=payload, headers=user_auth_headers
    )
    assert response.status_code == 200
    assert "operating_point" in response.json()


def test_reservoir_pz_endpoint(client, user_auth_headers):
    payload = {
        "pressure": [3000, 2500, 2000],
        "z": [0.85, 0.82, 0.80],
        "gp": [0, 100, 200],
    }
    response = client.post(
        "/api/v1/gaia/reservoir/pz-analysis", json=payload, headers=user_auth_headers
    )
    assert response.status_code == 200
    assert "ogip" in response.json()


def test_simulation_run_endpoint(client, user_auth_headers):
    payload = {
        "nx": 5,
        "dx": 100,
        "dy": 100,
        "dz": 20,
        "dt": 1.0,
        "n_steps": 2,
        "wells": [{"cell_index": 2, "q_total": 500}],
    }
    response = client.post(
        "/api/v1/gaia/simulation/run-oil-water", json=payload, headers=user_auth_headers
    )
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
        "discount_rate": 0.1,
    }
    response = client.post(
        "/api/v1/gaia/economics/run", json=payload, headers=user_auth_headers
    )
    assert response.status_code == 200
    assert "npv" in response.json()


def test_economics_analyze_endpoint(client, user_auth_headers):
    # 10-year production profile payload
    production_profile = [10000.0] * 10
    payload = {
        "production_profile": production_profile,
        "oil_price": 70.0,
        "opex": 20.0,  # net 50$/bbl * 10000 bbl = $500,000 / yr net revenue
        "capex": 2000000.0,  # $2,000,000 initial CAPEX
        "discount_rate": 0.10,
    }
    response = client.post(
        "/api/v1/economics/analyze", json=payload, headers=user_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "npv" in data
    assert "irr" in data
    assert "cumulative_cash_flow" in data
    # Expected net cash flow: year 0 = -2000000, years 1..10 = +500000
    # Expected NPV @ 10% ~ 1072283.55
    assert abs(data["npv"] - 1072283.55) < 1.0
    assert 0.20 < data["irr"] < 0.25
    assert len(data["cumulative_cash_flow"]) == 11
    assert data["cumulative_cash_flow"][0] == -2000000.0
    assert data["cumulative_cash_flow"][-1] == 3000000.0
