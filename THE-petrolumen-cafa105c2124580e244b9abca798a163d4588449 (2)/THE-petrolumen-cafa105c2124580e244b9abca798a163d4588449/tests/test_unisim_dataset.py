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

def download_unisim_dataset():
    """Download UNISIM-I dataset."""
    url = "http://www.unisim.cepetro.unicamp.br/unisim-i/UNISIM-I-D.zip"
    zip_path = "unisim_data.zip"
    
    if not os.path.exists(zip_path):
        print("Downloading UNISIM-I dataset...")
        response = requests.get(url)
        with open(zip_path, 'wb') as f:
            f.write(response.content)
            
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("unisim_data")
            
    return "unisim_data"

def test_static_modeling():
    """Test static modeling with UNISIM-I data."""
    print("\nTesting Static Modeling...")
    
    # Initialize model
    model = StaticModel()
    
    # Import well data
    well_files = [
        "unisim_data/wells/INJ1.las",
        "unisim_data/wells/INJ2.las",
        "unisim_data/wells/INJ3.las",
        "unisim_data/wells/PROD1.las",
        "unisim_data/wells/PROD2.las",
        "unisim_data/wells/PROD3.las"
    ]
    well_names = ["INJ1", "INJ2", "INJ3", "PROD1", "PROD2", "PROD3"]
    
    model.import_well_data(well_files, well_names)
    
    # Import seismic data
    model.import_seismic_data("unisim_data/seismic/seismic.segy")
    
    # Create grid
    model.create_grid(nx=200, ny=200, nz=100, dx=50, dy=50, dz=5)
    
    # Calculate properties
    model.calculate_properties()
    
    # Visualize
    model.visualize_model(property_name="porosity", save_path="unisim_porosity.png")
    
    print("Static modeling test completed")

def test_flow_simulation():
    """Test flow simulation with UNISIM-I data."""
    print("\nTesting Flow Simulation...")
    
    # Initialize simulator
    simulator = FlowSimulator()
    
    # Setup simulation
    grid = pv.UniformGrid()
    grid.dimensions = (200, 200, 100)
    grid.cell_size = (50, 50, 5)
    
    fluids = {
        'oil': {
            'viscosity': 0.7,  # cp
            'density': 850,    # kg/m3
            'compressibility': 1e-5  # 1/bar
        },
        'water': {
            'viscosity': 0.3,  # cp
            'density': 1000,   # kg/m3
            'compressibility': 3e-5  # 1/bar
        }
    }
    
    initial_conditions = {
        'pressure': np.ones(grid.n_cells) * 250,  # bar
        'saturation': np.ones(grid.n_cells) * 0.2  # So
    }
    
    boundary_conditions = {
        'pressure': {
            'type': 'dirichlet',
            'value': 250  # bar
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
    simulator.visualize_results(property_name="pressure", save_path="unisim_pressure.png")
    
    print("Flow simulation test completed")

def test_geostatistics():
    """Test geostatistics with UNISIM-I data."""
    print("\nTesting Geostatistics...")
    
    # Initialize geostatistics
    geo = Geostatistics()
    
    # Load well data
    well_data = pd.read_csv("unisim_data/well_data.csv")
    coordinates = well_data[['x', 'y', 'z']].values
    values = well_data['porosity'].values
    
    # Calculate variogram
    geo.calculate_variogram(
        coordinates=coordinates,
        values=values,
        model='spherical',
        max_dist=2000
    )
    
    # Perform kriging
    grid_coordinates = np.meshgrid(
        np.linspace(0, 10000, 200),
        np.linspace(0, 10000, 200),
        np.linspace(0, 500, 100)
    )
    grid_coordinates = np.stack(grid_coordinates, axis=-1).reshape(-1, 3)
    
    kriged_values = geo.perform_kriging(
        coordinates=coordinates,
        values=values,
        grid_coordinates=grid_coordinates
    )
    
    # Visualize
    geo.visualize_variogram(save_path="unisim_variogram.png")
    
    print("Geostatistics test completed")

def test_history_matching():
    """Test history matching with UNISIM-I data."""
    print("\nTesting History Matching...")
    
    # Initialize matcher
    matcher = HistoryMatcher()
    
    # Define parameters
    parameters = {
        'permeability': {
            'initial': 200,
            'min': 20,
            'max': 2000
        },
        'porosity': {
            'initial': 0.25,
            'min': 0.15,
            'max': 0.35
        }
    }
    matcher.define_parameters(parameters)
    
    # Load historical data
    historical_data = pd.read_csv("unisim_data/production_data.csv")
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
        save_path="unisim_history_matching"
    )
    
    print("History matching test completed")

def main():
    """Run all tests."""
    print("Starting UNISIM-I dataset tests...")
    
    # Download dataset
    data_dir = download_unisim_dataset()
    
    # Run tests
    test_static_modeling()
    test_flow_simulation()
    test_geostatistics()
    test_history_matching()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main() 