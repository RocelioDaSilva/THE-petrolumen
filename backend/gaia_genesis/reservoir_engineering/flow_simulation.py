import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# For 3D visualization, libraries like PyVista or Mayavi could be used.
# This example will use Matplotlib for simpler 2D slice plotting.
# import pyvista as pv # Example if PyVista was used

class ReservoirSimulator:
    def __init__(self, name="DefaultSim"):
        self.name = name
        self.grid = None # Will store grid information (e.g., dimensions, cell sizes)
        self.properties = {} # e.g., {'porosity': np.array, 'permeability': np.array}
        self.wells = [] # List of well objects or dictionaries
        self.simulation_results = {} # To store results over time
        # For simplicity, this simulator won't implement complex physics,
        # but rather the structure for managing simulation entities.

    # --- Grid Management ---
    def create_structured_grid(self, nx: int, ny: int, nz: int, dx: float, dy: float, dz: float):
        """Defines a structured Cartesian grid."""
        if not (nx > 0 and ny > 0 and nz > 0 and dx > 0 and dy > 0 and dz > 0):
            raise ValueError("Grid dimensions and cell sizes must be positive.")
        self.grid = {
            'type': 'structured_cartesian',
            'nx': nx, 'ny': ny, 'nz': nz, # Number of cells in x, y, z
            'dx': dx, 'dy': dy, 'dz': dz, # Cell dimensions in x, y, z
            'total_cells': nx * ny * nz
        }
        # Initialize default properties if needed, e.g., all active cells
        self.properties['active_cells'] = np.ones((nx, ny, nz), dtype=bool)
        print(f"Structured grid created: {nx}x{ny}x{nz} cells. Total: {self.grid['total_cells']} cells.")

    def add_property(self, name: str, values: np.ndarray):
        """Adds a petrophysical property to the grid (e.g., porosity, permeability)."""
        if self.grid is None:
            raise RuntimeError("Grid must be created before adding properties.")

        expected_shape = (self.grid['nx'], self.grid['ny'], self.grid['nz'])
        if values.shape != expected_shape:
            raise ValueError(f"Property '{name}' array shape {values.shape} does not match grid dimensions {expected_shape}.")

        self.properties[name.lower()] = values
        print(f"Property '{name}' added/updated for the grid.")

    # --- Well Management ---
    def add_well(self, name: str, trajectory: list[tuple[int, int, int]], completions: list[dict]):
        """
        Defines a production/injection well.
        trajectory: List of (i, j, k) cell indices the well passes through.
        completions: List of dictionaries, e.g.,
                     [{'ijk': (i,j,k), 'type': 'producer', 'rate_target': 500, 'bhp_limit': 1000}, ...]
                     Completion 'type' could be 'producer', 'injector'.
        """
        if self.grid is None:
            raise RuntimeError("Grid must be created before adding wells.")

        for i, j, k in trajectory:
            if not (0 <= i < self.grid['nx'] and 0 <= j < self.grid['ny'] and 0 <= k < self.grid['nz']):
                raise ValueError(f"Trajectory point ({i},{j},{k}) for well '{name}' is outside grid boundaries.")

        # Validate completions
        for comp in completions:
            ci, cj, ck = comp.get('ijk', (None,None,None))
            if not (0 <= ci < self.grid['nx'] and 0 <= cj < self.grid['ny'] and 0 <= ck < self.grid['nz']):
                 raise ValueError(f"Completion point ({ci},{cj},{ck}) for well '{name}' is outside grid boundaries.")
            if comp.get('type') not in ['producer', 'injector']:
                raise ValueError(f"Invalid completion type '{comp.get('type')}' for well '{name}'. Must be 'producer' or 'injector'.")


        well_data = {
            'name': name,
            'trajectory': trajectory, # Path of the wellbore through grid cells
            'completions': completions, # Where the well is open to flow
            'type': completions[0]['type'] if completions else 'unknown', # Overall well type based on first completion
            'status': 'active' # e.g., active, shut-in
        }
        self.wells.append(well_data)
        print(f"Well '{name}' added with {len(trajectory)} trajectory points and {len(completions)} completions.")
        return well_data

    def convert_well_type(self, well_name: str, new_type: str):
        """Changes a well's type (e.g., from producer to injector)."""
        well_found = False
        for well in self.wells:
            if well['name'] == well_name:
                if new_type not in ['producer', 'injector', 'observer', 'shut-in']: # Added more types
                    raise ValueError(f"Invalid new well type '{new_type}'.")

                print(f"Converting well '{well_name}' from type '{well.get('type', 'unknown')}' to '{new_type}'.")
                well['type'] = new_type
                # This might also change how completions are handled or targets are set in a real sim
                for comp in well.get('completions', []):
                    comp['type'] = new_type # Assuming completion type aligns with well type
                well_found = True
                break
        if not well_found:
            raise ValueError(f"Well '{well_name}' not found.")

    # --- Simulation Execution (Conceptual) ---
    def run_simulation(self, end_time: float, time_steps: list[float]):
        """
        Executes the reservoir simulation (conceptual).
        In a real simulator, this would involve solving PDEs for flow.
        Here, we'll just simulate some dummy results.
        """
        if not self.grid or not self.wells:
            raise RuntimeError("Grid and wells must be defined before running simulation.")

        print(f"Starting simulation '{self.name}' up to time {end_time} with {len(time_steps)} steps.")

        current_time = 0.0
        self.simulation_results = {'time': [current_time]}
        for well in self.wells:
            self.simulation_results[well['name']] = {
                'oil_rate': [0.0], 'gas_rate': [0.0], 'water_rate': [0.0], 'bhp': [5000.0] # Initial dummy BHP
            }
            if well['type'] == 'injector':
                 self.simulation_results[well['name']]['injection_rate'] = [0.0]


        for dt in time_steps:
            current_time += dt
            self.simulation_results['time'].append(current_time)

            # Dummy result generation:
            for well in self.wells:
                if well['status'] != 'active': # Skip non-active wells
                    self.simulation_results[well['name']]['oil_rate'].append(0)
                    self.simulation_results[well['name']]['gas_rate'].append(0)
                    self.simulation_results[well['name']]['water_rate'].append(0)
                    self.simulation_results[well['name']]['bhp'].append(self.simulation_results[well['name']]['bhp'][-1]) # No change
                    if 'injection_rate' in self.simulation_results[well['name']]:
                        self.simulation_results[well['name']]['injection_rate'].append(0)
                    continue

                if well['type'] == 'producer':
                    # Simulate decline for producers
                    prev_oil_rate = self.simulation_results[well['name']]['oil_rate'][-1]
                    new_oil_rate = max(0, prev_oil_rate * np.exp(-0.01 * dt) + (np.random.rand()-0.5)*5) if prev_oil_rate >0 else 100 * np.random.rand()
                    if self.simulation_results[well['name']]['oil_rate'][-1] == 0 and len(self.simulation_results[well['name']]['oil_rate'])==1 : # Initial step
                        new_oil_rate = 100 + np.random.rand()*20 # Initial production

                    self.simulation_results[well['name']]['oil_rate'].append(new_oil_rate)
                    self.simulation_results[well['name']]['gas_rate'].append(new_oil_rate * (0.5 + np.random.rand()*0.2) ) # GOR
                    self.simulation_results[well['name']]['water_rate'].append(new_oil_rate * (0.1 + current_time *0.001)) # Increasing water cut
                    self.simulation_results[well['name']]['bhp'].append(max(500, self.simulation_results[well['name']]['bhp'][-1] - np.random.rand()*50))

                elif well['type'] == 'injector':
                    # Simulate constant injection for injectors (or could be pressure controlled)
                    target_inj_rate = well['completions'][0].get('rate_target', 1000) if well['completions'] else 1000
                    self.simulation_results[well['name']]['injection_rate'].append(target_inj_rate * (0.95 + np.random.rand()*0.1))
                    self.simulation_results[well['name']]['bhp'].append(min(8000, self.simulation_results[well['name']]['bhp'][-1] + np.random.rand()*100))
                    # Injectors typically don't "produce" oil/gas/water in this context
                    self.simulation_results[well['name']]['oil_rate'].append(0)
                    self.simulation_results[well['name']]['gas_rate'].append(0)
                    self.simulation_results[well['name']]['water_rate'].append(0)


            print(f"  ...simulated up to time {current_time:.2f}")

        # Convert results to DataFrame for easier handling later
        self.simulation_results['summary'] = pd.DataFrame(self.simulation_results['time'], columns=['Time'])
        for well in self.wells:
            for key in self.simulation_results[well['name']]:
                 self.simulation_results['summary'][f"{well['name']}_{key}"] = self.simulation_results[well['name']][key][1:] # [1:] to match time steps results

        print(f"Simulation '{self.name}' completed. Total time: {current_time}. Results stored.")
        return self.simulation_results

    # --- Visualization (Simplified) ---
    def plot_property_slice(self, property_name: str, slice_dim: str = 'z', slice_index: int = 0, file_path=None):
        """Visualizes a 2D slice of a grid property using Matplotlib."""
        if property_name not in self.properties:
            raise ValueError(f"Property '{property_name}' not found.")
        if self.grid is None:
            raise RuntimeError("Grid not defined.")

        prop_array = self.properties[property_name]

        plt.figure(figsize=(8, 6))
        if slice_dim.lower() == 'z':
            if not (0 <= slice_index < self.grid['nz']):
                raise ValueError(f"Slice index {slice_index} for Z is out of bounds (0-{self.grid['nz']-1}).")
            data_slice = prop_array[:, :, slice_index]
            plt.imshow(data_slice.T, origin='lower', aspect='auto', interpolation='nearest',
                       extent=[0, self.grid['nx']*self.grid['dx'], 0, self.grid['ny']*self.grid['dy']])
            plt.xlabel(f"X (cells, dx={self.grid['dx']})")
            plt.ylabel(f"Y (cells, dy={self.grid['dy']})")
            plt.title(f"{property_name} - Z-Slice at k={slice_index}")
        elif slice_dim.lower() == 'y':
            if not (0 <= slice_index < self.grid['ny']):
                raise ValueError(f"Slice index {slice_index} for Y is out of bounds (0-{self.grid['ny']-1}).")
            data_slice = prop_array[:, slice_index, :]
            plt.imshow(data_slice.T, origin='lower', aspect='auto', interpolation='nearest',
                       extent=[0, self.grid['nx']*self.grid['dx'], 0, self.grid['nz']*self.grid['dz']])
            plt.xlabel(f"X (cells, dx={self.grid['dx']})")
            plt.ylabel(f"Z (cells, dz={self.grid['dz']})")
            plt.title(f"{property_name} - Y-Slice at j={slice_index}")
        elif slice_dim.lower() == 'x':
            if not (0 <= slice_index < self.grid['nx']):
                raise ValueError(f"Slice index {slice_index} for X is out of bounds (0-{self.grid['nx']-1}).")
            data_slice = prop_array[slice_index, :, :]
            plt.imshow(data_slice.T, origin='lower', aspect='auto', interpolation='nearest',
                       extent=[0, self.grid['ny']*self.grid['dy'], 0, self.grid['nz']*self.grid['dz']])
            plt.xlabel(f"Y (cells, dy={self.grid['dy']})")
            plt.ylabel(f"Z (cells, dz={self.grid['dz']})")
            plt.title(f"{property_name} - X-Slice at i={slice_index}")
        else:
            raise ValueError("Invalid slice_dim. Choose 'x', 'y', or 'z'.")

        plt.colorbar(label=property_name)
        plt.grid(False)
        if file_path:
            plt.savefig(file_path)
            print(f"Property slice plot saved to {file_path}")
        else:
            plt.show()

    def plot_3d_model(self):
        """Renders a 3D view of the reservoir model (placeholder)."""
        print("plot_3d_model: 3D visualization requires a dedicated library like PyVista or Mayavi.")
        print("This is a placeholder. In a real scenario, you would use such a library to render the grid, properties, and wells.")
        if self.grid:
            print(f"Grid dimensions: {self.grid['nx']}x{self.grid['ny']}x{self.grid['nz']}")
        if self.properties:
            print(f"Available properties: {list(self.properties.keys())}")
        # Example with PyVista (if installed and configured):
        # if self.grid and 'pyvista' in sys.modules:
        #     grid_pv = pv.UniformGrid()
        #     grid_pv.dimensions = np.array([self.grid['nx'], self.grid['ny'], self.grid['nz']]) + 1
        #     grid_pv.origin = (0, 0, 0)
        #     grid_pv.spacing = (self.grid['dx'], self.grid['dy'], self.grid['dz'])
        #     if 'porosity' in self.properties: # Add a sample property
        #         grid_pv.cell_data['porosity'] = self.properties['porosity'].flatten(order='F') # Fortran order for VTK
        #     grid_pv.plot(show_edges=True)


    def plot_well_results(self, well_name: str, metrics: list[str] = ['oil_rate', 'bhp'], file_path=None):
        """Plots simulation results (e.g., rate, pressure) for a specific well."""
        if not self.simulation_results or 'time' not in self.simulation_results:
            print("No simulation results available.")
            return
        if well_name not in self.simulation_results:
            print(f"No results found for well '{well_name}'. Available wells: { [k for k in self.simulation_results if k not in ['time', 'summary']] }")
            return

        time_data = self.simulation_results['time'][1:] # Exclude initial time 0 if results start from first step
        well_data = self.simulation_results[well_name]

        num_metrics = len(metrics)
        if num_metrics == 0:
            print("No metrics specified for plotting.")
            return

        fig, axes = plt.subplots(num_metrics, 1, figsize=(10, 4 * num_metrics), sharex=True)
        if num_metrics == 1: axes = [axes] # Ensure axes is iterable

        for i, metric in enumerate(metrics):
            if metric not in well_data:
                print(f"Metric '{metric}' not found for well '{well_name}'. Available: {list(well_data.keys())}")
                axes[i].set_title(f"Metric '{metric}' not available")
                axes[i].text(0.5, 0.5, "Data not available", ha='center', va='center')
                continue

            metric_data = well_data[metric][1:] # Exclude initial values
            axes[i].plot(time_data, metric_data, marker='o', linestyle='-')
            axes[i].set_ylabel(metric.replace('_', ' ').title())
            axes[i].set_title(f"{metric.replace('_', ' ').title()} for Well {well_name}")
            axes[i].grid(True)

        axes[-1].set_xlabel("Time")
        fig.tight_layout()
        if file_path:
            plt.savefig(file_path)
            print(f"Well results plot saved to {file_path}")
        else:
            plt.show()

    def plot_field_results(self, metrics: list[str] = ['oil_rate'], file_path=None):
        """Plots overall field simulation results (e.g., total field production)."""
        if not self.simulation_results or 'summary' not in self.simulation_results:
            print("No simulation summary results available. Run simulation first.")
            return

        summary_df = self.simulation_results['summary']
        time_data = summary_df['Time']

        plt.figure(figsize=(12, 6))
        for metric in metrics:
            total_metric_col = f"Field_Total_{metric}"
            summary_df[total_metric_col] = 0

            # Sum metric across all relevant wells
            for well in self.wells:
                col_name = f"{well['name']}_{metric}"
                if col_name in summary_df.columns and well['type'] == 'producer': # Example: sum only producer oil_rates
                     summary_df[total_metric_col] += summary_df[col_name].fillna(0)

            if summary_df[total_metric_col].sum() > 0 : # Only plot if there's data
                plt.plot(time_data, summary_df[total_metric_col], label=f"Total Field {metric.replace('_',' ').title()}", marker='.')
            else:
                print(f"No data to plot for total field {metric}.")


        plt.xlabel("Time")
        plt.ylabel("Total Rate / Value")
        plt.title("Field Production/Injection Summary")
        plt.legend()
        plt.grid(True)
        if file_path:
            plt.savefig(file_path)
            print(f"Field results plot saved to {file_path}")
        else:
            plt.show()

    # --- Sensitivity Analysis (Conceptual) ---
    def run_sensitivity_analysis(self, parameter_path: str, values: list, base_case_results=None):
        """
        Performs sensitivity analysis on a given parameter (conceptual).
        parameter_path: string like "properties.porosity.scale_factor" or "wells.WellA.completions.0.bhp_limit"
        values: list of values to test for the parameter.
        base_case_results: results from a base case run (optional, for comparison).

        This is highly conceptual. A real implementation would need robust ways to modify
        parameters and re-run simulations.
        """
        print(f"\n--- Running Sensitivity Analysis on '{parameter_path}' with values {values} ---")
        sensitivity_summary = {}

        # Store original state (very simplified)
        original_value = None
        # This is a very naive way to access/modify nested parameters. A proper utility would be needed.
        # For example: getattr_nested, setattr_nested
        obj_to_modify = self
        param_parts = parameter_path.split('.')

        try:
            for i, part in enumerate(param_parts[:-1]):
                if isinstance(obj_to_modify, dict) and part in obj_to_modify:
                    obj_to_modify = obj_to_modify[part]
                elif isinstance(obj_to_modify, list) and part.isdigit() and int(part) < len(obj_to_modify):
                    obj_to_modify = obj_to_modify[int(part)]
                elif hasattr(obj_to_modify, part):
                    obj_to_modify = getattr(obj_to_modify, part)
                else:
                    raise ValueError(f"Cannot find path '{'.'.join(param_parts[:i+1])}' in simulator structure.")

            last_part = param_parts[-1]
            if isinstance(obj_to_modify, dict): original_value = obj_to_modify.get(last_part)
            elif hasattr(obj_to_modify, last_part): original_value = getattr(obj_to_modify, last_part)
            else: raise ValueError(f"Cannot get original value for '{last_part}' in '{type(obj_to_modify)}'")
        except Exception as e:
            print(f"Error accessing original parameter for sensitivity: {e}")
            return None


        for val in values:
            print(f"  Testing value: {val} for {parameter_path}")
            # Modify parameter (super simplified)
            try:
                if isinstance(obj_to_modify, dict): obj_to_modify[last_part] = val
                else: setattr(obj_to_modify, last_part, val)

                # Re-run simulation (using same time steps as a previous run, if any)
                # This assumes a previous run's time steps are implicitly available or defined.
                # For this example, let's assume a fixed set of steps.
                sim_time_steps = [10, 10, 10, 10, 10] # Placeholder if no prior run
                if self.simulation_results and 'time' in self.simulation_results and len(self.simulation_results['time']) > 1:
                    sim_time_steps = np.diff(self.simulation_results['time']).tolist()

                current_run_results = self.run_simulation(end_time=sum(sim_time_steps), time_steps=sim_time_steps)

                # Extract a key metric (e.g., total oil production at end time for a specific well or field)
                # This is highly dependent on what 'metric' means in the original request.
                # Let's assume a metric: cumulative oil from first producer at last time step.
                key_metric_value = None
                if current_run_results and 'summary' in current_run_results and not current_run_results['summary'].empty:
                    first_producer = next((w['name'] for w in self.wells if w['type'] == 'producer'), None)
                    if first_producer:
                        oil_col = f"{first_producer}_oil_rate"
                        if oil_col in current_run_results['summary']:
                             # For simplicity, let's use final oil rate as metric
                            key_metric_value = current_run_results['summary'][oil_col].iloc[-1]
                sensitivity_summary[val] = key_metric_value
                print(f"    -> Resulting metric value: {key_metric_value}")

            except Exception as e:
                print(f"    Error during sensitivity run with value {val}: {e}")
                sensitivity_summary[val] = None
            finally:
                # Restore original parameter value (important!)
                if original_value is not None:
                    if isinstance(obj_to_modify, dict): obj_to_modify[last_part] = original_value
                    else: setattr(obj_to_modify, last_part, original_value)

        print("--- Sensitivity Analysis Complete ---")
        return sensitivity_summary

    def plot_sensitivity_results(self, sensitivity_data: dict, parameter_name: str, metric_name: str, file_path=None):
        """Visualizes sensitivity analysis results (e.g., tornado plot - simplified here)."""
        if not sensitivity_data:
            print("No sensitivity data to plot.")
            return

        param_values = list(sensitivity_data.keys())
        metric_values = [sensitivity_data[pv] if sensitivity_data[pv] is not None else 0 for pv in param_values] # Handle None

        plt.figure(figsize=(10, 6))
        plt.plot(param_values, metric_values, marker='o', linestyle='-')
        plt.xlabel(parameter_name)
        plt.ylabel(metric_name)
        plt.title(f"Sensitivity of {metric_name} to {parameter_name}")
        plt.grid(True)
        if file_path:
            plt.savefig(file_path)
            print(f"Sensitivity plot saved to {file_path}")
        else:
            plt.show()

