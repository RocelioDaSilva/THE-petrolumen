"""
Thermal Modeling Module

This module provides advanced thermal modeling capabilities for reservoir simulation,
including heat transfer, temperature-dependent fluid properties, and thermal
recovery methods.
"""

import numpy as np
from typing import Dict, List, Tuple
from scipy.sparse import csr_matrix, lil_matrix
from scipy.sparse.linalg import spsolve


class ThermalModel:
    def __init__(
        self, grid_dims: Tuple[int, int, int], properties: Dict[str, np.ndarray]
    ):
        """
        Initialize thermal model.

        Args:
            grid_dims: Grid dimensions (nx, ny, nz)
            properties: Dictionary of thermal properties
        """
        self.nx, self.ny, self.nz = grid_dims
        self.n_cells = self.nx * self.ny * self.nz
        self.properties = properties

        # Initialize temperature field
        self.temperature = np.ones(self.n_cells) * properties.get(
            "initial_temperature", 180.0
        )  # °F
        self.temperature_prev = self.temperature.copy()

        # Initialize thermal properties
        self.rock_heat_capacity = properties.get(
            "rock_heat_capacity", np.ones(self.n_cells) * 0.2
        )  # Btu/lb-°F
        self.rock_thermal_conductivity = properties.get(
            "rock_thermal_conductivity", np.ones(self.n_cells) * 1.0
        )  # Btu/ft-hr-°F
        self.rock_density = properties.get(
            "rock_density", np.ones(self.n_cells) * 165.0
        )  # lb/ft³

        # Fluid thermal properties
        self.fluid_heat_capacity = {
            "oil": properties.get(
                "oil_heat_capacity", np.ones(self.n_cells) * 0.5
            ),  # Btu/lb-°F
            "water": properties.get(
                "water_heat_capacity", np.ones(self.n_cells) * 1.0
            ),  # Btu/lb-°F
            "gas": properties.get(
                "gas_heat_capacity", np.ones(self.n_cells) * 0.5
            ),  # Btu/lb-°F
        }

        self.fluid_thermal_conductivity = {
            "oil": properties.get(
                "oil_thermal_conductivity", np.ones(self.n_cells) * 0.08
            ),  # Btu/ft-hr-°F
            "water": properties.get(
                "water_thermal_conductivity", np.ones(self.n_cells) * 0.4
            ),  # Btu/ft-hr-°F
            "gas": properties.get(
                "gas_thermal_conductivity", np.ones(self.n_cells) * 0.02
            ),  # Btu/ft-hr-°F
        }

        # Initialize boundary conditions
        self.boundary_conditions = {
            "type": "constant_temperature",  # 'constant_temperature',
            # 'constant_heat_flux', 'convective'
            "values": {
                "top": 180.0,  # °F
                "bottom": 180.0,  # °F
                "left": 180.0,  # °F
                "right": 180.0,  # °F
                "front": 180.0,  # °F
                "back": 180.0,  # °F
            },
        }

        # Initialize thermal recovery method
        self.thermal_recovery_method = None  # 'steam_flooding',
        # 'cyclic_steam_stimulation', 'sagd', 'in_situ_combustion'
        self.thermal_recovery_params = {}

        # Temperature-dependent viscosity model parameters
        self.viscosity_model = {
            "oil": {
                "type": "exponential",  # 'exponential', 'andrade', 'custom'
                "reference_temperature": 180.0,  # °F
                "reference_viscosity": 10.0,  # cP
                "activation_energy": 10000.0,  # J/mol
            },
            "water": {
                "type": "exponential",
                "reference_temperature": 180.0,  # °F
                "reference_viscosity": 0.5,  # cP
                "activation_energy": 5000.0,  # J/mol
            },
        }

    def set_initial_temperature(
        self, temperature_gradient: float, depth: np.ndarray, surface_temp: float = 60.0
    ):
        """
        Set initial temperature based on depth and temperature gradient.

        Args:
            temperature_gradient: Temperature gradient (°F/ft)
            depth: Depth array for each cell (ft)
            surface_temp: Surface temperature (°F)
        """
        self.temperature = surface_temp + depth * temperature_gradient
        self.temperature_prev = self.temperature.copy()

    def enable_thermal_recovery(self, method: str, params: Dict):
        """
        Enable thermal recovery method.

        Args:
            method: Thermal recovery method
            params: Parameters for the method
        """
        self.thermal_recovery_method = method
        self.thermal_recovery_params = params

        if method == "steam_flooding":
            # Initialize steam flooding parameters
            self.thermal_recovery_params.setdefault("steam_quality", 0.8)
            self.thermal_recovery_params.setdefault("steam_temperature", 400.0)  # °F
            self.thermal_recovery_params.setdefault(
                "steam_injection_rate", 1000.0
            )  # bbl/day

        elif method == "cyclic_steam_stimulation":
            # Initialize CSS parameters
            self.thermal_recovery_params.setdefault("steam_quality", 0.8)
            self.thermal_recovery_params.setdefault("steam_temperature", 400.0)  # °F
            self.thermal_recovery_params.setdefault("injection_period", 10.0)  # days
            self.thermal_recovery_params.setdefault("soaking_period", 5.0)  # days
            self.thermal_recovery_params.setdefault("production_period", 30.0)  # days

        elif method == "sagd":
            # Initialize SAGD parameters
            self.thermal_recovery_params.setdefault("steam_quality", 0.8)
            self.thermal_recovery_params.setdefault("steam_temperature", 400.0)  # °F
            self.thermal_recovery_params.setdefault("well_pair_spacing", 5.0)  # m
            self.thermal_recovery_params.setdefault("vertical_spacing", 5.0)  # m

        elif method == "in_situ_combustion":
            # Initialize in-situ combustion parameters
            self.thermal_recovery_params.setdefault(
                "air_injection_rate", 1000.0  # scf/day
            )
            self.thermal_recovery_params.setdefault("ignition_temperature", 600.0)  # °F
            self.thermal_recovery_params.setdefault("fuel_content", 0.1)  # kg/kg

    def solve_heat_equation(
        self,
        dt: float,
        saturation: Dict[str, np.ndarray],
        velocity: Dict[str, np.ndarray],
        grid_geometry: Dict,
    ):
        """
        Solve heat equation for temperature field.

        Args:
            dt: Time step (days)
            saturation: Dictionary of phase saturations
            velocity: Dictionary of phase velocities
            grid_geometry: Grid geometry information
        """
        # Save previous temperature
        self.temperature_prev = self.temperature.copy()

        # Assemble heat equation system
        A_matrix, b_vector = self._assemble_heat_equation(
            dt, saturation, velocity, grid_geometry
        )

        # Apply boundary conditions
        A_matrix, b_vector = self._apply_thermal_boundary_conditions(
            A_matrix, b_vector, grid_geometry
        )

        # Solve for temperature
        try:
            self.temperature = spsolve(A_matrix, b_vector)
        except Exception as e:
            print(
                f"Error solving heat equation: {e}. Matrix A might be singular or "
                "ill-conditioned."
            )
            # Fallback or error handling: e.g., keep previous temperature or use a
            # more robust solver. For now, we'll just log the error and potentially
            # not update temperature this step
            self.temperature = (
                self.temperature_prev.copy()
            )  # Revert to previous if solve fails

        # Apply thermal recovery effects
        if self.thermal_recovery_method:
            self._apply_thermal_recovery_effects(dt, saturation)

    def _assemble_heat_equation(
        self,
        dt: float,
        saturation: Dict[str, np.ndarray],
        velocity: Dict[str, np.ndarray],
        grid_geometry: Dict,
    ):
        """
        Assemble heat equation system.

        Args:
            dt: Time step (days)
            saturation: Dictionary of phase saturations
            velocity: Dictionary of phase velocities
            grid_geometry: Grid geometry information

        Returns:
            Tuple of (system_matrix, right_hand_side)
        """
        dt_hours = dt * 24.0
        if dt_hours == 0:
            dt_hours = 1e-6  # Avoid division by zero

        A = lil_matrix((self.n_cells, self.n_cells))
        b = np.zeros(self.n_cells)

        dx_val = grid_geometry.get("dx", 1.0)
        dy_val = grid_geometry.get("dy", 1.0)
        dz_val = grid_geometry.get("dz", 1.0)

        # Ensure dx, dy, dz are arrays if grid is structured, or handle scalar if uniform
        dx_arr = (
            np.full(self.nx, dx_val) if isinstance(dx_val, (int, float)) else dx_val
        )
        dy_arr = (
            np.full(self.ny, dy_val) if isinstance(dy_val, (int, float)) else dy_val
        )
        dz_arr = (
            np.full(self.nz, dz_val) if isinstance(dz_val, (int, float)) else dz_val
        )

        cell_volume = np.zeros(self.n_cells)
        for i in range(self.nx):
            for j in range(self.ny):
                for k in range(self.nz):
                    idx = i + j * self.nx + k * self.nx * self.ny
                    cell_volume[idx] = dx_arr[i] * dy_arr[j] * dz_arr[k]

        effective_heat_capacity = np.zeros(self.n_cells)
        effective_thermal_conductivity = np.zeros(self.n_cells)

        porosity_arr = grid_geometry.get("porosity", np.ones(self.n_cells) * 0.2)

        for i in range(self.n_cells):
            porosity = porosity_arr[i]
            effective_heat_capacity[i] = (
                (1 - porosity) * self.rock_density[i] * self.rock_heat_capacity[i]
            )
            for phase in ["oil", "water", "gas"]:
                if phase in saturation and i < len(saturation[phase]):  # Check bounds
                    phase_density = 50.0  # Placeholder
                    effective_heat_capacity[i] += (
                        porosity
                        * saturation[phase][i]
                        * phase_density
                        * self.fluid_heat_capacity[phase][i]
                    )

            effective_thermal_conductivity[i] = (
                1 - porosity
            ) * self.rock_thermal_conductivity[i]
            for phase in ["oil", "water", "gas"]:
                if phase in saturation and i < len(saturation[phase]):  # Check bounds
                    effective_thermal_conductivity[i] += (
                        porosity
                        * saturation[phase][i]
                        * self.fluid_thermal_conductivity[phase][i]
                    )

        for i_idx in range(self.n_cells):  # Renamed loop variable
            # Diagonal term
            A[i_idx, i_idx] = (
                effective_heat_capacity[i_idx] * cell_volume[i_idx] / dt_hours
            )
            b[i_idx] = (
                effective_heat_capacity[i_idx]
                * cell_volume[i_idx]
                * self.temperature_prev[i_idx]
                / dt_hours
            )

            # Simplified 1D conduction terms (example for x-direction)
            current_x_idx = i_idx % self.nx
            if current_x_idx > 0:  # Left neighbor
                term = (
                    effective_thermal_conductivity[i_idx]
                    * cell_volume[i_idx]
                    / (dx_arr[current_x_idx] ** 2)
                )  # Use dx_arr
                A[i_idx, i_idx - 1] = -term
                A[i_idx, i_idx] += term
            if current_x_idx < self.nx - 1:  # Right neighbor
                term = (
                    effective_thermal_conductivity[i_idx]
                    * cell_volume[i_idx]
                    / (dx_arr[current_x_idx] ** 2)
                )  # Use dx_arr
                A[i_idx, i_idx + 1] = -term
                A[i_idx, i_idx] += term

            # Simplified 1D convection (example for x-direction)
            for phase in ["oil", "water", "gas"]:
                if (
                    phase in velocity
                    and phase in saturation
                    and i_idx < len(velocity[phase])
                    and i_idx < len(saturation[phase])
                ):
                    v_phase_i = velocity[phase][i_idx]
                    s_phase_i = saturation[phase][i_idx]
                    cp_phase_i = self.fluid_heat_capacity[phase][i_idx]

                    conv_term_base = (
                        s_phase_i
                        * cp_phase_i
                        * cell_volume[i_idx]
                        / dx_arr[current_x_idx]
                    )

                    if (
                        v_phase_i > 0 and current_x_idx > 0
                    ):  # Flow from left (i-1) to current (i)
                        A[i_idx, i_idx] += v_phase_i * conv_term_base
                        A[i_idx, i_idx - 1] -= v_phase_i * conv_term_base
                    elif (
                        v_phase_i < 0 and current_x_idx < self.nx - 1
                    ):  # Flow from right (i+1) to current (i)
                        A[i_idx, i_idx] -= (
                            v_phase_i * conv_term_base
                        )  # v_phase_i is negative
                        A[i_idx, i_idx + 1] += (
                            v_phase_i * conv_term_base
                        )  # v_phase_i is negative

        return A.tocsr(), b

    def _apply_thermal_boundary_conditions(
        self, A: csr_matrix, b: np.ndarray, grid_geometry: Dict
    ):
        """Apply thermal boundary conditions to the system."""
        # This is a placeholder for the full implementation
        return A, b

    def _apply_thermal_recovery_effects(
        self, dt: float, saturation: Dict[str, np.ndarray]
    ):
        """Apply effects of thermal recovery methods."""
        if self.thermal_recovery_method == "steam_flooding":
            self._apply_steam_flooding_effects(dt, saturation)
        elif self.thermal_recovery_method == "cyclic_steam_stimulation":
            self._apply_css_effects(dt, saturation)
        elif self.thermal_recovery_method == "sagd":
            self._apply_sagd_effects(dt, saturation)
        elif self.thermal_recovery_method == "in_situ_combustion":
            self._apply_isc_effects(dt, saturation)

    def _apply_steam_flooding_effects(
        self, dt: float, saturation: Dict[str, np.ndarray]
    ):
        """Apply steam flooding effects."""
        pass

    def _apply_css_effects(self, dt: float, saturation: Dict[str, np.ndarray]):
        """Apply cyclic steam stimulation effects."""
        pass

    def _apply_sagd_effects(self, dt: float, saturation: Dict[str, np.ndarray]):
        """Apply SAGD effects."""
        pass

    def _apply_isc_effects(self, dt: float, saturation: Dict[str, np.ndarray]):
        """Apply in-situ combustion effects."""
        pass

    def calculate_temperature_dependent_viscosity(
        self, phase: str, reference_viscosity: np.ndarray
    ) -> np.ndarray:
        """
        Calculate temperature-dependent viscosity.

        Args:
            phase: Fluid phase ('oil', 'water', 'gas')
            reference_viscosity: Reference viscosity at standard conditions

        Returns:
            Temperature-dependent viscosity
        """
        if phase not in self.viscosity_model:
            return reference_viscosity

        model = self.viscosity_model[phase]

        if model["type"] == "exponential":
            b = model.get("temperature_coefficient", 0.02)
            T_ref = model.get("reference_temperature", 180.0)
            return reference_viscosity * np.exp(-b * (self.temperature - T_ref))

        elif model["type"] == "andrade":
            T_abs = self.temperature + 459.67
            A = model.get("A", 1e-5)
            B = model.get("B", 10000.0)
            return A * np.exp(B / np.maximum(T_abs, 1e-6))  # Avoid division by zero

        elif model["type"] == "custom":
            if "function" in model and callable(model["function"]):
                return model["function"](self.temperature, reference_viscosity)

        return reference_viscosity

    def calculate_thermal_properties(
        self, pressure: np.ndarray, saturation: Dict[str, np.ndarray]
    ) -> Dict:
        """
        Calculate thermal properties for current conditions.

        Args:
            pressure: Pressure field
            saturation: Dictionary of phase saturations

        Returns:
            Dictionary of thermal properties
        """
        effective_thermal_conductivity = np.zeros(self.n_cells)  # Placeholder
        effective_heat_capacity = np.zeros(self.n_cells)  # Placeholder

        return {
            "thermal_conductivity": effective_thermal_conductivity,
            "heat_capacity": effective_heat_capacity,
            "temperature": self.temperature.copy(),  # Return a copy
        }


