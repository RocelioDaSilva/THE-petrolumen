import numpy as np
import pytest

from app.engines.production import EconomicAnalysis


def _configured_analysis() -> EconomicAnalysis:
    analysis = EconomicAnalysis()
    analysis.set_economic_parameters(
        oil_price=50.0,
        gas_price=2.0,
        discount_rate=10.0,
        project_life=2,
        capex={"development": 1000.0},
        opex={"fixed": 100.0},
        tax_rate=0.25,
        water_disposal_cost_per_bbl=1.0,
    )
    return analysis


def test_cash_flow_accounts_for_year_zero_capex_water_and_tax_loss_guard():
    analysis = _configured_analysis()
    cash_flow = analysis.calculate_cash_flow(
        oil_production=[10.0, 20.0],
        gas_production=[5.0, 10.0],
        water_production=[2.0, 3.0],
    )

    np.testing.assert_allclose(cash_flow["revenue"]["total"], [510.0, 1020.0])
    np.testing.assert_allclose(cash_flow["costs"]["water_disposal"], [2.0, 3.0])
    np.testing.assert_allclose(cash_flow["depreciation"], [500.0, 500.0])
    np.testing.assert_allclose(cash_flow["taxes"], [0.0, 104.25])
    np.testing.assert_allclose(cash_flow["cash_flow"], [-1000.0, 408.0, 812.75])
    assert analysis.calculate_npv() == pytest.approx(
        -1000.0 + 408.0 / 1.1 + 812.75 / 1.1**2
    )


def test_project_metrics_and_invalid_irr_are_explicit():
    analysis = _configured_analysis()
    analysis.calculate_cash_flow([10.0, 20.0], [5.0, 10.0], [2.0, 3.0])

    assert analysis.calculate_irr() == pytest.approx(12.8319209)
    assert analysis.calculate_payback() == pytest.approx(1.728, abs=0.001)
    assert analysis.calculate_roi() == pytest.approx(22.075)

    never_recovers = EconomicAnalysis()
    never_recovers.set_economic_parameters(
        oil_price=0.0,
        gas_price=0.0,
        discount_rate=0.0,
        project_life=1,
        capex={"development": 10.0},
        opex={},
    )
    never_recovers.calculate_cash_flow([0.0], [0.0], [0.0])
    with pytest.raises(ValueError, match="IRR requires"):
        never_recovers.calculate_irr()
    with pytest.raises(ValueError, match="does not recover"):
        never_recovers.calculate_payback()


def test_sensitivity_and_monte_carlo_do_not_mutate_base_assumptions():
    analysis = _configured_analysis()
    analysis.calculate_cash_flow([10.0, 20.0], [5.0, 10.0], [2.0, 3.0])
    original_parameters = dict(analysis.economic_parameters)
    original_cash_flow = analysis.cash_flow["cash_flow"].copy()

    sensitivity = analysis.sensitivity_analysis("oil_price", [40.0, 60.0])
    monte_carlo = analysis.monte_carlo_simulation(
        3, {"oil_price": (lambda: 55.0,)}
    )

    assert sensitivity[40.0] < sensitivity[60.0]
    assert monte_carlo["mean"] > analysis.calculate_npv()
    assert analysis.economic_parameters == original_parameters
    np.testing.assert_array_equal(analysis.cash_flow["cash_flow"], original_cash_flow)


def test_economic_inputs_reject_inconsistent_years_and_invalid_parameters():
    analysis = _configured_analysis()
    with pytest.raises(ValueError, match="one annual volume"):
        analysis.calculate_cash_flow([10.0], [5.0, 10.0], [2.0, 3.0])

    with pytest.raises(ValueError, match="tax rate"):
        analysis.set_economic_parameters(
            oil_price=50.0,
            gas_price=2.0,
            discount_rate=10.0,
            project_life=2,
            capex={},
            opex={},
            tax_rate=34.0,
        )
