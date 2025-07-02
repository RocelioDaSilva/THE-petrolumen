from typing import List, Tuple, Dict, Any
import numpy as np

class ReservoirSimulator:
    def create_structured_grid(self, nx: int, ny: int, nz: int, dx: float, dy: float, dz: float) -> None:
        """Defines a structured simulation grid."""
        pass

    def add_property(self, name: str, values: np.ndarray) -> None:
        """Adds petrophysical properties (e.g., porosity, permeability) to the grid."""
        pass

    def add_well(self, name: str, trajectory: List[Tuple[float, float, float]], completions: List[Dict[str, Any]]) -> None:
        """Defines a production/injection well."""
        pass

    def convert_well_type(self, name: str, new_type: str) -> None:
        """Changes a well's type (e.g., from producer to injector)."""
        pass

    def run_simulation(self, end_time: float, time_step: float) -> None:
        """Executes the reservoir simulation."""
        pass

    def plot_property_slice(self, property_name: str, slice_axis: str = 'z', slice_index: int = 0) -> None:
        """Visualizes a slice of a grid property."""
        # In a real scenario, this might return a Plotly figure object or save to a file
        pass

    def plot_3d_model(self) -> None:
        """Renders a 3D view of the reservoir model."""
        # In a real scenario, this might return a Plotly figure object or save to a file
        pass

    def plot_well_results(self, well_name: str) -> None:
        """Plots simulation results for a specific well."""
        # In a real scenario, this might return a Plotly figure object or save to a file
        pass

    def plot_field_results(self) -> None:
        """Plots overall field simulation results."""
        # In a real scenario, this might return a Plotly figure object or save to a file
        pass

    def run_sensitivity_analysis(self, parameter: str, values: List[Any], metric: str) -> Dict[str, Any]:
        """Performs sensitivity analysis on a given parameter. Returns sensitivity data."""
        pass

    def plot_sensitivity_results(self, sensitivity_data: Dict[str, Any], parameter_name: str, metric_name: str) -> None:
        """Visualizes sensitivity analysis results."""
        # In a real scenario, this might return a Plotly figure object or save to a file
        pass
