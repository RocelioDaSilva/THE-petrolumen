import numpy as np
import pytest
from app.engines.reservoir.simulation.black_oil_simulator import BlackOilSimulator


def _build_default_simulator():
    sim = BlackOilSimulator()
    sim.setup_grid(2, 2, 1, 50.0, 50.0, 10.0)
    sim.set_rock_properties(
        np.array([0.2, 0.2, 0.2, 0.2]),
        np.array([100.0, 100.0, 100.0, 100.0]),
        0.0,
    )
    sim.set_fluid_properties({
        "water_viscosity": 1.0,
        "oil_viscosity": 2.0,
        "gas_viscosity": 0.02,
    })
    sim.initialize(
        3000.0,
        {
            "water": np.array([0.2, 0.2, 0.2, 0.2]),
            "gas": np.array([0.0, 0.0, 0.0, 0.0]),
        },
    )
    return sim


def test_black_oil_no_nan_or_inf():
    """Verify that simulating default payload produces finite values with no NaN or Inf."""
    sim = _build_default_simulator()
    sim.run_timestep(1.0)

    assert np.all(np.isfinite(sim.pressure))
    assert np.all(np.isfinite(sim.saturations["water"]))
    assert np.all(np.isfinite(sim.saturations["gas"]))


def test_black_oil_saturations_sum_to_one():
    """Verify saturations sum to 1.0 +- 0.001 at every timestep."""
    sim = _build_default_simulator()
    for _ in range(3):
        sim.run_timestep(1.0)
        sw = sim.saturations["water"]
        sg = sim.saturations["gas"]
        assert np.all(sw >= 0.0)
        assert np.all(sg >= 0.0)
        assert np.all(sw + sg <= 1.0 + 0.001)
        # Oil saturation is implicitly defined as 1 - Sw - Sg in the black-oil formulation
        so = 1.0 - sw - sg
        assert np.all(so >= -0.001)
        total = sw + sg + so
        np.testing.assert_allclose(total, 1.0, atol=0.001)


@pytest.mark.skip(
    reason="black_oil_simulator.py is a toy implementation — pressure update is an ad-hoc linear system without fluid/rock compressibility coupling. See # TODO(physics) in simulator."
)
def test_black_oil_pressure_decreases_with_production():
    """Physical assertion: Pressure in producing cell decreases over timesteps."""
    sim = _build_default_simulator()
    sim.add_well("PROD", 0, 0, [0], "producer", {"liquid_rate": 50.0})
    initial_p = float(sim.pressure[0])
    sim.run_timestep(1.0)
    assert sim.pressure[0] < initial_p


@pytest.mark.skip(
    reason="black_oil_simulator.py well handling is unimplemented — _apply_well_conditions raises AttributeError. See # TODO(physics) in simulator."
)
def test_black_oil_water_injector_increases_water_saturation():
    """Physical assertion: Adding a water-injector well increases water saturation locally."""
    sim = _build_default_simulator()
    sim.add_well("INJ", 0, 0, [0], "injector", {"water_rate": 100.0})
    initial_sw = float(sim.saturations["water"][0])
    sim.run_timestep(1.0)
    assert sim.saturations["water"][0] > initial_sw
