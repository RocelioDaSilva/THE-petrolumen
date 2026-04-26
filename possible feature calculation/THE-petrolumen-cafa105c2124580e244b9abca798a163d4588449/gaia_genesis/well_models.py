"""
Advanced Well Modeling

This module provides advanced well modeling capabilities for reservoir simulation,
including multisegment wells, intelligent well completions, and complex well controls.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum, auto

class WellType(Enum):
    """Types of wells in the simulation."""
    PRODUCER = auto()
    INJECTOR = auto()
    OBSERVATION = auto()

class CompletionType(Enum):
    """Types of well completions."""
    PERFORATION = auto()
    OPEN_HOLE = auto()
    FRACTURE = auto()
    SLOTTED_LINER = auto()
    SCREEN = auto()

class ControlType(Enum):
    """Types of well controls."""
    RATE = auto()
    BHP = auto()
    THP = auto()
    DRAWDOWN = auto()
    LIFT_GAS = auto()

@dataclass
class WellControl:
    """Well control settings."""
    control_type: ControlType
    target_value: float
    phase: str = 'oil'  # 'oil', 'gas', 'water', 'liquid'
    min_bhp: Optional[float] = None
    max_bhp: Optional[float] = None
    start_time: float = 0.0
    end_time: Optional[float] = None

@dataclass
class WellCompletion:
    """Well completion data."""
    i: int
    j: int
    k: int
    completion_type: CompletionType
    open_flag: bool = True
    skin: float = 0.0
    diameter: float = 0.5  # ft
    kh: Optional[float] = None  # md-ft
    well_index: Optional[float] = None
    transmissibility_factor: float = 1.0

@dataclass
class WellSegment:
    """Well segment for multisegment well model."""
    segment_id: int
    inlet_segment: Optional[int]
    outlet_segment: Optional[int]
    length: float  # ft
    diameter: float  # ft
    roughness: float  # ft
    depth_change: float  # ft
    volume: Optional[float] = None
    pressure_drop_model: str = 'beggs_brill'  # 'beggs_brill', 'hagedorn_brown', 'no_pressure_drop'

class Well:
    """Advanced well model with multisegment capabilities."""
    
    def __init__(self, name: str, well_type: WellType, heel_i: int, heel_j: int, heel_k: int):
        """
        Initialize well.
        
        Args:
            name: Well name
            well_type: Well type (producer, injector, etc.)
            heel_i, heel_j, heel_k: Heel location (grid indices)
        """
        self.name = name
        self.well_type = well_type
        self.heel_i = heel_i
        self.heel_j = heel_j
        self.heel_k = heel_k
        
        self.completions: List[WellCompletion] = []
        self.segments: List[WellSegment] = []
        self.controls: List[WellControl] = []
        self.trajectory: List[Tuple[float, float, float]] = []
        
        self.status = 'OPEN'  # 'OPEN', 'SHUT'
        self.current_control = 0
        
        # Results
        self.bhp: List[float] = []
        self.thp: List[float] = []
        self.rates: Dict[str, List[float]] = {
            'oil': [], 'gas': [], 'water': [], 'total': []
        }
        self.cumulative: Dict[str, float] = {
            'oil': 0.0, 'gas': 0.0, 'water': 0.0
        }
    
    def add_completion(self, completion: WellCompletion):
        """Add completion to well."""
        self.completions.append(completion)
    
    def add_segment(self, segment: WellSegment):
        """Add segment to well (for multisegment wells)."""
        self.segments.append(segment)
    
    def add_control(self, control: WellControl):
        """Add control to well."""
        self.controls.append(control)
    
    def set_trajectory(self, trajectory: List[Tuple[float, float, float]]):
        """
        Set well trajectory.
        
        Args:
            trajectory: List of (x, y, z) points defining well path
        """
        self.trajectory = trajectory
    
    def calculate_well_index(self, grid_properties: Dict):
        """
        Calculate well index for each completion.
        
        Args:
            grid_properties: Grid properties dictionary
        """
        for comp in self.completions:
            if comp.well_index is None:
                comp.well_index = self._peaceman_well_index(comp, grid_properties)
    
    def _peaceman_well_index(self, completion: WellCompletion, grid_properties: Dict) -> float:
        """
        Calculate Peaceman well index.
        
        Args:
            completion: Well completion
            grid_properties: Grid properties
            
        Returns:
            Well index (md-ft/cp/psi)
        """
        i, j, k = completion.i, completion.j, completion.k
        
        # Get grid properties
        dx = grid_properties.get('dx', np.ones(1))[i if isinstance(grid_properties.get('dx', np.ones(1)), np.ndarray) else 0]
        dy = grid_properties.get('dy', np.ones(1))[j if isinstance(grid_properties.get('dy', np.ones(1)), np.ndarray) else 0]
        dz = grid_properties.get('dz', np.ones(1))[k if isinstance(grid_properties.get('dz', np.ones(1)), np.ndarray) else 0]
        
        # Get permeability
        kx = grid_properties.get('permeability_x', np.ones((1, 1, 1)))[i, j, k]
        ky = grid_properties.get('permeability_y', np.ones((1, 1, 1)))[i, j, k]
        kz = grid_properties.get('permeability_z', np.ones((1, 1, 1)))[i, j, k]
        
        # Calculate equivalent radius
        re = 0.28 * np.sqrt(np.sqrt(ky/kx) * dx**2 + np.sqrt(kx/ky) * dy**2) / \
             ((ky/kx)**0.25 + (kx/ky)**0.25)
        
        # Well radius
        rw = completion.diameter / 2
        
        # Calculate well index
        k_avg = np.sqrt(kx * ky)
        wi = 2 * np.pi * k_avg * dz / (np.log(re/rw) + completion.skin)
        
        return wi * completion.transmissibility_factor

class MultisegmentWell(Well):
    """Multisegment well model with advanced flow modeling."""
    
    def __init__(self, name: str, well_type: WellType, heel_i: int, heel_j: int, heel_k: int):
        """Initialize multisegment well."""
        super().__init__(name, well_type, heel_i, heel_j, heel_k)
        self.is_multisegment = True
        
        # Segment properties
        self.segment_pressure: List[float] = []
        self.segment_temperature: List[float] = []
        self.segment_flow_rates: Dict[str, List[float]] = {
            'oil': [], 'gas': [], 'water': [], 'total': []
        }
        self.segment_holdup: List[float] = []
        self.segment_flow_regime: List[str] = []
    
    def build_segment_topology(self):
        """Build segment topology from segments."""
        if not self.segments:
            return
        
        # Sort segments by ID
        self.segments.sort(key=lambda s: s.segment_id)
        
        # Validate topology
        for segment in self.segments:
            if segment.inlet_segment is not None:
                # Check if inlet segment exists
                if not any(s.segment_id == segment.inlet_segment for s in self.segments):
                    raise ValueError(f"Inlet segment {segment.inlet_segment} for segment {segment.segment_id} not found")
            
            if segment.outlet_segment is not None:
                # Check if outlet segment exists
                if not any(s.segment_id == segment.outlet_segment for s in self.segments):
                    raise ValueError(f"Outlet segment {segment.outlet_segment} for segment {segment.segment_id} not found")
    
    def calculate_pressure_profile(self, fluid_properties: Dict):
        """
        Calculate pressure profile along well.
        
        Args:
            fluid_properties: Fluid properties dictionary
        """
        # Initialize pressure profile
        self.segment_pressure = [0.0] * len(self.segments)
        
        # Set pressure at bottom hole (last segment)
        if self.bhp:
            self.segment_pressure[-1] = self.bhp[-1]
        else:
            return
        
        # Calculate pressure profile from bottom to top
        for i in range(len(self.segments) - 2, -1, -1):
            segment = self.segments[i]
            outlet_segment = next((s for s in self.segments if s.segment_id == segment.outlet_segment), None)
            
            if outlet_segment is None:
                continue
            
            # Get outlet segment pressure
            outlet_pressure = self.segment_pressure[self.segments.index(outlet_segment)]
            
            # Calculate pressure drop
            dp = self._calculate_segment_pressure_drop(segment, fluid_properties)
            
            # Update segment pressure
            self.segment_pressure[i] = outlet_pressure - dp
    
    def _calculate_segment_pressure_drop(self, segment: WellSegment, fluid_properties: Dict) -> float:
        """
        Calculate pressure drop across segment.
        
        Args:
            segment: Well segment
            fluid_properties: Fluid properties
            
        Returns:
            Pressure drop (psi)
        """
        # Simplified pressure drop calculation
        if segment.pressure_drop_model == 'no_pressure_drop':
            return 0.0
        
        # Hydrostatic component
        fluid_density = fluid_properties.get('density', 62.4)  # lb/ft³
        dp_hydrostatic = 0.433 * fluid_density * segment.depth_change  # psi
        
        # Friction component
        if segment.pressure_drop_model == 'beggs_brill':
            dp_friction = self._beggs_brill_pressure_drop(segment, fluid_properties)
        elif segment.pressure_drop_model == 'hagedorn_brown':
            dp_friction = self._hagedorn_brown_pressure_drop(segment, fluid_properties)
        else:
            dp_friction = 0.0
        
        return dp_hydrostatic + dp_friction
    
    def _beggs_brill_pressure_drop(self, segment: WellSegment, fluid_properties: Dict) -> float:
        """Calculate pressure drop using Beggs-Brill correlation."""
        # Simplified implementation
        return 0.0  # Placeholder
    
    def _hagedorn_brown_pressure_drop(self, segment: WellSegment, fluid_properties: Dict) -> float:
        """Calculate pressure drop using Hagedorn-Brown correlation."""
        # Simplified implementation
        return 0.0  # Placeholder

class IntelligentWell(MultisegmentWell):
    """Intelligent well with ICD/ICV completions and downhole monitoring."""
    
    def __init__(self, name: str, well_type: WellType, heel_i: int, heel_j: int, heel_k: int):
        """Initialize intelligent well."""
        super().__init__(name, well_type, heel_i, heel_j, heel_k)
        self.is_intelligent = True
        
        # ICD/ICV settings
        self.icd_settings: Dict[int, Dict] = {}  # completion_id -> settings
        self.icv_settings: Dict[int, Dict] = {}  # completion_id -> settings
        
        # Downhole monitoring
        self.downhole_sensors: Dict[str, Dict] = {}
        
        # Control strategy
        self.control_strategy: Optional[callable] = None
    
    def add_icd(self, completion_id: int, strength: float, type_: str = 'autonomous'):
        """
        Add inflow control device (ICD).
        
        Args:
            completion_id: Completion ID
            strength: ICD strength
            type_: ICD type ('autonomous', 'active', 'passive')
        """
        self.icd_settings[completion_id] = {
            'type': type_,
            'strength': strength,
            'status': 'OPEN'
        }
    
    def add_icv(self, completion_id: int, positions: int = 10, current_position: int = 10):
        """
        Add interval control valve (ICV).
        
        Args:
            completion_id: Completion ID
            positions: Number of valve positions
            current_position: Current valve position
        """
        self.icv_settings[completion_id] = {
            'positions': positions,
            'current_position': current_position,
            'status': 'OPEN'
        }
    
    def add_downhole_sensor(self, name: str, location: Tuple[int, int, int], 
                           sensor_type: str, frequency: float = 1.0):
        """
        Add downhole sensor.
        
        Args:
            name: Sensor name
            location: Sensor location (i, j, k)
            sensor_type: Sensor type ('pressure', 'temperature', 'flow_rate', 'water_cut')
            frequency: Measurement frequency (1/day)
        """
        self.downhole_sensors[name] = {
            'location': location,
            'type': sensor_type,
            'frequency': frequency,
            'data': []
        }
    
    def set_control_strategy(self, strategy_func: callable):
        """
        Set control strategy function.
        
        Args:
            strategy_func: Control strategy function
        """
        self.control_strategy = strategy_func
    
    def update_controls(self, reservoir_state: Dict, time: float):
        """
        Update well controls based on strategy.
        
        Args:
            reservoir_state: Current reservoir state
            time: Current simulation time
        """
        if self.control_strategy is None:
            return
        
        # Get sensor data
        sensor_data = {name: sensor['data'][-1] if sensor['data'] else None 
                      for name, sensor in self.downhole_sensors.items()}
        
        # Call control strategy
        control_updates = self.control_strategy(self, sensor_data, reservoir_state, time)
        
        # Apply control updates
        if control_updates:
            # Update ICVs
            if 'icv_positions' in control_updates:
                for comp_id, position in control_updates['icv_positions'].items():
                    if comp_id in self.icv_settings:
                        self.icv_settings[comp_id]['current_position'] = position
            
            # Update well control
            if 'well_control' in control_updates:
                control = control_updates['well_control']
                if isinstance(control, WellControl):
                    self.controls.append(control)
                    self.current_control = len(self.controls) - 1

class WellManager:
    """Manager for all wells in the simulation."""
    
    def __init__(self):
        """Initialize well manager."""
        self.wells: Dict[str, Well] = {}
        self.well_groups: Dict[str, List[str]] = {}
        self.group_controls: Dict[str, List[WellControl]] = {}
    
    def add_well(self, well: Well):
        """
        Add well to manager.
        
        Args:
            well: Well object
        """
        self.wells[well.name] = well
    
    def create_well_group(self, group_name: str, well_names: List[str]):
        """
        Create well group.
        
        Args:
            group_name: Group name
            well_names: List of well names in group
        """
        self.well_groups[group_name] = well_names
    
    def add_group_control(self, group_name: str, control: WellControl):
        """
        Add control to well group.
        
        Args:
            group_name: Group name
            control: Well control
        """
        if group_name not in self.group_controls:
            self.group_controls[group_name] = []
        
        self.group_controls[group_name].append(control)
    
    def initialize_wells(self, grid_properties: Dict):
        """
        Initialize all wells.
        
        Args:
            grid_properties: Grid properties
        """
        for well in self.wells.values():
            well.calculate_well_index(grid_properties)
            
            if isinstance(well, MultisegmentWell):
                well.build_segment_topology()
    
    def update_well_controls(self, time: float):
        """
        Update well controls based on time.
        
        Args:
            time: Current simulation time
        """
        for well in self.wells.values():
            # Find applicable control
            applicable_controls = [
                (i, control) for i, control in enumerate(well.controls)
                if control.start_time <= time and (control.end_time is None or time <= control.end_time)
            ]
            
            if applicable_controls:
                # Use the latest applicable control
                well.current_control = applicable_controls[-1][0]
        
        # Update group controls
        for group_name, well_names in self.well_groups.items():
            if group_name in self.group_controls:
                applicable_controls = [
                    control for control in self.group_controls[group_name]
                    if control.start_time <= time and (control.end_time is None or time <= control.end_time)
                ]
                
                if applicable_controls:
                    # Apply group control to all wells in group
                    group_control = applicable_controls[-1]
                    self._apply_group_control(group_name, group_control)
    
    def _apply_group_control(self, group_name: str, group_control: WellControl):
        """
        Apply group control to wells.
        
        Args:
            group_name: Group name
            group_control: Group control
        """
        if group_name not in self.well_groups:
            return
        
        # Get wells in group
        well_names = self.well_groups[group_name]
        wells = [self.wells[name] for name in well_names if name in self.wells]
        
        if not wells:
            return
        
        # For rate control, distribute rate among wells
        if group_control.control_type == ControlType.RATE:
            # Simple allocation: equal distribution
            rate_per_well = group_control.target_value / len(wells)
            
            for well in wells:
                # Add new control to well
                well_control = WellControl(
                    control_type=group_control.control_type,
                    target_value=rate_per_well,
                    phase=group_control.phase,
                    min_bhp=group_control.min_bhp,
                    max_bhp=group_control.max_bhp,
                    start_time=group_control.start_time,
                    end_time=group_control.end_time
                )
                
                well.controls.append(well_control)
                well.current_control = len(well.controls) - 1
