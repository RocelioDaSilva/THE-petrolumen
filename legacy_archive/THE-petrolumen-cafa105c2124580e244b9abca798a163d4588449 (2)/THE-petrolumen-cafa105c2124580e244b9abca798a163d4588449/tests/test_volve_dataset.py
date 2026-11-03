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

def download_volve_dataset():
    """Download Volve dataset."""
    url = "https://www.equinor.com/content/dam/statoil/documents/what-we-do/digitalisation-in-our-dna/volve-data-village.zip"
    zip_path = "volve_data.zip"
    
    if not os.path.exists(zip_path):
        print("Downloading Volve dataset...")
        response = requests.get(url)
        with open(zip_path, 'wb') as f:
            f.write(response.content)
            
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("volve_data")
            
    return "volve_data"

def test_static_modeling():
    """Test static modeling with Volve data."""
    print("\nTesting Static Modeling...")
    
    # Initialize model
    model = StaticModel()
    
    # Import well data
    well_files = [
        "volve_data/15_9-F-1A.las",
        "volve_data/15_9-F-1B.las",
        "volve_data/15_9-F-1C.las"
    ]
    well_names = ["F-1A", "F-1B", "F-1C"]
    
    model.import_well_data(well_files, well_names)
    
    # Import seismic data
    model.import_seismic_data("volve_data/seismic.segy")
    
    # Create grid
    model.create_grid(nx=100, ny=100, nz=50, dx=100, dy=100, dz=10)
    
    # Calculate properties
    model.calculate_properties()
    
    # Visualize
    model.visualize_model(property_name="porosity", save_path="volve_porosity.png")
    
    print("Static modeling test completed")

def test_flow_simulation():
    """Test flow simulation with Volve data."""
    print("\nTesting Flow Simulation...")
    
    # Initialize simulator
    simulator = FlowSimulator()
    
    # Setup simulation
    grid = pv.UniformGrid()
    grid.dimensions = (100, 100, 50)
    grid.cell_size = (100, 100, 10)
    
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
    simulator.visualize_results(property_name="pressure", save_path="volve_pressure.png")
    
    print("Flow simulation test completed")

def test_geostatistics():
    """Test geostatistics with Volve data."""
    print("\nTesting Geostatistics...")
    
    # Initialize geostatistics
    geo = Geostatistics()
    
    # Load well data
    well_data = pd.read_csv("volve_data/well_data.csv")
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
        np.linspace(0, 10000, 100),
        np.linspace(0, 10000, 100),
        np.linspace(0, 5000, 50)
    )
    grid_coordinates = np.stack(grid_coordinates, axis=-1).reshape(-1, 3)
    
    kriged_values = geo.perform_kriging(
        coordinates=coordinates,
        values=values,
        grid_coordinates=grid_coordinates
    )
    
    # Visualize
    geo.visualize_variogram(save_path="volve_variogram.png")
    
    print("Geostatistics test completed")

def test_history_matching():
    """Test history matching with Volve data."""
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
    historical_data = pd.read_csv("volve_data/production_data.csv")
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
        save_path="volve_history_matching"
    )
    
    print("History matching test completed")

def main():
    """Run all tests."""
    print("Starting Volve dataset tests...")
    
    # Download dataset
    data_dir = download_volve_dataset()
    
    # Run tests
    test_static_modeling()
    test_flow_simulation()
    test_geostatistics()
    test_history_matching()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main() 