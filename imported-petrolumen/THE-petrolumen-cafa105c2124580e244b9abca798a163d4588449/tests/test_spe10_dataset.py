import os
import numpy as np
import pandas as pd
from pathlib import Path
import requests
import zipfile
import lasio
import segyio
import pyvista as pv

from gaia_genesis.reservoir_engineering.static_modeling import StaticModel
from gaia_genesis.reservoir_engineering.flow_simulation import FlowSimulator
from gaia_genesis.reservoir_engineering.geostatistics import Geostatistics
from gaia_genesis.reservoir_engineering.history_matching import HistoryMatcher

def download_spe10_dataset():
    """Download SPE10 dataset."""
    url = "https://www.spe.org/web/csp/datasets/SPE10.zip"
    zip_path = "spe10_data.zip"
    
    if not os.path.exists(zip_path):
        print("Downloading SPE10 dataset...")
        response = requests.get(url)
        with open(zip_path, 'wb') as f:
            f.write(response.content)
            
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("spe10_data")
            
    return "spe10_data"

def test_static_modeling():
    """Test static modeling with SPE10 data."""
    print("\nTesting Static Modeling...")
    
    # Initialize model
    model = StaticModel()
    
    # Import well data
    well_files = [
        "spe10_data/wells/INJ1.las",
        "spe10_data/wells/INJ2.las",
        "spe10_data/wells/PROD1.las",
        "spe10_data/wells/PROD2.las"
    ]
    well_names = ["INJ1", "INJ2", "PROD1", "PROD2"]
    
    model.import_well_data(well_files, well_names)
    
    # Import seismic data
    model.import_seismic_data("spe10_data/seismic/seismic.segy")
    
    # Create grid
    model.create_grid(nx=60, ny=220, nz=85, dx=20, dy=10, dz=2)
    
    # Calculate properties
    model.calculate_properties()
    
    # Visualize
    model.visualize_model(property_name="porosity", save_path="spe10_porosity.png")
    
    print("Static modeling test completed")

def test_flow_simulation():
    """Test flow simulation with SPE10 data."""
    print("\nTesting Flow Simulation...")
    
    # Initialize simulator
    simulator = FlowSimulator()
    
    # Setup simulation
    grid = pv.UniformGrid()
    grid.dimensions = (60, 220, 85)
    grid.cell_size = (20, 10, 2)
    
    fluids = {
        'oil': {
            'viscosity': 0.5,  # cp
            'density': 800,    # kg/m3
            'compressibility': 1e-5  # 1/bar
        },
        'water': {
            'viscosity': 0.3,  # cp
            'density': 1000,   # kg/m3
            'compressibility': 3e-5  # 1/bar
        }
    }
    
    initial_conditions = {
        'pressure': np.ones(grid.n_cells) * 200,  # bar
        'saturation': np.ones(grid.n_cells) * 0.2  # So
    }
    
    boundary_conditions = {
        'pressure': {
            'type': 'dirichlet',
            'value': 200  # bar
        }
    }
    
    simulator.setup_simulation(
        grid=grid,
        fluids=fluids,
        initial_conditions=initial_conditions,
        boundary_conditions=boundary_conditions
    )
    
    # Run simulation
    simulator.run_simulation(
        end_time=365,  # days
        max_dt=1,
        min_dt=0.1,
        target_dt=0.5
    )
    
    # Visualize results
    simulator.visualize_results(property_name="pressure", save_path="spe10_pressure.png")
    
    print("Flow simulation test completed")

def test_geostatistics():
    """Test geostatistics with SPE10 data."""
    print("\nTesting Geostatistics...")
    
    # Initialize geostatistics
    geo = Geostatistics()
    
    # Load well data
    well_data = pd.read_csv("spe10_data/well_data.csv")
    coordinates = well_data[['x', 'y', 'z']].values
    values = well_data['porosity'].values
    
    # Calculate variogram
    geo.calculate_variogram(
        coordinates=coordinates,
        values=values,
        model='spherical',
        max_dist=1000
    )
    
    # Perform kriging
    grid_coordinates = np.meshgrid(
        np.linspace(0, 1200, 60),
        np.linspace(0, 2200, 220),
        np.linspace(0, 170, 85)
    )
    grid_coordinates = np.stack(grid_coordinates, axis=-1).reshape(-1, 3)
    
    kriged_values = geo.perform_kriging(
        coordinates=coordinates,
        values=values,
        grid_coordinates=grid_coordinates
    )
    
    # Visualize
    geo.visualize_variogram(save_path="spe10_variogram.png")
    
    print("Geostatistics test completed")

def test_history_matching():
    """Test history matching with SPE10 data."""
    print("\nTesting History Matching...")
    
    # Initialize matcher
    matcher = HistoryMatcher()
    
    # Define parameters
    parameters = {
        'permeability': {
            'initial': 100,
            'min': 10,
            'max': 1000
        },
        'porosity': {
            'initial': 0.2,
            'min': 0.1,
            'max': 0.3
        }
    }
    matcher.define_parameters(parameters)
    
    # Load historical data
    historical_data = pd.read_csv("spe10_data/production_data.csv")
    matcher.set_historical_data(historical_data)
    
    # Initialize simulator
    simulator = FlowSimulator()
    # ... setup simulator ...
    
    # Run matching
    results = matcher.run_matching(
        simulator=simulator,
        method='Nelder-Mead',
        max_iter=100
    )
    
    # Analyze uncertainty
    uncertainty = matcher.analyze_uncertainty(
        simulator=simulator,
        n_samples=100
    )
    
    # Visualize results
    matcher.visualize_results(
        simulator=simulator,
        save_path="spe10_history_matching"
    )
    
    print("History matching test completed")

def main():
    """Run all tests."""
    print("Starting SPE10 dataset tests...")
    
    # Download dataset
    data_dir = download_spe10_dataset()
    
    # Run tests
    test_static_modeling()
    test_flow_simulation()
    test_geostatistics()
    test_history_matching()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main() 