class SteamInjectionModel:
    """Model for steam injection processes."""

    def __init__(self, thermal_model: ThermalModel):
        """
        Initialize steam injection model.

        Args:
            thermal_model: Thermal model instance
        """
        self.thermal_model = thermal_model
        self.steam_quality = 0.8
        self.steam_temperature = 400.0
        self.steam_pressure = 250.0
        self.steam_enthalpy = 1200.0
        self.injection_cells = []
        self.injection_rates = {}
        self.steam_chamber = np.zeros(thermal_model.n_cells, dtype=bool)
        self.condensation_front = np.zeros(thermal_model.n_cells, dtype=bool)

    def set_steam_properties(self, quality: float, temperature: float, pressure: float):
        """
        Set steam properties.
        """
        self.steam_quality = quality
        self.steam_temperature = temperature
        self.steam_pressure = pressure
        self.steam_enthalpy = 1000.0 + 0.5 * temperature

    def add_injection_well(self, well_cells: List[int], injection_rate: float):
        """
        Add steam injection well.
        """
        for cell_idx in well_cells:  # Ensure cell_idx is used
            if 0 <= cell_idx < self.thermal_model.n_cells:  # Boundary check
                self.injection_cells.append(cell_idx)
                self.injection_rates[cell_idx] = injection_rate * 5.615 * 62.4
            else:
                print(
                    f"Warning: Cell index {cell_idx} out of bounds for injection well."
                )

    def calculate_steam_injection_effects(
        self,
        dt: float,
        saturation: Dict[str, np.ndarray],
        pressure: np.ndarray,
        grid_geometry: Dict,
    ):
        """
        Calculate effects of steam injection.
        """
        heat_source = np.zeros(self.thermal_model.n_cells)

        dx_val = grid_geometry.get("dx", 1.0)
        dy_val = grid_geometry.get("dy", 1.0)
        dz_val = grid_geometry.get("dz", 1.0)

        dx_arr = (
            np.full(self.thermal_model.nx, dx_val)
            if isinstance(dx_val, (int, float))
            else dx_val
        )
        dy_arr = (
            np.full(self.thermal_model.ny, dy_val)
            if isinstance(dy_val, (int, float))
            else dy_val
        )
        dz_arr = (
            np.full(self.thermal_model.nz, dz_val)
            if isinstance(dz_val, (int, float))
            else dz_val
        )

        cell_volume = np.zeros(self.thermal_model.n_cells)
        for i in range(self.thermal_model.nx):
            for j in range(self.thermal_model.ny):
                for k in range(self.thermal_model.nz):
                    idx = (
                        i
                        + j * self.thermal_model.nx
                        + k * self.thermal_model.nx * self.thermal_model.ny
                    )
                    if (
                        idx < self.thermal_model.n_cells
                    ):  # Ensure index is within bounds
                        cell_volume[idx] = dx_arr[i] * dy_arr[j] * dz_arr[k]

        for cell_idx in self.injection_cells:  # Use cell_idx
            if (
                cell_idx in self.injection_rates
                and cell_idx < len(cell_volume)
                and cell_volume[cell_idx] > 0
            ):
                heat_added = self.injection_rates[cell_idx] * self.steam_enthalpy * dt
                heat_source[cell_idx] = heat_added / cell_volume[cell_idx]
                if cell_idx < len(self.thermal_model.temperature):
                    self.thermal_model.temperature[cell_idx] = self.steam_temperature

        self._update_steam_chamber(pressure, saturation)

        return {
            "temperature": self.thermal_model.temperature.copy(),
            "heat_source": heat_source,
            "steam_chamber": self.steam_chamber.copy(),
            "condensation_front": self.condensation_front.copy(),
        }

    def _update_steam_chamber(
        self, pressure: np.ndarray, saturation: Dict[str, np.ndarray]
    ):
        """Update steam chamber and condensation front."""
        steam_temp_threshold = self.steam_temperature - 10.0
        gas_sat_threshold = 0.3

        for i_idx in range(self.thermal_model.n_cells):  # Use i_idx
            if (
                i_idx < len(self.thermal_model.temperature)
                and "gas" in saturation
                and i_idx < len(saturation["gas"])
            ):
                if (
                    self.thermal_model.temperature[i_idx] >= steam_temp_threshold
                    and saturation["gas"][i_idx] >= gas_sat_threshold
                ):
                    self.steam_chamber[i_idx] = True
                else:
                    self.steam_chamber[i_idx] = False

                if (
                    0 < i_idx < self.thermal_model.n_cells - 1
                ):  # Check bounds for gradient
                    if i_idx + 1 < len(
                        self.thermal_model.temperature
                    ) and i_idx - 1 < len(
                        self.thermal_model.temperature
                    ):  # Check bounds for temp access
                        temp_gradient = abs(
                            self.thermal_model.temperature[i_idx + 1]
                            - self.thermal_model.temperature[i_idx - 1]
                        )
                        if (
                            temp_gradient > 20.0
                            and saturation["gas"][i_idx]
                            < saturation["gas"][
                                i_idx - 1
                            ]  # Check bounds for sat access
                            and self.thermal_model.temperature[i_idx]
                            < steam_temp_threshold
                        ):
                            self.condensation_front[i_idx] = True
                        else:
                            self.condensation_front[i_idx] = False
                    else:
                        self.condensation_front[i_idx] = (
                            False  # Out of bounds for gradient calc
                        )
                else:
                    self.condensation_front[i_idx] = False  # Edge cells
            else:  # If 'gas' not in saturation or index out of bounds
                self.steam_chamber[i_idx] = False
                self.condensation_front[i_idx] = False
