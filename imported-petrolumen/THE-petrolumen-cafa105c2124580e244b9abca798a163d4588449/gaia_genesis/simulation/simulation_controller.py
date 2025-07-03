import numpy as np
from typing import Dict, List, Optional
from .black_oil_simulator import BlackOilSimulator
from .compositional_simulator import CompositionalSimulator
from .thermal_simulator import ThermalSimulator
from .network_designer import NetworkDesigner
from .parallel_engine import ParallelEngine
from ..pvt.correlations import *
from ..visualization.results_visualizer import ResultsVisualizer

class SimulationController:
    """Master controller for reservoir simulation"""
    
    def __init__(self, simulation_type: str = "black_oil"):
        self.simulation_type = simulation_type
        self.simulator = self._create_simulator()
        self.network = NetworkDesigner()
        self.parallel_engine = ParallelEngine()
        self.results_history = []
        self.visualizer = ResultsVisualizer()
        
    def _create_simulator(self):
        """Create appropriate simulator instance"""
        if self.simulation_type == "black_oil":
            return BlackOilSimulator()
        elif self.simulation_type == "compositional":
            return CompositionalSimulator()
        elif self.simulation_type == "thermal":
            return ThermalSimulator()
        else:
            raise ValueError(f"Unknown simulation type: {self.simulation_type}")
            
    def setup_model(self, model_data: Dict):
        """Set up simulation model"""
        # Grid setup
        self.simulator.setup_grid(**model_data["grid"])
        
        # Rock properties
        self.simulator.set_rock_properties(**model_data["rock"])
        
        # Fluid properties
        self.simulator.set_fluid_properties(model_data["pvt"])
        
        # Wells
        for well in model_data["wells"]:
            self.simulator.add_well(**well)
            
        # Surface network if provided
        if "network" in model_data:
            self._setup_network(model_data["network"])
            
    def initialize_simulation(self, initial_conditions: Dict):
        """Initialize simulation state"""
        self.simulator.initialize(**initial_conditions)
        
    def run_simulation(self, timesteps: List[float],
                      report_frequency: int = 1):
        """Run full simulation"""
        results = []
        for i, dt in enumerate(timesteps):
            self.simulator.run_timestep(dt)
            
            if (i + 1) % report_frequency == 0:
                result = self.simulator.get_results()
                if hasattr(self.simulator, 'get_thermal_results'):
                    result.update(self.simulator.get_thermal_results())
                results.append(result)
                
        self.results_history.extend(results)
        return results
        
    def _setup_network(self, network_data: Dict):
        """Set up surface network"""
        # Add wells
        for well in network_data["wells"]:
            self.network.add_well(**well)
            
        # Add separators
        for sep in network_data.get("separators", []):
            self.network.add_separator(**sep)
            
        # Add pipelines
        for pipe in network_data.get("pipelines", []):
            self.network.add_pipeline(**pipe)
            
    def get_results(self, result_type: str = "all") -> Dict:
        """Get simulation results"""
        if not self.results_history:
            return {}
            
        if result_type == "all":
            return self.results_history[-1]
        elif result_type == "pressure":
            return {"pressure": self.results_history[-1]["pressure"]}
        elif result_type == "saturations":
            return {"saturations": self.results_history[-1]["saturations"]}
        elif result_type == "production":
            return {"wells": self.results_history[-1]["wells"]}
        else:
            raise ValueError(f"Unknown result type: {result_type}")
            
    def get_timestep_results(self, timestep: int) -> Dict:
        """Get results for specific timestep"""
        if 0 <= timestep < len(self.results_history):
            return self.results_history[timestep]
        else:
            raise ValueError(f"Invalid timestep: {timestep}")
            
    def export_results(self, filename: str, format: str = "csv"):
        """Export simulation results"""
        if format == "csv":
            self._export_csv(filename)
        elif format == "vtk":
            self._export_vtk(filename)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
    def _export_csv(self, filename: str):
        """Export results to CSV format"""
        import pandas as pd
        
        # Collect all timestep data
        data = []
        for step, result in enumerate(self.results_history):
            row = {"timestep": step}
            row.update(self._flatten_results(result))
            data.append(row)
            
        # Create and save DataFrame
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        
    def _export_vtk(self, filename: str):
        """Export results to VTK format"""
        import vtk
        from vtk.util import numpy_support
        
        # Create VTK grid
        grid = vtk.vtkStructuredGrid()
        # Add geometry and properties
        # Save to file
        writer = vtk.vtkXMLStructuredGridWriter()
        writer.SetFileName(filename)
        writer.SetInputData(grid)
        writer.Write()
        
    def _flatten_results(self, results: Dict, 
                        prefix: str = "") -> Dict:
        """Flatten nested results dictionary"""
        flat = {}
        for key, value in results.items():
            if isinstance(value, dict):
                flat.update(self._flatten_results(value, f"{prefix}{key}_"))
            elif isinstance(value, np.ndarray):
                flat[f"{prefix}{key}"] = value.mean()  # Or other reduction
            else:
                flat[f"{prefix}{key}"] = value
        return flat
    
    def visualize_results(self, results: Dict):
        """Visualize simulation results"""
        self.visualizer.load_results(results)
        # Create standard plots
        pressure_map = self.visualizer.plot_pressure_map(layer=0)
        rates = self.visualizer.plot_well_rates("PROD-1")
        return pressure_map, rates
