import pytest
from gaia_genesis.economics import (
    EconomicsEvaluator,
    EconomicParameters,
    ProductionForecast,
    EconomicSensitivityAnalyzer,
)


def test_economics_evaluator_cash_flows_and_metrics():
    params = EconomicParameters(
        capex=1000000.0,
        oil_price=70.0,
        gas_price=3.0,
        opex_fixed_monthly=2000.0,
        opex_var_oil=5.0,
        royalty_rate=0.125,
        severance_tax_rate=0.05,
        income_tax_rate=0.21,
        discount_rate_annual=0.10,
        period_frequency="monthly",
    )

    # 12-month production forecast (1000 bbl/d declining by 5% per month)
    oil_rates = [1000.0 * (0.95**i) for i in range(12)]
    time_periods = list(range(1, 13))

    forecast = ProductionForecast(
        time_periods=time_periods,
        oil_rates=oil_rates,
        rates_are_daily=True,
    )

    res = EconomicsEvaluator.evaluate(params, forecast)

    assert res.total_capex == 1000000.0
    assert res.total_gross_revenue > 0.0
    assert res.total_net_revenue < res.total_gross_revenue
    assert len(res.cash_flow_periods) == 13  # Period 0 + 12 production periods
    assert res.cash_flow_periods[0].net_cash_flow == -1000000.0
    assert res.profitability_index > 0.0
    assert isinstance(res.npv, float)
    assert isinstance(res.irr, float)


def test_payout_time_linear_interpolation():
    # CAPEX $1,000,000, Net revenue $300,000/month after OPEX
    params = EconomicParameters(
        capex=1000000.0,
        oil_price=100.0,
        opex_var_oil=0.0,
        opex_fixed_monthly=0.0,
        royalty_rate=0.0,
        severance_tax_rate=0.0,
        income_tax_rate=0.0,
        discount_rate_annual=0.10,
        period_frequency="monthly",
    )

    # 3000 bbl/month constant
    forecast = ProductionForecast(
        time_periods=[1, 2, 3, 4, 5],
        oil_rates=[3000.0] * 5,  # 3000 * 100 = $300,000 / month
        rates_are_daily=False,
    )

    res = EconomicsEvaluator.evaluate(params, forecast)

    # Payout should occur at 1000000 / 300000 = 3.333 months
    assert pytest.approx(res.payout_months, 0.01) == 3.333
    assert res.payout_months > 3.0 and res.payout_months < 4.0


def test_sensitivity_analyzer():
    params = EconomicParameters(
        capex=1000000.0,
        oil_price=70.0,
        opex_var_oil=5.0,
        discount_rate_annual=0.10,
    )
    forecast = ProductionForecast(
        time_periods=[1, 2, 3, 4, 5, 6],
        oil_rates=[500.0] * 6,
        rates_are_daily=True,
    )

    # 1D sensitivity
    res_1d = EconomicSensitivityAnalyzer.run_1d_sensitivity(
        params, forecast, parameter_name="oil_price", percentage_steps=[-20, 0, 20]
    )
    assert len(res_1d) == 3
    assert res_1d[0]["npv"] < res_1d[2]["npv"]

    # 2D matrix
    res_2d = EconomicSensitivityAnalyzer.run_2d_sensitivity(
        params,
        forecast,
        param_x="oil_price",
        steps_x=[-10, 10],
        param_y="capex",
        steps_y=[-10, 10],
    )
    assert "matrix_npv" in res_2d
    assert len(res_2d["matrix_npv"]) == 2

    # Tornado diagram
    tornado = EconomicSensitivityAnalyzer.generate_tornado_data(
        params, forecast, parameters_to_test=["oil_price", "capex"], variation_pct=20.0
    )
    assert len(tornado) == 2
    assert tornado[0]["swing"] >= tornado[1]["swing"]


def test_economics_api_endpoints(client, user_auth_headers):
    # Test POST /api/v1/gaia/economics/evaluate
    payload_eval = {
        "forecast": {
            "time": [1, 2, 3, 4, 5, 6],
            "oil_rate": [1000.0, 950.0, 900.0, 850.0, 800.0, 750.0],
            "rates_are_daily": True,
        },
        "capex": 2000000.0,
        "oil_price": 75.0,
        "opex_fixed_monthly": 1500.0,
        "opex_var_oil": 4.5,
        "discount_rate": 0.10,
    }

    res_eval = client.post(
        "/api/v1/gaia/economics/evaluate",
        json=payload_eval,
        headers=user_auth_headers,
    )
    assert res_eval.status_code == 200
    data_eval = res_eval.json()
    assert "npv" in data_eval
    assert "irr" in data_eval
    assert "payout_months" in data_eval
    assert "cash_flow_periods" in data_eval

    # Test POST /api/v1/gaia/economics/sensitivity
    payload_sens = {
        "evaluate_request": payload_eval,
        "sensitivity_type": "tornado",
        "tornado_variation_pct": 15.0,
    }

    res_sens = client.post(
        "/api/v1/gaia/economics/sensitivity",
        json=payload_sens,
        headers=user_auth_headers,
    )
    assert res_sens.status_code == 200
    data_sens = res_sens.json()
    assert data_sens["type"] == "tornado"
    assert "tornado_data" in data_sens

    # Test POST /api/v1/gaia/economics/dca-economics
    payload_dca = {
        "dca_params": {"qi": 1000.0, "di": 0.05, "b": 0.5, "method": "hyperbolic"},
        "months_to_forecast": 36,
        "capex": 1500000.0,
        "oil_price": 70.0,
        "opex_fixed_monthly": 1000.0,
        "opex_var_oil": 5.0,
        "discount_rate": 0.10,
    }

    res_dca = client.post(
        "/api/v1/gaia/economics/dca-economics",
        json=payload_dca,
        headers=user_auth_headers,
    )
    assert res_dca.status_code == 200
    data_dca = res_dca.json()
    assert "npv" in data_dca
    assert len(data_dca["cash_flow_periods"]) == 37  # Period 0 + 36 months
