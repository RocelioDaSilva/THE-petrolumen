import logging
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from app.engines.analytics.advanced_analytics import AdvancedDataAnalysis
from app.engines.analytics.ai_seismic import AISeismicAnalysis
from app.engines.analytics.data_analytics import DataAnalytics
from app.engines.geology.geostatistics import Geostatistics
from app.engines.modeling.geomechanics import GeomechanicalModel
from app.engines.modeling.thermal_modeling import ThermalModel
from app.engines.modeling.uncertainty_analysis import UncertaintyAnalysis
from app.engines.modeling.workflow_automation import WorkflowAutomation
from app.engines.prediction.ai_prediction import AIPrediction
from app.engines.production.production_analysis import ProductionAnalysis
from app.engines.production.production_optimization import ProductionOptimization
from app.engines.production.reserves_evaluation import (
    ReserveCategory,
    ReservesEvaluation,
)
from app.engines.pvt.mbal import MaterialBalance
from app.engines.reservoir.reservoir_engineering import PVTProperties
from app.engines.reservoir.reservoir_simulation import ReservoirSimulation
from app.engines.reservoir.simulation.advanced_simulation import AdvancedSimulation
from app.engines.reservoir.simulation.commercial_simulator import CommercialSimulator
from app.engines.reservoir.simulation.eor_simulator import EORSimulator
from app.engines.reservoir.simulation.network_designer import NetworkDesigner
from app.engines.reservoir.simulation.parallel_engine import ParallelEngine
from app.engines.reservoir.simulation.production_optimizer import ProductionOptimizer
from app.engines.reservoir.simulation.proxy_models import ReservoirProxy
from app.engines.reservoir.simulation.simulator_integration import SimulatorIntegration
from app.engines.reservoir.simulation.auto_diff import AutoDiff
from app.engines.visualization.advanced_visualization import AdvancedVisualization


def test_advanced_simulation_capabilities():
    flow = SimpleNamespace(
        mesh=SimpleNamespace(cells=[0, 1]),
        pressure=np.array([3000.0, 2900.0]),
        saturation={"oil": np.array([0.6, 0.7])},
    )
    advanced = AdvancedSimulation(flow)
    advanced.enable_dual_porosity(
        {"porosity": 0.2, "permeability": 10.0},
        {"porosity": 0.01, "permeability": 100.0, "shape_factor": 12.0},
    )
    flow.saturation["oil"][0] = 0.4

    transfer = advanced.calculate_matrix_fracture_transfer()

    assert flow.permeability.tolist() == [100.0, 100.0]
    assert transfer["oil"][0] == pytest.approx(2.4)


def test_advanced_analytics_current_api():
    data = pd.DataFrame({"oil_rate": np.linspace(100.0, 50.0, 35)})
    analysis = AdvancedDataAnalysis()
    analysis.load_production_data(data)

    analysis.analyze_production_patterns()

    result = analysis.data["production_analysis"]
    assert "oil_rate_trend" in result
    assert "oil_rate_events" in result
    assert len(result["oil_rate_trend"]) == len(data)


def test_ai_seismic_current_api():
    analysis = AISeismicAnalysis()
    analysis.seismic_data = np.random.default_rng(7).normal(size=(9, 9))

    analysis.compute_attributes()

    assert {"envelope", "instant_phase", "instant_freq", "rel_impedance",
            "sweetness", "coherency"} <= analysis.attributes.keys()
    assert analysis.attributes["coherency"].shape == (9, 9)
    assert np.isfinite(analysis.attributes["coherency"][4, 4])


def test_commercial_simulator_dispatch(monkeypatch):
    simulator = CommercialSimulator()
    simulator.create_static_model(1, 1, 1, 10.0, 10.0, 5.0, {})
    simulator.setup_pvt_model(pvt_data={"pressure": [1000.0]})
    simulator.add_well("P1", "producer", [(0, 0, 0)], {"rate": 100.0})
    calls = []
    monkeypatch.setattr(
        simulator,
        "_run_black_oil_simulation",
        lambda timesteps, dt: calls.append((timesteps, dt)),
    )

    simulator.run_simulation(3, 0.5)

    assert simulator.wells["P1"]["type"] == "producer"
    assert calls == [(3, 0.5)]


