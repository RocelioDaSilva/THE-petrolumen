from typing import List, Tuple, Dict, Any
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ReservoirSimulator:
    def __init__(self):
        self.grid: Dict[str, Any] = {} # For 1D: nx, dx, area (cross-sectional)
        self.fluid_properties: Dict[str, float] = {} # viscosity, compressibility, formation_volume_factor
        self.rock_properties: Dict[str, Any] = {} # permeability (np.array for heterogeneity), porosity (np.array)
        self.initial_conditions: Dict[str, Any] = {} # initial_pressure (np.array)
        self.boundary_conditions: Dict[str, Any] = {} # type_left, value_left, type_right, value_right

        self.wells: List[Dict[str, Any]] = [] # List of wells, each a dict
        self.simulation_results: Dict[str, Any] = {}
        self.time_steps: Optional[np.ndarray] = None
        self.pressure_solutions: List[np.ndarray] = []
        self.well_rates: Dict[str, List[float]] = {}


    def setup_1d_grid(self, nx: int, dx: float, area: float = 100.0): # Area in ft^2 for field units
        """Defines a 1D grid."""
        if not (isinstance(nx, int) and nx > 0):
            raise ValueError("Grid dimension nx must be a positive integer.")
        if not (isinstance(dx, (float, int)) and dx > 0):
            raise ValueError("Grid spacing dx must be a positive number.")
        if not (isinstance(area, (float, int)) and area > 0):
            raise ValueError("Cross-sectional area must be a positive number.")

        self.grid = {'nx': nx, 'dx': dx, 'area': area}
        # Initialize rock properties with default uniform values if not set later
        self.rock_properties['permeability'] = np.full(nx, 100.0) # mD
        self.rock_properties['porosity'] = np.full(nx, 0.2)    # fraction
        self.initial_conditions['initial_pressure'] = np.full(nx, 3000.0) # psi
        logger.info(f"Created 1D grid: nx={nx}, dx={dx} ft, area={area} ft^2")

    def set_fluid_properties(self, viscosity: float, compressibility: float, fvf: float):
        """Sets single-phase fluid properties."""
        self.fluid_properties = {
            'viscosity': viscosity,         # cP
            'compressibility': compressibility, # 1/psi
            'fvf': fvf                      # rb/stb (reservoir barrel / stock tank barrel)
        }
        logger.info(f"Set fluid properties: mu={viscosity} cP, ct={compressibility} 1/psi, Bo={fvf} rb/stb")

    def set_rock_properties(self, permeability: Any, porosity: Any):
        """Sets rock properties. Can be scalar (for homogeneous) or array (for heterogeneous)."""
        if not self.grid:
            raise ValueError("Grid must be created before setting rock properties.")
        nx = self.grid['nx']

        if isinstance(permeability, (float, int)):
            self.rock_properties['permeability'] = np.full(nx, float(permeability))
        elif isinstance(permeability, (list, np.ndarray)):
            if len(permeability) != nx:
                raise ValueError(f"Permeability array size ({len(permeability)}) must match grid size nx ({nx}).")
            self.rock_properties['permeability'] = np.array(permeability, dtype=float)
        else:
            raise TypeError("Permeability must be a scalar or a list/numpy array.")

        if isinstance(porosity, (float, int)):
            self.rock_properties['porosity'] = np.full(nx, float(porosity))
        elif isinstance(porosity, (list, np.ndarray)):
            if len(porosity) != nx:
                raise ValueError(f"Porosity array size ({len(porosity)}) must match grid size nx ({nx}).")
            self.rock_properties['porosity'] = np.array(porosity, dtype=float)
        else:
            raise TypeError("Porosity must be a scalar or a list/numpy array.")
        logger.info("Set rock properties (permeability, porosity).")


    def set_initial_conditions(self, initial_pressure: Any):
        if not self.grid:
            raise ValueError("Grid must be created before setting initial conditions.")
        nx = self.grid['nx']
        if isinstance(initial_pressure, (float, int)):
            self.initial_conditions['initial_pressure'] = np.full(nx, float(initial_pressure))
        elif isinstance(initial_pressure, (list, np.ndarray)):
            if len(initial_pressure) != nx:
                raise ValueError(f"Initial pressure array size ({len(initial_pressure)}) must match grid size nx ({nx}).")
            self.initial_conditions['initial_pressure'] = np.array(initial_pressure, dtype=float)
        else:
            raise TypeError("Initial pressure must be a scalar or a list/numpy array.")
        logger.info("Set initial pressure conditions.")

    def set_boundary_conditions(self, type_left: str, value_left: float, type_right: str, value_right: float):
        """Sets boundary conditions for 1D model. types: 'pressure' or 'flux'."""
        if type_left not in ['pressure', 'flux'] or type_right not in ['pressure', 'flux']:
            raise ValueError("Boundary condition types must be 'pressure' or 'flux'.")
        self.boundary_conditions = {
            'type_left': type_left, 'value_left': value_left,
            'type_right': type_right, 'value_right': value_right
        }
        logger.info(f"Set boundary conditions: Left=({type_left}, {value_left}), Right=({type_right}, {value_right})")


    def add_well(self, name: str, location_index: int, well_type: str = "producer",
                 control_type: str = "bhp", control_value: float = 2000.0,
                 rw: float = 0.25, skin: float = 0.0):
        """Defines a well for the 1D model."""
        if not self.grid or location_index < 0 or location_index >= self.grid['nx']:
            raise ValueError(f"Invalid well location_index {location_index} for grid size {self.grid.get('nx')}.")
        if well_type not in ["producer", "injector"]:
            raise ValueError("Well type must be 'producer' or 'injector'.")
        if control_type not in ["bhp", "rate"]:
            raise ValueError("Well control type must be 'bhp' (bottom-hole pressure) or 'rate'.")

        self.wells.append({
            'name': name,
            'location_index': location_index, # Grid block index
            'type': well_type,
            'control_type': control_type,
            'control_value': control_value, # BHP (psi) or rate (STB/day, negative for producer)
            'rw': rw, # wellbore radius (ft)
            'skin': skin # skin factor (dimensionless)
        })
        logger.info(f"Added well '{name}' at index {location_index}, type '{well_type}', control: {control_type}={control_value}")


    def convert_well_type(self, name: str, new_type: str) -> None: # Keep for compatibility if needed
        """Changes a well's type (e.g., from producer to injector)."""
        if name not in self.wells:
            raise ValueError(f"Well '{name}' not found.")

        # Find the well and update its type
        found = False
        for well in self.wells:
            if well['name'] == name:
                old_type = well['type']
                well['type'] = new_type
                logger.info(f"Converted well '{name}' from type '{old_type}' to '{new_type}'.")
                found = True
                break
        if not found:
            raise ValueError(f"Well '{name}' not found for type conversion.")


    def run_simulation(self, end_time: float, dt: float) -> None:
        """
        Executes a simplified 1D single-phase finite difference reservoir simulation.
        Solves for pressure implicitly. Calculates well rates explicitly.
        Units: Field units (psi, ft, day, mD, cP, STB, etc.)
        """
        if not self.grid or not self.fluid_properties or not self.rock_properties or not self.initial_conditions:
            raise ValueError("Grid, fluid, rock properties, and initial conditions must be set before running simulation.")
        if end_time <= 0 or dt <= 0:
            raise ValueError("End time and time step (dt) must be positive.")

        nx = self.grid['nx']
        dx = self.grid['dx']
        area = self.grid['area'] # Cross-sectional area (ft^2)

        # Rock and Fluid Properties (assuming homogeneous for simplicity in matrix construction, can be extended)
        # For heterogeneous, transmissibilities T would need to be calculated for each interface.
        # Here, we'll use average or first block's properties for constructing a simplified T.
        k = self.rock_properties['permeability'] # mD, potentially an array
        phi = self.rock_properties['porosity']   # fraction, potentially an array
        mu = self.fluid_properties['viscosity']   # cP
        ct = self.fluid_properties['compressibility'] # 1/psi
        B = self.fluid_properties['fvf']          # rb/stb

        # Conversion factor for Darcy units: k (mD) * Area (ft^2) / (mu (cP) * B (rb/stb) * dx (ft))
        # Resulting transmissibility in STB/day/psi
        # 0.001127 for k in mD, A in ft^2, mu in cp, L in ft, for flow in bbl/day
        # For STB/day, need B in denominator.
        # T = (0.001127 * k_avg * area) / (mu * B_avg * dx)
        # For this simplified version, let's assume k is average if array, or scalar
        k_avg = np.mean(k) if isinstance(k, np.ndarray) else k
        phi_avg = np.mean(phi) if isinstance(phi, np.ndarray) else phi

        # Transmissibility coefficient (simplified, assumes homogeneous between blocks for T)
        # T_interface = (0.001127 * 2 * k1 * k2 * area) / ((k1 + k2) * mu * B * dx) for harmonic avg of k
        # For simplicity, using arithmetic average for k in T for now, or just k_avg
        T_const = (0.001127 * k_avg * area) / (mu * B * dx) # STB/day/psi

        # Accumulation term constant: (phi * ct * Volume_block) / dt
        # Volume_block = dx * area (ft^3)
        # dt is in days. ct is in 1/psi. phi is fraction.
        # Result needs to be in STB/psi for consistency if T is STB/day/psi and Q is STB/day
        # (phi * ct * dx * area) / (B * dt)  -- units: (frac * 1/psi * ft^3) / (rb/stb * day) -> (ft^3 / psi) / (rb/stb * day)
        # Need conversion for ft^3 to rb (reservoir barrels): 1 bbl = 5.615 ft^3
        # Accum_const = (phi_avg * ct * dx * area) / (B * dt * 5.615) # STB/day/psi

        # Simpler accumulation term for matrix construction (will be multiplied by P)
        # (phi * ct * Vp) / (B * dt) where Vp = pore volume = dx * area * phi
        # C = (phi * ct * dx * area) / (B * dt * 5.615)
        C_const = (phi_avg * ct * dx * area) / (B * dt * 5.615) # STB/day/psi

        P_old = np.copy(self.initial_conditions['initial_pressure'])
        self.pressure_solutions = [np.copy(P_old)]
        self.time_steps = np.arange(0, end_time + dt, dt)

        for well in self.wells: # Initialize rate storage
            self.well_rates[well['name']] = [0.0] # Rate at time 0

        logger.info(f"Starting 1D simulation: nx={nx}, end_time={end_time}, dt={dt}")
        logger.info(f"T_const={T_const:.4e}, C_const={C_const:.4e}")


        for t_idx, current_time in enumerate(self.time_steps[1:], 1): # Start from first time step
            A = np.zeros((nx, nx))
            Q = np.zeros(nx)

            # Fill matrix A and vector Q
            for i in range(nx):
                # Accumulation term
                A[i, i] = C_const
                Q[i] = C_const * P_old[i]

                # Left boundary / connection
                if i == 0:
                    if self.boundary_conditions.get('type_left') == 'pressure':
                        P_left = self.boundary_conditions['value_left']
                        A[i, i] += T_const
                        Q[i] += T_const * P_left
                    elif self.boundary_conditions.get('type_left') == 'flux':
                        # Flux into block 0 (positive if into domain)
                        # Convention: q_boundary * area / (B * 5.615) to get STB/day
                        # This is a source term, added to Q
                        # For simplicity, assume flux is given in STB/day directly
                        Q[i] += self.boundary_conditions['value_left']
                    # else no flow implicitly (A[i,i-1] is zero)
                else: # Internal block connection to the left
                    A[i, i] += T_const
                    A[i, i-1] = -T_const

                # Right boundary / connection
                if i == nx - 1:
                    if self.boundary_conditions.get('type_right') == 'pressure':
                        P_right = self.boundary_conditions['value_right']
                        A[i, i] += T_const
                        Q[i] += T_const * P_right
                    elif self.boundary_conditions.get('type_right') == 'flux':
                        # Flux out of block nx-1 (positive if out of domain, so subtract from Q)
                        Q[i] -= self.boundary_conditions['value_right']
                    # else no flow implicitly
                else: # Internal block connection to the right
                    A[i, i] += T_const
                    A[i, i+1] = -T_const

            # Add well terms (simplified Peaceman for BHP control)
            for well in self.wells:
                idx = well['location_index']
                if well['control_type'] == 'bhp':
                    P_bh = well['control_value']
                    # Peaceman well index for 1D cartesian
                    # WI = (0.001127 * 2 * np.pi * k_avg * (dx*area/dx)) / (mu * B * (np.log(0.2 * dx / well['rw']) + well['skin']))
                    # Simplified: WI = T_const_well_block * factor
                    # For a simple 1D block, effective permeability thickness product is k*h = k_avg * (area/dx) if dx is length
                    # Or k*A if A is cross-section and flow is along dx.
                    # Let's use a simplified WI based on block transmissibility for now.
                    # WI_approx = T_const * some_factor. For this example, let's assume WI is given or ~T_const.
                    # This is a highly simplified well model.
                    # A more common form: q = WI * (P_block - P_bh)
                    # WI = 0.00708 * k * h / (mu * B * (ln(re/rw) + S)) ; re = 0.14 * sqrt(dx^2+dy^2) for square grid
                    # For 1D, re ~ 0.2*dx
                    k_well_block = k[idx] if isinstance(k, np.ndarray) else k_avg
                    h_equiv = dx # Using dx as thickness for 1D model, assuming flow along an implicit y or z
                                 # Or, if dx is the flow length, area is perpendicular.
                                 # Let's assume dx is length, area is cross-section.
                                 # Peaceman's re for a block of size dx: re = 0.2 * dx (approx)
                    WI = (0.00708 * k_well_block * area) / (mu * B * (np.log(0.2 * dx / well['rw']) + well['skin'])) # STB/day/psi

                    if well['type'] == 'producer':
                        A[idx, idx] += WI
                        Q[idx] += WI * P_bh
                    elif well['type'] == 'injector': # Injector with BHP control (injects if P_bh > P_block)
                        A[idx, idx] += WI
                        Q[idx] += WI * P_bh # q_inj = WI * (P_bh - P_block) -> source term is WI*P_bh

                elif well['control_type'] == 'rate': # Constant rate well
                    rate_val = well['control_value'] # STB/day (negative for producer, positive for injector)
                    if well['type'] == 'producer':
                        Q[idx] += rate_val # rate_val is negative, so it's a sink
                    elif well['type'] == 'injector':
                        Q[idx] += rate_val # rate_val is positive, so it's a source


            # Solve for new pressures P_new
            try:
                P_new = np.linalg.solve(A, Q)
            except np.linalg.LinAlgError:
                logger.error(f"Singular matrix at time {current_time}. Simulation failed.")
                # Store what we have and stop or handle error
                self.simulation_results['status'] = 'Failed: Singular matrix'
                return

            self.pressure_solutions.append(np.copy(P_new))
            P_old = P_new

            # Calculate well rates for this timestep (explicitly, after pressure solution)
            for well in self.wells:
                idx = well['location_index']
                P_block = P_new[idx]
                if well['control_type'] == 'bhp':
                    P_bh = well['control_value']
                    k_well_block = k[idx] if isinstance(k, np.ndarray) else k_avg
                    WI = (0.00708 * k_well_block * area) / (mu * B * (np.log(0.2 * dx / well['rw']) + well['skin']))

                    if well['type'] == 'producer':
                        rate_calc = WI * (P_block - P_bh)
                        self.well_rates[well['name']].append(max(0, rate_calc)) # Ensure non-negative production
                    elif well['type'] == 'injector':
                        rate_calc = WI * (P_bh - P_block) # Injection rate
                        self.well_rates[well['name']].append(max(0, rate_calc)) # Ensure non-negative injection

                elif well['control_type'] == 'rate':
                     self.well_rates[well['name']].append(well['control_value'])


        self.simulation_results['status'] = 'Completed'
        self.simulation_results['pressures_vs_time'] = self.pressure_solutions
        self.simulation_results['well_rates_vs_time'] = self.well_rates
        self.simulation_results['time_array'] = self.time_steps
        logger.info("1D Simulation run completed.")


    def plot_property_slice(self, property_name: str, slice_axis: str = 'z', slice_index: int = 0) -> str:
        """Visualizes a slice of a grid property (less relevant for 1D)."""
        if property_name not in self.rock_properties and property_name not in self.initial_conditions:
            return f"Property '{property_name}' not found."
        if not self.grid:
            return "Grid not defined."
        if self.grid.get('nx',0) > 0 and self.grid.get('ny',0) == 0 : # Indicates 1D
             prop_data = self.rock_properties.get(property_name) or self.initial_conditions.get(property_name)
             if prop_data is not None:
                 # Placeholder for 1D plot (e.g. property vs. block index)
                 # import matplotlib.pyplot as plt
                 # plt.plot(prop_data)
                 # plt.title(f'{property_name}')
                 # plt.xlabel('Block Index'); plt.ylabel(property_name)
                 # plt.show()
                 return f"1D Plot of property '{property_name}' would be generated here."
             else:
                 return f"Data for property '{property_name}' not found."

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
        well_exists = any(w['name'] == well_name for w in self.wells)
        if not well_exists:
            return f"Well '{well_name}' not found."

        if not self.simulation_results or \
           'time_array' not in self.simulation_results or \
           well_name not in self.simulation_results.get('well_rates_vs_time', {}):
            return f"No simulation results found for well '{well_name}'."

        # Placeholder for plotting (e.g., Plotly)
        # Example:
        # time_array = self.simulation_results['time_array']
        # rates = self.simulation_results['well_rates_vs_time'][well_name]
        # import matplotlib.pyplot as plt
        # plt.plot(time_array, rates); plt.title(f"Results for Well {well_name}"); plt.xlabel("Time (days)"); plt.ylabel("Rate (STB/day or Mcf/day)")
        # plt.show()
        logger.info(f"Plotting results for well '{well_name}'.")
        return f"Plot of simulation rates for well '{well_name}' would be generated here."

    def plot_field_results(self) -> str:
        """Plots overall field simulation results."""
        if not self.simulation_results or 'time_array' not in self.simulation_results or 'well_rates_vs_time' not in self.simulation_results:
            return "No simulation results to plot for the field."

        time_array = self.simulation_results['time_array']
        total_production_rate = np.zeros_like(time_array)
        total_injection_rate = np.zeros_like(time_array)

        well_rates_data = self.simulation_results['well_rates_vs_time']

        for well_info in self.wells:
            well_name = well_info['name']
            if well_name in well_rates_data:
                rates = np.array(well_rates_data[well_name])
                # Ensure rates array matches time_array length (it should if generated correctly)
                if len(rates) == len(time_array):
                    if well_info['type'] == 'producer':
                        total_production_rate += rates # Assuming producer rates are positive STB/day
                    elif well_info['type'] == 'injector':
                        total_injection_rate += rates # Assuming injector rates are positive STB/day
                else:
                    logger.warning(f"Rate data length mismatch for well {well_name}. Skipping for field plot.")

        # Placeholder for plotting
        # import matplotlib.pyplot as plt
        # fig, ax1 = plt.subplots()
        # color = 'tab:red'
        # ax1.set_xlabel('Time (days)')
        # ax1.set_ylabel('Total Production Rate (STB/day)', color=color)
        # ax1.plot(time_array, total_production_rate, color=color)
        # ax1.tick_params(axis='y', labelcolor=color)
        #
        # if np.any(total_injection_rate > 0): # Only plot injection if there is any
        #     ax2 = ax1.twinx()
        #     color = 'tab:blue'
        #     ax2.set_ylabel('Total Injection Rate (STB/day)', color=color)
        #     ax2.plot(time_array, total_injection_rate, color=color, linestyle='--')
        #     ax2.tick_params(axis='y', labelcolor=color)
        #
        # fig.tight_layout()
        # plt.title('Field Production and Injection Rates')
        # plt.show()

        logger.info("Plotting field results (total production/injection).")
        return "Plot of overall field production and injection rates would be generated here."

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
