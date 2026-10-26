import numpy as np
from gaia_genesis.flow_simulation import FlowSimulation


def test_dry_gas_impes_depletion():
    """
    Test basic dry gas depletion simulation.
    Ensures that average pressure decreases when gas is produced.
    """
    # 5x5x1 grid
    sim = FlowSimulation(nx=5, ny=5, nz=1, dx=100.0, dy=100.0, dz=20.0)

    # 1 well in center (index 12 in 5x5 grid) producing 1000 scf/day
    wells = [{"cell_index": 12, "q_sc": 1000.0}]

    initial_p = np.mean(sim.pressure)

    # Run for 10 days
    results = sim.run_dry_gas_impes(dt_days=1.0, n_steps=10, wells=wells)

    final_p = results["pressure"][-1]

    assert (
        final_p < initial_p
    ), f"Pressure should decrease. Initial: {initial_p}, Final: {final_p}"
    assert len(results["time"]) == 10
    assert len(results["pressure"]) == 10


def test_dry_gas_impes_no_production():
    """
    Ensures pressure remains stable if there is no production.
    """
    sim = FlowSimulation(nx=3, ny=3, nz=1)
    initial_p = np.mean(sim.pressure)

    results = sim.run_dry_gas_impes(dt_days=1.0, n_steps=5, wells=[])

    final_p = results["pressure"][-1]
    assert np.isclose(
        final_p, initial_p, atol=1e-5
    ), f"Pressure should remain stable. Got {final_p}, expected {initial_p}"


def test_oil_water_impes_basic():
    """
    Test basic oil-water simulation with an injector and producer.
    """
    sim = FlowSimulation(nx=5, ny=1, nz=1)
    # Cell 0: Water Injector, Cell 4: Oil Producer
    sim.saturation["water"] = np.ones(sim.num_cells) * 0.2
    sim.saturation["oil"] = np.ones(sim.num_cells) * 0.8

    wells = [
        {"cell_index": 0, "q_total": -50.0},  # Injection (Negative)
        {"cell_index": 4, "q_total": 50.0},  # Production (Positive)
    ]

    results = sim.run_oil_water_impes(dt_days=1.0, n_steps=20, wells=wells)

    # In a 1D flood, water saturation at the injector cell should increase
    assert (
        sim.saturation["water"][0] > 0.2
    ), f"Water saturation should increase at injector. Got {sim.saturation['water'][0]}"
    # Overall average water saturation should increase
    assert results["water_saturation"][-1] > results["water_saturation"][0]


from gaia_genesis.reservoir_engineering import WellTesting


def test_radial_drawdown_to_welltest_analysis():
    """
    Integration test: Run a radial simulation and analyze the results using Horner/Semi-log.
    """
    sim = FlowSimulation(mesh_type="radial")
    # 50 cells, rw=0.3, re=2000, h=50
    sim.create_radial_grid(nr=50, rw=0.3, re=2000.0, h=50.0)
    sim.permeability = np.ones(50) * 150.0  # 150 md

    # Run drawdown for 72 hours at 200 bbl/day
    res = sim.run_radial_drawdown(dt_hours=1.0, n_steps=72, q_bbl_day=200.0)

    wt = WellTesting()
    # Semi-log analysis on drawdown (similar logic to buildup)
    # Using analyze_buildup with tp large to simulate drawdown semi-log
    # mu=1.0, bo=1.1, ct=1e-5, phi=0.2, rw=0.3, h=50
    analysis = wt.analyze_buildup(
        time=res["time"],
        pressure=res["pwf"],
        tp=10000.0,  # Large tp for drawdown
        rate=200.0,
        mu=1.0,
        bo=1.1,
        ct=1e-5,
        phi=0.2,
        rw=0.3,
        h=50.0,
    )

    # We expect k to be close to 150 md
    # Numerical error and grid effects will exist, but it should be within 20%
    assert (
        120.0 < analysis["permeability"] < 180.0
    ), f"Permeability mismatch. Got {analysis['permeability']}"