def test_data_analytics_current_api():
    rows = []
    for well, offset in (("A", 0.0), ("B", 10.0)):
        for day in range(4):
            rows.append({
                "well_name": well,
                "rate": 100.0 + offset - day * 5.0,
                "water_cut": 0.2 + day * 0.01,
                "pressure": 3000.0 - day * 20.0,
            })
    analysis = DataAnalytics()
    analysis.load_production_data(pd.DataFrame(rows))

    analysis.analyze_production_patterns(window_size=2, n_clusters=2)

    assert analysis.production_patterns["features"].shape == (6, 6)
    assert len(analysis.production_patterns["clusters"]) == 6


def test_geostatistics_variogram_and_kriging():
    data = pd.DataFrame({
        "x": [0.0, 1.0, 0.0, 1.0],
        "y": [0.0, 0.0, 1.0, 1.0],
        "z": [0.0, 0.0, 0.0, 0.0],
        "value": [1.0, 2.0, 3.0, 4.0],
    })
    model = Geostatistics()
    model.load_data(data, "x", "y", "z", "value")
    model.calculate_variogram(n_lags=3, max_lag=2.0)
    model.fit_variogram_model(model_type="spherical")

    estimate = model.perform_kriging(
        np.array([[0.5]]), np.array([[0.5]]), np.array([[0.0]])
    )

    assert estimate["predicted"].shape == (1, 1)
    assert np.isfinite(estimate["predicted"]).all()
    assert (estimate["std"] >= 0).all()


def test_geomechanics_solver():
    model = GeomechanicalModel((1, 1, 1), {"biot_coefficient": 0.8})
    model.set_initial_stress(
        {"xx": 1.0, "yy": 1.0, "zz": 1.0}, np.array([100.0])
    )
    model.update_stress_from_pressure(
        np.array([900.0]), np.array([1000.0])
    )
    porosity, permeability = model.update_porosity_permeability(
        np.array([0.2]), np.array([100.0])
    )

    assert model.stress["xx"][0] == pytest.approx(180.0)
    assert porosity[0] == pytest.approx(0.2)
    assert permeability[0] == pytest.approx(100.0)


def test_production_analysis_workflows():
    time = np.arange(20, dtype=float)
    rates = 1000.0 * np.exp(-0.05 * time)
    analysis = ProductionAnalysis()
    analysis.load_historical_data(
        pd.DataFrame({"time": time, "oil": rates}),
        "time",
        {"oil": "oil"},
    )

    result = analysis.fit_decline_curves(
        "oil", decline_type="exponential", n_samples=0
    )

    assert result["parameters"]["qi"] == pytest.approx(1000.0, rel=1e-3)
    assert result["parameters"]["Di"] == pytest.approx(0.05, rel=1e-3)
    assert result["uncertainty"] is None


def test_production_optimization_workflows():
    optimizer = ProductionOptimization(flow_simulation=None)
    forecast = optimizer.forecast_production(
        forecast_period=4,
        dt=1.0,
        decline_curves={"oil": {"qi": 100.0, "Di": 0.1}},
    )

    assert forecast["time"].tolist() == [0.0, 1.0, 2.0, 3.0]
    assert forecast["oil"][0] == pytest.approx(100.0)
    assert forecast["oil"][-1] < forecast["oil"][0]


def test_material_balance_oil_gas():
    balance = MaterialBalance("oil")
    balance.add_pressure_point(3000.0)
    balance.add_pressure_point(1000.0)
    balance.add_pvt_data(1000.0, bo=1.2, bg=0.01, rs=500.0, z=0.8)
    balance.add_pvt_data(3000.0, bo=1.4, bg=0.005, rs=800.0, z=0.9)
    balance.add_production_point(oil_prod=10000.0, gas_prod=50000.0)

    oil_error = balance.calculate_oil_mbal(
        1_000_000.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1e-6, 1e-6, 0.2
    )
    gas_error = balance.calculate_gas_mbal(
        1_000_000.0, 0.0, 0.0, 1.0, 1e-6, 1e-6, 0.2
    )

    assert np.isfinite(oil_error)
    assert np.isfinite(gas_error)


