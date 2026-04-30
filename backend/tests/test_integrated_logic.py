import pytest
import numpy as np
from gaia_genesis.flow_simulation import FlowSimulation
from gaia_genesis.static_modeling import StaticModeling
from gaia_genesis.pvt import EosSolver
from gaia_genesis.dca_advanced import perform_ple_fit, perform_sepd_fit

def test_implicit_flow_sim():
    # Test 1D Implicit Solver stability and results
    sim = FlowSimulation(nx=10, dx=100)
    wells = [{"cell_index": 5, "q_sc": 500}] # Producing from middle cell
    results = sim.run_simulation(end_time=100, dt=1, wells=wells)

    assert results["status"] == "Completed"
    pressures = results["pressures_vs_time"]
    assert len(pressures) > 1
    # Check that pressure decreased at well location
    assert pressures[-1][5] < pressures[0][5]
    # Check for consistency
    assert len(pressures[-1]) == 10

def test_ordinary_kriging_logic():
    sm = StaticModeling()
    sm.create_3d_grid(nx=10, ny=10, nz=1, dx=10, dy=10, dz=1)
    # Add scattered well data
    sm.add_well_data("W1", 20, 20, np.array([0]), {"perm": np.array([100.0])})
    sm.add_well_data("W2", 80, 80, np.array([0]), {"perm": np.array([200.0])})

    sm.kriging_interpolation("perm", variogram_model="spherical")
    grid = sm.properties["perm"]

    assert grid.shape == (10, 10)
    # Check that it interpolates
    # Values at well locations should be exactly the well values
    assert np.isclose(grid[2, 2], 100.0)
    assert np.isclose(grid[8, 8], 200.0)
    assert not np.isnan(grid).any()

def test_eos_solver_compositional():
    eos = EosSolver(eos_type="PR")
    # Methane properties
    eos.add_component("C1", {
        "critical_pressure": 46.0, # bar
        "critical_temperature": 190.6, # K
        "acentric_factor": 0.011,
        "molecular_weight": 16.04
    })

    composition = {"C1": 1.0}
    # Test Z-factor calculation at 100 bar, 300 K
    z = eos.calculate_z_factor(P=10.0, T=300.0, composition=composition) # simplified P units for test
    assert 0.7 < z < 1.0

def test_advanced_dca_integration():
    time = np.linspace(0, 100, 20)
    # Generate synthetic PLE data
    qi, di, d_inf, n = 1000, 0.1, 0.01, 0.5
    rate = qi * np.exp(-d_inf * time - di * time**n)

    ple_results = perform_ple_fit(time, rate)
    assert ple_results["model"] == "PLE"
    assert ple_results["r_squared"] > 0.9

    # Generate synthetic SEPD data
    qi, tau, n = 1000, 50, 0.6
    rate_sepd = qi * np.exp(-((time / tau) ** n))
    sepd_results = perform_sepd_fit(time, rate_sepd)
    assert sepd_results["model"] == "SEPD"
    assert sepd_results["r_squared"] > 0.9