# Example Usage:
if __name__ == '__main__':
    sim = ReservoirSimulator(name="MyFieldSim_v1")

    # 1. Create Grid
    sim.create_structured_grid(nx=10, ny=10, nz=3, dx=100.0, dy=100.0, dz=50.0)

    # 2. Add Properties
    porosity_data = np.full((10, 10, 3), 0.2) # Uniform porosity
    porosity_data[0:5, :, 0] = 0.25 # Higher porosity in one layer region
    sim.add_property('porosity', porosity_data)

    perm_data = np.full((10, 10, 3), 100.0) # Uniform permeability in mD
    perm_data[:, :, 1] = 50.0 # Lower perm layer
    sim.add_property('permeability_mD', perm_data)

    # Plot property slice
    sim.plot_property_slice('porosity', slice_dim='z', slice_index=0, file_path="porosity_z0.png")
    sim.plot_property_slice('permeability_mD', slice_dim='y', slice_index=5, file_path="perm_y5.png")


    # 3. Add Wells
    # Producer P1
    p1_traj = [(i, 5, 1) for i in range(3, 7)] # Horizontal section in layer k=1, j=5
    p1_comps = [{'ijk': (i, 5, 1), 'type': 'producer', 'bhp_limit': 1500} for i in range(3,7)]
    sim.add_well("P1", trajectory=p1_traj, completions=p1_comps)

    # Injector I1
    i1_traj = [(0,0,k) for k in range(sim.grid['nz'])] # Vertical well in corner
    i1_comps = [{'ijk': (0,0,k), 'type': 'injector', 'rate_target': 500} for k in range(sim.grid['nz'])]
    sim.add_well("I1", trajectory=i1_traj, completions=i1_comps)

    # 4. Run Simulation
    time_steps_days = [30] * 12 # Simulate for 1 year with monthly steps
    results = sim.run_simulation(end_time=sum(time_steps_days), time_steps=time_steps_days)

    if results and 'summary' in results:
        print("\nSimulation Summary DataFrame Head:")
        print(results['summary'].head())

    # 5. Plot Results
    sim.plot_well_results("P1", metrics=['oil_rate', 'gas_rate', 'water_rate', 'bhp'], file_path="P1_results.png")
    sim.plot_well_results("I1", metrics=['injection_rate', 'bhp'], file_path="I1_results.png")
    sim.plot_field_results(metrics=['oil_rate'], file_path="field_total_oil.png") # Plot total field oil production

    # 6. (Conceptual) 3D Plot
    sim.plot_3d_model()

    # 7. Convert well type (example)
    sim.convert_well_type("P1", "shut-in")
    print(f"P1 status after conversion: {sim.wells[0]['type']}")
    # Re-run simulation to see effect (optional, would require re-running sim.run_simulation)
    print("\nRe-running simulation after shutting in P1...")
    results_after_shut_in = sim.run_simulation(end_time=sum(time_steps_days), time_steps=time_steps_days)
    sim.plot_well_results("P1", metrics=['oil_rate'], file_path="P1_results_after_shutin.png")
    sim.plot_field_results(metrics=['oil_rate'], file_path="field_total_oil_after_shutin.png")


    # 8. Sensitivity Analysis (Conceptual)
    # Restore P1 to producer for this test
    sim.convert_well_type("P1", "producer")

    # Example: Sensitivity to P1's BHP limit
    # Note: This path is illustrative. The run_sensitivity_analysis method has a basic way to set this.
    # A robust solution would involve a proper way to identify and modify specific well completion parameters.
    # Let's assume we want to vary the 'bhp_limit' of the first completion of well 'P1'.
    # The path needs to correctly point to where this is stored.
    # Our current structure: self.wells is a list of dicts. P1 is wells[0]. Completions is wells[0]['completions'][0]['bhp_limit']
    # This is a bit fragile if well order changes or structure is different.
    # For this example, let's assume P1 is the first well.
    if sim.wells and sim.wells[0]['name'] == 'P1' and sim.wells[0]['completions']:
        # This path is specific to the current structure and P1 being the first well.
        # A more general approach would be needed for arbitrary well names / completion indices.
        # For demonstration, let's simplify the parameter path for this example.
        # The run_sensitivity_analysis has a naive setter; let's use a more direct modification for this test case.

        original_bhp_limit = sim.wells[0]['completions'][0]['bhp_limit']
        bhp_values_to_test = [original_bhp_limit - 200, original_bhp_limit, original_bhp_limit + 200]
        sensitivity_output = {}

        print(f"\n--- Running Manual Sensitivity on P1 BHP Limit ---")
        for bhp_val in bhp_values_to_test:
            print(f"  Testing P1 BHP Limit: {bhp_val}")
            sim.wells[0]['completions'][0]['bhp_limit'] = bhp_val # Directly modify

            # Rerun simulation
            current_run_results = sim.run_simulation(end_time=sum(time_steps_days), time_steps=time_steps_days)

            metric_val = None
            if current_run_results and 'summary' in current_run_results and not current_run_results['summary'].empty:
                if "P1_oil_rate" in current_run_results['summary'].columns:
                    metric_val = current_run_results['summary']["P1_oil_rate"].sum() # Cumulative oil for P1
            sensitivity_output[bhp_val] = metric_val
            print(f"    -> P1 Cumulative Oil: {metric_val}")

        # Restore original
        sim.wells[0]['completions'][0]['bhp_limit'] = original_bhp_limit

        sim.plot_sensitivity_results(sensitivity_output, "P1 BHP Limit", "P1 Cumulative Oil", file_path="sensitivity_p1_bhp.png")
    else:
        print("Could not run P1 BHP sensitivity example as P1 or its completions are not set up as expected.")


    # Clean up dummy image files
    import os
    for f in ["porosity_z0.png", "perm_y5.png", "P1_results.png", "I1_results.png",
              "field_total_oil.png", "P1_results_after_shutin.png",
              "field_total_oil_after_shutin.png", "sensitivity_p1_bhp.png"]:
        if os.path.exists(f):
            os.remove(f)

```
