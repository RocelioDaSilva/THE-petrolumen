import pytest
import numpy as np
from gaia_genesis.reservoir_engineering import DeclineAnalysis


def test_decline_analysis_fitting():
    dca = DeclineAnalysis()
    # Generate synthetic exponential data: q = 100 * exp(-0.01 * t)
    t = np.linspace(0, 100, 10)
    q = 100 * np.exp(-0.01 * t)

    # Test Exponential Fit
    params = dca.fit_arps(t, q, method="exponential")
    assert params["method"] == "exponential"
    assert pytest.approx(params["qi"], rel=1e-2) == 100
    assert pytest.approx(params["di"], rel=1e-2) == 0.01

    # Test Forecast
    q_forecast = dca.forecast_production(params, t)
    assert np.allclose(q, q_forecast, rtol=1e-2)

    # Test EUR (economic limit 1.0)
    # Integral of 100 * exp(-0.01 * t) from 0 to limit_time
    # limit_rate = 100 * exp(-0.01 * t_limit) => 0.01 = exp(-0.01 * t_limit) => ln(0.01) = -0.01 * t_limit
    # t_limit = -ln(0.01) / 0.01 = 460.5
    # Integral = [qi * exp(-di*t) / -di] from 0 to t_limit
    # = (qi/di) * (1 - exp(-di * t_limit)) = (qi/di) * (1 - limit_rate/qi) = (100 - 1) / 0.01 = 9900
    eur = dca.calculate_eur(params, limit_rate=1.0)
    assert pytest.approx(eur, rel=1e-2) == 9900


def test_hyperbolic_fit():
    dca = DeclineAnalysis()
    # q = 100 / (1 + 0.5 * 0.01 * t)**(1/0.5)
    t = np.linspace(0, 200, 20)
    qi_true, di_true, b_true = 100, 0.01, 0.5
    q = qi_true / (1 + b_true * di_true * t) ** (1 / b_true)

    params = dca.fit_arps(t, q, method="hyperbolic")
    assert params["method"] == "hyperbolic"
    assert pytest.approx(params["qi"], rel=1e-2) == qi_true
    assert pytest.approx(params["di"], rel=1e-2) == di_true
    assert pytest.approx(params["b"], rel=1e-2) == b_true