def test_reserves_evaluation_workflows():
    petrophysical = pd.DataFrame({
        "area": [100.0],
        "net_pay": [50.0],
        "porosity": [20.0],
        "water_saturation": [25.0],
        "net_gross": [0.8],
    })
    production = pd.DataFrame({
        "time": [0.0, 1.0, 2.0],
        "oil_rate": [100.0, 80.0, 64.0],
        "gas_rate": [1000.0, 800.0, 640.0],
    })
    evaluation = ReservesEvaluation()

    estimates = evaluation.calculate_reserves(
        petrophysical, production, {"oil_price": 70.0, "gas_price": 3.0}
    )

    assert set(estimates) == set(ReserveCategory)
    assert estimates[ReserveCategory.PROVED].oil_volume > 0
    assert estimates[ReserveCategory.PROVED].gas_volume > 0


def test_reservoir_engineering_capabilities():
    pvt = PVTProperties()

    rs = pvt.calculate_solution_gas_ratio(
        pressure=2000.0,
        temperature=180.0,
        api_gravity=35.0,
        gas_specific_gravity=0.7,
    )
    z_factor = pvt.calculate_z_factor(2000.0, 180.0, 0.7)

    assert rs > 0
    assert z_factor > 0


def test_ai_prediction_pipeline():
    predictor = AIPrediction()
    data = pd.DataFrame({
        "feature": np.arange(10, dtype=float),
        "target": np.arange(10, dtype=float) * 2.0,
    })

    x_train, x_test, y_train, y_test = predictor.prepare_data(
        data, "target", ["feature"], test_size=0.2
    )

    assert x_train.shape == (8, 1)
    assert x_test.shape == (2, 1)
    assert len(y_train) == 8
    assert len(y_test) == 2
    assert predictor.feature_columns == ["feature"]


def test_reservoir_simulation_model_selection():
    simulation = ReservoirSimulation(model_type="thermal")
    simulation.create_grid(2, 1, 1, 10.0, 10.0, 5.0)
    simulation.set_initial_conditions(
        3000.0, 180.0, {"water": 0.2, "oil": 0.7, "gas": 0.1}
    )

    assert simulation.model_type == "thermal"
    assert simulation.grid["cells"] == 2
    assert simulation.initial_conditions["pressure"] == 3000.0


def test_auto_diff_derivative_propagation():
    auto_diff = AutoDiff()
    result = auto_diff.evaluate_function(
        lambda x: x * x + 3 * x,
        {"x": 2.0},
    )

    assert result["value"] == pytest.approx(10.0)
    assert result["derivatives"]["x"] == pytest.approx(7.0)


def test_eor_simulator_current_api():
    simulator = EORSimulator()
    simulator.setup_grid(2, 1, 1, 10.0, 10.0, 5.0)
    simulator.setup_polymer_flood({"viscosity_multiplier": 4.0})

    assert simulator.eor_type == "polymer"
    assert simulator.chemical_properties["polymer_concentration"].shape == (
        2,
    )
    assert simulator.chemical_properties["viscosity_multiplier"] == 4.0


def test_network_designer_current_api():
    network = NetworkDesigner()
    network.add_well("W1", surface_pressure=1000.0, bhp=2500.0)
    network.add_separator("S1", pressure=500.0, temperature=80.0)
    network.add_pipeline("P1", "W1", "S1", diameter=0.2, length=1000.0)

    assert network.elements["W1"].bhp == 2500.0
    assert network.elements["S1"].temperature == 80.0
    assert network.connections == [("W1", "PIPE-P1", "S1")]


def test_parallel_engine_cpu_solve():
    engine = ParallelEngine.__new__(ParallelEngine)
    engine.use_gpu = False
    engine.n_cores = 1
    engine.pool = None

    solution = engine.solve_linear_system(
        np.array([[3.0, 1.0], [1.0, 2.0]]),
        np.array([9.0, 8.0]),
    )

    assert solution == pytest.approx([2.0, 3.0])


