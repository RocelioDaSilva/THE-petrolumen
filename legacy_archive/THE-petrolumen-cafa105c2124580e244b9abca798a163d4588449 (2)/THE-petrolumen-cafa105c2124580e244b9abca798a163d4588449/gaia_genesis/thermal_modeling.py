"""
Thermal Modeling Module

This module provides advanced thermal modeling capabilities for reservoir simulation,
including heat transfer, temperature-dependent fluid properties, and thermal recovery methods.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Any
from scipy.sparse import csr_matrix, lil_matrix
from scipy.sparse.linalg import spsolve
import numba

class ThermalModel:
    def __init__(self, grid_dims: Tuple[int, int, int], properties: Dict[str, np.ndarray]):
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
        self.temperature = np.ones(self.n_cells) * properties.get('initial_temperature', 180.0)  # °F
        self.temperature_prev = self.temperature.copy()
        
        # Initialize thermal properties
        self.rock_heat_capacity = properties.get('rock_heat_capacity', np.ones(self.n_cells) * 0.2)  # Btu/lb-°F
        self.rock_thermal_conductivity = properties.get('rock_thermal_conductivity', np.ones(self.n_cells) * 1.0)  # Btu/ft-hr-°F
        self.rock_density = properties.get('rock_density', np.ones(self.n_cells) * 165.0)  # lb/ft³
        
        # Fluid thermal properties
        self.fluid_heat_capacity = {
            'oil': properties.get('oil_heat_capacity', np.ones(self.n_cells) * 0.5),  # Btu/lb-°F
            'water': properties.get('water_heat_capacity', np.ones(self.n_cells) * 1.0),  # Btu/lb-°F
            'gas': properties.get('gas_heat_capacity', np.ones(self.n_cells) * 0.5)  # Btu/lb-°F
        }
        
        self.fluid_thermal_conductivity = {
            'oil': properties.get('oil_thermal_conductivity', np.ones(self.n_cells) * 0.08),  # Btu/ft-hr-°F
            'water': properties.get('water_thermal_conductivity', np.ones(self.n_cells) * 0.4),  # Btu/ft-hr-°F
            'gas': properties.get('gas_thermal_conductivity', np.ones(self.n_cells) * 0.02)  # Btu/ft-hr-°F
        }
        
        # Initialize boundary conditions
        self.boundary_conditions = {
            'type': 'constant_temperature',  # 'constant_temperature', 'constant_heat_flux', 'convective'
            'values': {
                'top': 180.0,  # °F
                'bottom': 180.0,  # °F
                'left': 180.0,  # °F
                'right': 180.0,  # °F
                'front': 180.0,  # °F
                'back': 180.0  # °F
            }
        }
        
        # Initialize thermal recovery method
        self.thermal_recovery_method = None  # 'steam_flooding', 'cyclic_steam_stimulation', 'sagd', 'in_situ_combustion'
        self.thermal_recovery_params = {}
        
        # Temperature-dependent viscosity model parameters
        self.viscosity_model = {
            'oil': {
                'type': 'exponential',  # 'exponential', 'andrade', 'custom'
                'reference_temperature': 180.0,  # °F
                'reference_viscosity': 10.0,  # cP
                'activation_energy': 10000.0  # J/mol
            },
            'water': {
                'type': 'exponential',
                'reference_temperature': 180.0,  # °F
                'reference_viscosity': 0.5,  # cP
                'activation_energy': 5000.0  # J/mol
            }
        }
    
    def set_initial_temperature(self, temperature_gradient: float, depth: np.ndarray, surface_temp: float = 60.0):
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
        
        if method == 'steam_flooding':
            # Initialize steam flooding parameters
            self.thermal_recovery_params.setdefault('steam_quality', 0.8)
            self.thermal_recovery_params.setdefault('steam_temperature', 400.0)  # °F
            self.thermal_recovery_params.setdefault('steam_injection_rate', 1000.0)  # bbl/day
        
        elif method == 'cyclic_steam_stimulation':
            # Initialize CSS parameters
            self.thermal_recovery_params.setdefault('steam_quality', 0.8)
            self.thermal_recovery_params.setdefault('steam_temperature', 400.0)  # °F
            self.thermal_recovery_params.setdefault('injection_period', 10.0)  # days
            self.thermal_recovery_params.setdefault('soaking_period', 5.0)  # days
            self.thermal_recovery_params.setdefault('production_period', 30.0)  # days
        
        elif method == 'sagd':
            # Initialize SAGD parameters
            self.thermal_recovery_params.setdefault('steam_quality', 0.8)
            self.thermal_recovery_params.setdefault('steam_temperature', 400.0)  # °F
            self.thermal_recovery_params.setdefault('well_pair_spacing', 5.0)  # m
            self.thermal_recovery_params.setdefault('vertical_spacing', 5.0)  # m
        
        elif method == 'in_situ_combustion':
            # Initialize in-situ combustion parameters
            self.thermal_recovery_params.setdefault('air_injection_rate', 1000.0)  # scf/day
            self.thermal_recovery_params.setdefault('ignition_temperature', 600.0)  # °F
            self.thermal_recovery_params.setdefault('fuel_content', 0.1)  # kg/kg
    
    def solve_heat_equation(self, dt: float, saturation: Dict[str, np.ndarray], 
                           velocity: Dict[str, np.ndarray], grid_geometry: Dict):
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
        A, b = self._assemble_heat_equation(dt, saturation, velocity, grid_geometry)
        
        # Apply boundary conditions
        A, b = self._apply_thermal_boundary_conditions(A, b, grid_geometry)
        
        # Solve for temperature
        self.temperature = spsolve(A, b)
        
        # Apply thermal recovery effects
        if self.thermal_recovery_method:
            self._apply_thermal_recovery_effects(dt, saturation)
    
    def _assemble_heat_equation(self, dt: float, saturation: Dict[str, np.ndarray], 
                              velocity: Dict[str, np.ndarray], grid_geometry: Dict):
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
        # Convert dt from days to hours
        dt_hours = dt * 24.0
        
        # Create empty system matrix and right-hand side
        A = lil_matrix((self.n_cells, self.n_cells))
        b = np.zeros(self.n_cells)
        
        # Get grid properties
        dx = grid_geometry.get('dx', np.ones(self.nx))
        dy = grid_geometry.get('dy', np.ones(self.ny))
        dz = grid_geometry.get('dz', np.ones(self.nz))
        
        # Calculate cell volumes
        cell_volume = np.zeros(self.n_cells)
        for i in range(self.nx):
            for j in range(self.ny):
                for k in range(self.nz):
                    idx = i + j * self.nx + k * self.nx * self.ny
                    cell_volume[idx] = dx[i] * dy[j] * dz[k]
        
        # Calculate effective thermal properties
        effective_heat_capacity = np.zeros(self.n_cells)
        effective_thermal_conductivity = np.zeros(self.n_cells)
        
        for i in range(self.n_cells):
            # Calculate porosity-weighted heat capacity
            porosity = grid_geometry.get('porosity', np.ones(self.n_cells) * 0.2)[i]
            
            # Rock contribution
            effective_heat_capacity[i] = (1 - porosity) * self.rock_density[i] * self.rock_heat_capacity[i]
            
            # Fluid contribution
            for phase in ['oil', 'water', 'gas']:
                if phase in saturation:
                    phase_density = 50.0  # lb/ft³ (placeholder - should be calculated from PVT)
                    effective_heat_capacity[i] += porosity * saturation[phase][i] * phase_density * self.fluid_heat_capacity[phase][i]
            
            # Calculate effective thermal conductivity (simple weighted average)
            effective_thermal_conductivity[i] = (1 - porosity) * self.rock_thermal_conductivity[i]
            
            for phase in ['oil', 'water', 'gas']:
                if phase in saturation:
                    effective_thermal_conductivity[i] += porosity * saturation[phase][i] * self.fluid_thermal_conductivity[phase][i]
        
        # Assemble system (simplified 1D approach for illustration)
        # In a real simulator, this would be a full 3D discretization
        for i in range(self.n_cells):
            # Diagonal term (accumulation)
            A[i, i] = effective_heat_capacity[i] * cell_volume[i] / dt_hours
            
            # Right-hand side (previous temperature)
            b[i] = effective_heat_capacity[i] * cell_volume[i] * self.temperature_prev[i] / dt_hours
            
            # Add conduction terms (simplified)
            # In a real simulator, this would consider the full 3D stencil
            if i > 0:  # Left neighbor
                A[i, i-1] = -effective_thermal_conductivity[i] * cell_volume[i] / dx[i % self.nx]**2
                A[i, i] -= A[i, i-1]
            
            if i < self.n_cells - 1:  # Right neighbor
                A[i, i+1] = -effective_thermal_conductivity[i] * cell_volume[i] / dx[i % self.nx]**2
                A[i, i] -= A[i, i+1]
            
            # Add convection terms (simplified)
            # In a real simulator, this would use upwinding and consider all phases
            for phase in ['oil', 'water', 'gas']:
                if phase in velocity and phase in saturation:
                    # Simplified 1D convection
                    if i > 0 and velocity[phase][i] < 0:  # Flow from right to left
                        A[i, i] += velocity[phase][i] * saturation[phase][i] * self.fluid_heat_capacity[phase][i] * cell_volume[i] / dx[i % self.nx]
                        A[i, i-1] -= velocity[phase][i] * saturation[phase][i] * self.fluid_heat_capacity[phase][i] * cell_volume[i] / dx[i % self.nx]
                    
                    if i < self.n_cells - 1 and velocity[phase][i] > 0:  # Flow from left to right
                        A[i, i] -= velocity[phase][i] * saturation[phase][i] * self.fluid_heat_capacity[phase][i] * cell_volume[i] / dx[i % self.nx]
                        A[i, i+1] += velocity[phase][i] * saturation[phase][i] * self.fluid_heat_capacity[phase][i] * cell_volume[i] / dx[i % self.nx]
        
        # Convert to CSR format for efficient solving
        A = A.tocsr()
        
        return A, b
    
    def _apply_thermal_boundary_conditions(self, A: csr_matrix, b: np.ndarray, grid_geometry: Dict):
        """Apply thermal boundary conditions to the system."""
        # This is a placeholder for the full implementation
        # In a real simulator, this would apply the specified boundary conditions
        return A, b
    
    def _apply_thermal_recovery_effects(self, dt: float, saturation: Dict[str, np.ndarray]):
        """Apply effects of thermal recovery methods."""
        if self.thermal_recovery_method == 'steam_flooding':
            self._apply_steam_flooding_effects(dt, saturation)
        elif self.thermal_recovery_method == 'cyclic_steam_stimulation':
            self._apply_css_effects(dt, saturation)
        elif self.thermal_recovery_method == 'sagd':
            self._apply_sagd_effects(dt, saturation)
        elif self.thermal_recovery_method == 'in_situ_combustion':
            self._apply_isc_effects(dt, saturation)
    
    def _apply_steam_flooding_effects(self, dt: float, saturation: Dict[str, np.ndarray]):
        """Apply steam flooding effects."""
        # This is a placeholder for the full implementation
        # In a real simulator, this would model steam injection and condensation
        pass
    
    def _apply_css_effects(self, dt: float, saturation: Dict[str, np.ndarray]):
        """Apply cyclic steam stimulation effects."""
        # This is a placeholder for the full implementation
        pass
    
    def _apply_sagd_effects(self, dt: float, saturation: Dict[str, np.ndarray]):
        """Apply SAGD effects."""
        # This is a placeholder for the full implementation
        pass
    
    def _apply_isc_effects(self, dt: float, saturation: Dict[str, np.ndarray]):
        """Apply in-situ combustion effects."""
        # This is a placeholder for the full implementation
        pass
    
    def calculate_temperature_dependent_viscosity(self, phase: str, reference_viscosity: np.ndarray) -> np.ndarray:
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
        
        if model['type'] == 'exponential':
            # Simple exponential model: μ = μ_ref * exp(-b * (T - T_ref))
            b = model.get('temperature_coefficient', 0.02)  # 1/°F
            T_ref = model.get('reference_temperature', 180.0)  # °F
            
            return reference_viscosity * np.exp(-b * (self.temperature - T_ref))
        
        elif model['type'] == 'andrade':
            # Andrade equation: μ = A * exp(B/T)
            # Convert temperature to absolute (Rankine)
            T_abs = self.temperature + 459.67  # °F to °R
            
            # Get Andrade parameters
            A = model.get('A', 1e-5)
            B = model.get('B', 10000.0)
            
            return A * np.exp(B / T_abs)
        
        elif model['type'] == 'custom':
            # Custom model using provided function
            if 'function' in model and callable(model['function']):
                return model['function'](self.temperature, reference_viscosity)
        
        # Default: return reference viscosity
        return reference_viscosity
    
    def calculate_thermal_properties(self, pressure: np.ndarray, saturation: Dict[str, np.ndarray]) -> Dict:
        """
        Calculate thermal properties for current conditions.
        
        Args:
            pressure: Pressure field
            saturation: Dictionary of phase saturations
            
        Returns:
            Dictionary of thermal properties
        """
        # Calculate effective thermal properties
        effective_thermal_conductivity = np.zeros(self.n_cells)
        effective_heat_capacity = np.zeros(self.n_cells)
        
        # This is a placeholder for the full implementation
        # In a real simulator, this would calculate all relevant thermal properties
        
        return {
            'thermal_conductivity': effective_thermal_conductivity,
            'heat_capacity': effective_heat_capacity,
            'temperature': self.temperature
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
        
        # Steam properties
        self.steam_quality = 0.8  # Fraction
        self.steam_temperature = 400.0  # °F
        self.steam_pressure = 250.0  # psia
        self.steam_enthalpy = 1200.0  # Btu/lb
        
        # Injection parameters
        self.injection_cells = []  # Cells where steam is injected
        self.injection_rates = {}  # Steam injection rates (lb/day)
        
        # Steam chamber tracking
        self.steam_chamber = np.zeros(thermal_model.n_cells, dtype=bool)
        self.condensation_front = np.zeros(thermal_model.n_cells, dtype=bool)
    
    def set_steam_properties(self, quality: float, temperature: float, pressure: float):
        """
        Set steam properties.
        
        Args:
            quality: Steam quality (fraction)
            temperature: Steam temperature (°F)
            pressure: Steam pressure (psia)
        """
        self.steam_quality = quality
        self.steam_temperature = temperature
        self.steam_pressure = pressure
        
        # Calculate steam enthalpy (simplified correlation)
        # In a real simulator, this would use steam tables
        self.steam_enthalpy = 1000.0 + 0.5 * temperature  # Btu/lb
    
    def add_injection_well(self, well_cells: List[int], injection_rate: float):
        """
        Add steam injection well.
        
        Args:
            well_cells: List of cell indices for the well
            injection_rate: Steam injection rate (bbl/day)
        """
        for cell in well_cells:
            self.injection_cells.append(cell)
            
            # Convert from bbl/day to lb/day (assuming water density of 62.4 lb/ft³)
            self.injection_rates[cell] = injection_rate * 5.615 * 62.4  # lb/day
    
    def calculate_steam_injection_effects(self, dt: float, saturation: Dict[str, np.ndarray],
                                        pressure: np.ndarray, grid_geometry: Dict):
        """
        Calculate effects of steam injection.
        
        Args:
            dt: Time step (days)
            saturation: Dictionary of phase saturations
            pressure: Pressure field
            grid_geometry: Grid geometry information
            
        Returns:
            Dictionary of updated properties
        """
        # Initialize heat source term
        heat_source = np.zeros(self.thermal_model.n_cells)
        
        # Calculate cell volumes
        dx = grid_geometry.get('dx', np.ones(self.thermal_model.nx))
        dy = grid_geometry.get('dy', np.ones(self.thermal_model.ny))
        dz = grid_geometry.get('dz', np.ones(self.thermal_model.nz))
        
        cell_volume = np.zeros(self.thermal_model.n_cells)
        for i in range(self.thermal_model.nx):
            for j in range(self.thermal_model.ny):
                for k in range(self.thermal_model.nz):
                    idx = i + j * self.thermal_model.nx + k * self.thermal_model.nx * self.thermal_model.ny
                    cell_volume[idx] = dx[i] * dy[j] * dz[k]
        
        # Apply heat from steam injection
        for cell in self.injection_cells:
            if cell in self.injection_rates:
                # Heat added = mass * enthalpy
                heat_added = self.injection_rates[cell] * self.steam_enthalpy * dt  # Btu
                
                # Convert to heat source term (Btu/ft³-day)
                heat_source[cell] = heat_added / cell_volume[cell]
                
                # Update temperature directly for injection cell
                self.thermal_model.temperature[cell] = self.steam_temperature
        
        # Track steam chamber
        self._update_steam_chamber(pressure, saturation)
        
        # Return updated properties
        return {
            'temperature': self.thermal_model.temperature,
            'heat_source': heat_source,
            'steam_chamber': self.steam_chamber,
            'condensation_front': self.condensation_front
        }
    
    def _update_steam_chamber(self, pressure: np.ndarray, saturation: Dict[str, np.ndarray]):
        """Update steam chamber and condensation front."""
        # Simple model: steam chamber is where temperature is close to steam temperature
        # and gas saturation is high
        steam_temp_threshold = self.steam_temperature - 10.0  # °F
        gas_sat_threshold = 0.3
        
        for i in range(self.thermal_model.n_cells):
            # Check if cell is in steam chamber
            if (self.thermal_model.temperature[i] >= steam_temp_threshold and
                'gas' in saturation and saturation['gas'][i] >= gas_sat_threshold):
                self.steam_chamber[i] = True
            else:
                self.steam_chamber[i] = False
            
            # Check if cell is at condensation front
            # (high temperature gradient and decreasing gas saturation)
            if i > 0 and i < self.thermal_model.n_cells - 1:
                temp_gradient = abs(self.thermal_model.temperature[i+1] - self.thermal_model.temperature[i-1])
                
                if (temp_gradient > 20.0 and  # °F
                    'gas' in saturation and
                    saturation['gas'][i] < saturation['gas'][i-1] and
                    self.thermal_model.temperature[i] < steam_temp_threshold):
                    self.condensation_front[i] = True
                else:
                    self.condensation_front[i] = False
