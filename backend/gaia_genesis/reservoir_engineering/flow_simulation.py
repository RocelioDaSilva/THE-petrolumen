from typing import List, Tuple, Dict, Any
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ReservoirSimulator:
    def __init__(self):
        self.grid: Dict[str, Any] = {}
        self.properties: Dict[str, np.ndarray] = {}
        self.wells: Dict[str, Dict[str, Any]] = {}
        self.simulation_results: Dict[str, Any] = {} # To store some dummy results

    def create_structured_grid(self, nx: int, ny: int, nz: int, dx: float, dy: float, dz: float) -> None:
        """Defines a structured simulation grid."""
        if not all(isinstance(dim, int) and dim > 0 for dim in [nx, ny, nz]):
            raise ValueError("Grid dimensions (nx, ny, nz) must be positive integers.")
        if not all(isinstance(spacing, (float, int)) and spacing > 0 for spacing in [dx, dy, dz]):
            raise ValueError("Grid spacings (dx, dy, dz) must be positive numbers.")

        self.grid = {
            'type': 'structured',
            'nx': nx, 'ny': ny, 'nz': nz,
            'dx': dx, 'dy': dy, 'dz': dz
        }
        logger.info(f"Created structured grid: {nx}x{ny}x{nz} with spacings {dx}x{dy}x{dz}")

    def add_property(self, name: str, values: np.ndarray) -> None:
        """Adds petrophysical properties (e.g., porosity, permeability) to the grid."""
        if not self.grid:
            raise ValueError("Grid must be created before adding properties.")

        expected_size = self.grid['nx'] * self.grid['ny'] * self.grid['nz']
        if values.size != expected_size:
            raise ValueError(f"Property '{name}' array size ({values.size}) does not match grid size ({expected_size}).")

        self.properties[name] = values
        logger.info(f"Added property '{name}' to the grid.")

    def add_well(self, name: str, trajectory: List[Tuple[float, float, float]],
                 completions: List[Dict[str, Any]], well_type: str = "producer") -> None:
        """Defines a production/injection well."""
        if name in self.wells:
            logger.warning(f"Well '{name}' already exists. Overwriting.")

        self.wells[name] = {
            'trajectory': trajectory,
            'completions': completions,
            'type': well_type # e.g., "producer", "injector"
        }
        logger.info(f"Added well '{name}' of type '{well_type}'.")

    def convert_well_type(self, name: str, new_type: str) -> None:
        """Changes a well's type (e.g., from producer to injector)."""
        if name not in self.wells:
            raise ValueError(f"Well '{name}' not found.")

        old_type = self.wells[name]['type']
        self.wells[name]['type'] = new_type
        logger.info(f"Converted well '{name}' from type '{old_type}' to '{new_type}'.")

    def run_simulation(self, end_time: float, time_step: float) -> None:
        """Executes the reservoir simulation."""
        if not self.grid:
            raise ValueError("Grid must be defined to run simulation.")
        if not self.wells:
            logger.warning("Running simulation with no wells defined.")
        if end_time <= 0 or time_step <= 0:
            raise ValueError("End time and time step must be positive.")

        logger.info(f"Starting simulation: end_time={end_time}, time_step={time_step}")
        # This is a placeholder for actual complex simulation logic.
        # A real simulator would solve PDEs for fluid flow.

        # Simulate some dummy results
        self.simulation_results['time_steps'] = np.arange(0, end_time + time_step, time_step)
        for well_name, well_data in self.wells.items():
            if well_data['type'] == 'producer':
                # Simulate declining production
                rates = 1000 * np.exp(-0.1 * self.simulation_results['time_steps']) * (np.random.rand(len(self.simulation_results['time_steps']))*0.2 + 0.9)
                self.simulation_results[f'{well_name}_oil_rate'] = rates
            elif well_data['type'] == 'injector':
                 # Simulate constant injection
                rates = 500 * (np.random.rand(len(self.simulation_results['time_steps']))*0.1 + 0.95)
                self.simulation_results[f'{well_name}_water_injection_rate'] = rates

        logger.info("Simulation run completed (placeholder).")
        print("Reservoir simulation run (placeholder execution).")

    def plot_property_slice(self, property_name: str, slice_axis: str = 'z', slice_index: int = 0) -> str:
        """Visualizes a slice of a grid property."""
        if property_name not in self.properties:
            return f"Property '{property_name}' not found."
        if not self.grid:
            return "Grid not defined."

        # Placeholder for actual plotting logic (e.g., using Matplotlib or Plotly)
        # Example:
        # prop = self.properties[property_name].reshape((self.grid['nz'], self.grid['ny'], self.grid['nx']))
        # if slice_axis == 'z':
        #     data_slice = prop[slice_index, :, :]
        # elif slice_axis == 'y':
        #     data_slice = prop[:, slice_index, :]
        # else: # slice_axis == 'x'
        #     data_slice = prop[:, :, slice_index]
        # plt.imshow(data_slice); plt.colorbar(); plt.title(f'{property_name} - Slice {slice_axis}={slice_index}')
        # plt.show()

        logger.info(f"Plotting property slice for '{property_name}', axis {slice_axis}, index {slice_index}.")
        return f"Plot of property slice '{property_name}' (axis {slice_axis}, index {slice_index}) would be generated here."

    def plot_3d_model(self) -> str:
        """Renders a 3D view of the reservoir model."""
        if not self.grid:
            return "Grid not defined to render 3D model."
        # Placeholder for 3D plotting (e.g., using PyVista or Plotly)
        logger.info("Generating 3D model plot.")
        return "3D model plot would be generated here."

    def plot_well_results(self, well_name: str) -> str:
        """Plots simulation results for a specific well."""
        if well_name not in self.wells:
            return f"Well '{well_name}' not found."
        if not self.simulation_results or f'{well_name}_oil_rate' not in self.simulation_results and f'{well_name}_water_injection_rate' not in self.simulation_results :
            return f"No simulation results found for well '{well_name}'."

        # Placeholder for plotting (e.g., Plotly)
        # Example:
        # time = self.simulation_results['time_steps']
        # rates = self.simulation_results.get(f'{well_name}_oil_rate') or self.simulation_results.get(f'{well_name}_water_injection_rate')
        # plt.plot(time, rates); plt.title(f"Results for Well {well_name}"); plt.xlabel("Time"); plt.ylabel("Rate")
        # plt.show()
        logger.info(f"Plotting results for well '{well_name}'.")
        return f"Plot of simulation results for well '{well_name}' would be generated here."

    def plot_field_results(self) -> str:
        """Plots overall field simulation results."""
        if not self.simulation_results:
            return "No simulation results to plot for the field."

        # Placeholder for plotting (e.g., field oil production rate, total injection)
        logger.info("Plotting field results.")
        return "Plot of overall field simulation results would be generated here."

    def run_sensitivity_analysis(self, parameter_name: str, values: List[Any], metric: str) -> Dict[str, Any]:
        """Performs sensitivity analysis on a given parameter. Returns sensitivity data."""
        logger.info(f"Running sensitivity analysis for parameter '{parameter_name}' with values {values} on metric '{metric}'.")
        # This is a placeholder. Real sensitivity analysis would re-run simulations for each parameter value.

        results = {}
        # Example: if parameter_name is "permeability_multiplier" and metric is "total_oil_production"
        # For each value in 'values', adjust permeability, run simulation, get total oil.
        for val_idx, val in enumerate(values):
            # Dummy result: metric value increases with parameter value
            results[str(val)] = (val_idx + 1) * 1000

        logger.info(f"Sensitivity analysis completed. Results: {results}")
        return {"parameter_name": parameter_name, "values": values, "metric_name": metric, "results": results}

    def plot_sensitivity_results(self, sensitivity_data: Dict[str, Any], parameter_name: str, metric_name: str) -> str:
        """Visualizes sensitivity analysis results."""
        if not sensitivity_data or 'results' not in sensitivity_data:
            return "No sensitivity data provided or data is malformed."

        # Placeholder for plotting
        # Example:
        # param_values = sensitivity_data['values']
        # metric_outcomes = [sensitivity_data['results'][str(v)] for v in param_values]
        # plt.plot(param_values, metric_outcomes, marker='o')
        # plt.xlabel(parameter_name); plt.ylabel(metric_name); plt.title(f"Sensitivity of {metric_name} to {parameter_name}")
        # plt.show()
        logger.info(f"Plotting sensitivity results for parameter '{parameter_name}' and metric '{metric_name}'.")
        return f"Plot of sensitivity results for {parameter_name} vs {metric_name} would be generated here."

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    sim = ReservoirSimulator()
    sim.create_structured_grid(nx=10, ny=10, nz=3, dx=100.0, dy=100.0, dz=50.0)

    # Add porosity property (example)
    poro_values = np.full((10*10*3), 0.2) # Uniform porosity
    sim.add_property(name="porosity", values=poro_values)

    # Add a producer well
    sim.add_well(name="P1", trajectory=[(500,500,25), (500,500,75), (500,500,125)],
                 completions=[{'depth': 25, 'type': 'perforation'}, {'depth': 125, 'type': 'perforation'}],
                 well_type="producer")

    # Add an injector well
    sim.add_well(name="I1", trajectory=[(100,100,25), (100,100,75), (100,100,125)],
                 completions=[{'depth': 75, 'type': 'perforation'}],
                 well_type="injector")

    sim.run_simulation(end_time=365.0, time_step=30.0) # Simulate for 1 year

    print(sim.plot_property_slice(property_name="porosity", slice_axis='z', slice_index=0))
    print(sim.plot_well_results(well_name="P1"))
    print(sim.plot_field_results())

    sensitivity_data = sim.run_sensitivity_analysis(parameter_name="matrix_permeability",
                                                    values=[10, 50, 100],
                                                    metric="cumulative_oil_production")
    print(sim.plot_sensitivity_results(sensitivity_data, "matrix_permeability", "cumulative_oil_production"))

    sim.convert_well_type("P1", "injector") # Example of converting well type
    print(f"Well P1 new type: {sim.wells['P1']['type']}")