def test_production_optimizer_scenario_ranking():
    class Simulator:
        def run_simulation(self, parameters):
            return {
                "rates": parameters["rates"],
                "cumulative_production": parameters["cumulative"],
                "OOIP": 1000.0,
            }

    optimizer = ProductionOptimizer(Simulator())
    optimizer.set_economic_parameters({"oil_price": 10.0, "discount_rate": 0.0})
    optimizer.add_scenario("base", {
        "rates": [{"oil": 10.0, "gas": 0.0, "water": 0.0}],
        "cumulative": 100.0,
    })

    ranked = optimizer.rank_scenarios()

    assert ranked.loc[0, "scenario"] == "base"
    assert ranked.loc[0, "npv"] == pytest.approx(100.0)
    assert ranked.loc[0, "recovery"] == pytest.approx(0.1)


def test_reservoir_proxy_models():
    proxy = ReservoirProxy(input_dim=1, output_dim=1)
    features = np.array([[1.0], [2.0], [3.0], [4.0]])
    targets = np.array([[10.0], [20.0], [30.0], [40.0]])

    scaled_features, scaled_targets = proxy.prepare_data(features, targets)

    assert scaled_features.shape == features.shape
    assert scaled_targets.shape == targets.shape
    assert np.mean(scaled_features) == pytest.approx(0.0)
    assert np.mean(scaled_targets) == pytest.approx(0.0)


def test_simulation_controller_dispatch(monkeypatch):
    import app.engines.reservoir.simulation.simulation_controller as controller_module

    monkeypatch.setattr(controller_module, "ParallelEngine", lambda: object())
    from app.engines.reservoir.simulation.black_oil_simulator import BlackOilSimulator
    from app.engines.reservoir.simulation.simulation_controller import (
        SimulationController,
    )

    controller = SimulationController("black_oil")

    assert isinstance(controller.simulator, BlackOilSimulator)
    with pytest.raises(ValueError, match="Unknown simulation type"):
        SimulationController("unsupported")


def test_simulator_integration_dispatch():
    simulator = CommercialSimulator()

    integration = SimulatorIntegration(simulator)

    assert integration.advanced_sim.flow_sim is simulator


def test_thermal_modeling_heat_balance():
    model = ThermalModel((2, 1, 1), {})
    model.set_initial_temperature(
        temperature_gradient=0.02,
        depth=np.array([100.0, 200.0]),
        surface_temp=60.0,
    )
    viscosity = model.calculate_temperature_dependent_viscosity(
        "oil", np.array([10.0, 10.0])
    )

    assert model.temperature.tolist() == pytest.approx([62.0, 64.0])
    assert viscosity[1] < viscosity[0]


def test_uncertainty_analysis_statistics():
    class HistoryMatching:
        parameters = {"porosity": {"bounds": [1.0, 3.0], "value": 2.0}}

        def run_simulation(self):
            return self.parameters["porosity"]["value"]

        def calculate_error(self, simulated):
            return simulated**2 + 1.0

    analysis = UncertaintyAnalysis(HistoryMatching())

    result = analysis.run_parameter_sensitivity(n_samples=5)

    assert result["porosity"]["values"].shape == (5,)
    assert result["porosity"]["sensitivity"] > 0


def test_advanced_visualization_current_api():
    dates = pd.to_datetime(["2024-01-01", "2024-02-01"] * 2)
    data = pd.DataFrame({
        "well": ["A", "A", "B", "B"],
        "date": dates,
        "oil_rate": [100.0, 90.0, 80.0, 70.0],
        "cum_oil": [10.0, 20.0, 8.0, 16.0],
        "cum_gas": [100.0, 200.0, 80.0, 160.0],
        "water_cut": [0.1, 0.2, 0.15, 0.25],
    })
    visualization = AdvancedVisualization()
    visualization.load_data({"production": data})

    visualization.create_production_dashboard()

    assert set(visualization.figures["production"]) == {
        "history", "cross_plot", "heatmap"
    }


def test_workflow_automation_dependencies(monkeypatch):
    monkeypatch.setattr(
        WorkflowAutomation,
        "_setup_logger",
        lambda self: logging.Logger("test-workflow-automation"),
    )
    calls = []
    workflow = WorkflowAutomation()
    workflow.register_workflow(
        "test",
        [{"name": "record", "function": calls.append, "args": ["ran"]}],
    )

    workflow.run_workflow("test")

    assert calls == ["ran"]
    assert workflow.workflows["test"]["status"] == "completed"
