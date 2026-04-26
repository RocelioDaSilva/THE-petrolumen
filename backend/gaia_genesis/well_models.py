"""
Advanced Well Modeling

This module provides advanced well modeling capabilities for reservoir simulation,
including multisegment wells, intelligent well completions, and complex well
controls.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass  # Removed unused 'field'
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
    phase: str = "oil"  # 'oil', 'gas', 'water', 'liquid'
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
    pressure_drop_model: str = (
        "beggs_brill"  # 'beggs_brill', 'hagedorn_brown', 'no_pressure_drop'
    )


class Well:
    """Advanced well model with multisegment capabilities."""

    def __init__(
        self, name: str, well_type: WellType, heel_i: int, heel_j: int, heel_k: int
    ):
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

        self.status = "OPEN"  # 'OPEN', 'SHUT'
        self.current_control = 0  # Index of the current active control

        # Results
        self.bhp: List[float] = []
        self.thp: List[float] = []
        self.rates: Dict[str, List[float]] = {
            "oil": [],
            "gas": [],
            "water": [],
            "total": [],
        }
        self.cumulative: Dict[str, float] = {
            "oil": 0.0,
            "gas": 0.0,
            "water": 0.0,
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

    def _peaceman_well_index(
        self, completion: WellCompletion, grid_properties: Dict
    ) -> float:
        """
        Calculate Peaceman well index.

        Args:
            completion: Well completion
            grid_properties: Grid properties

        Returns:
            Well index (md-ft/cp/psi) - Note: units depend on consistency,
            typically it's (ft^3/day) / (psi) for oilfield units
        """
        i, j, k = completion.i, completion.j, completion.k

        # Get grid properties
        # Handle scalar or array grid dimensions
        dx_all = grid_properties.get("dx", np.array([1.0]))
        dy_all = grid_properties.get("dy", np.array([1.0]))
        dz_all = grid_properties.get("dz", np.array([1.0]))

        dx = (
            dx_all[i]
            if isinstance(dx_all, np.ndarray) and i < len(dx_all)
            else dx_all if isinstance(dx_all, (int, float)) else 1.0
        )
        dy = (
            dy_all[j]
            if isinstance(dy_all, np.ndarray) and j < len(dy_all)
            else dy_all if isinstance(dy_all, (int, float)) else 1.0
        )
        dz = (
            dz_all[k]
            if isinstance(dz_all, np.ndarray) and k < len(dz_all)
            else dz_all if isinstance(dz_all, (int, float)) else 1.0
        )

        # Get permeability (assuming 3D array for kx, ky, kz)
        perm_shape = grid_properties.get("permeability_x", np.ones((1, 1, 1))).shape

        kx = grid_properties.get("permeability_x", np.ones(perm_shape))[
            min(i, perm_shape[0] - 1),
            min(j, perm_shape[1] - 1),
            min(k, perm_shape[2] - 1),
        ]
        ky = grid_properties.get("permeability_y", np.ones(perm_shape))[
            min(i, perm_shape[0] - 1),
            min(j, perm_shape[1] - 1),
            min(k, perm_shape[2] - 1),
        ]
        # kz is often used for vertical wells, but for horizontal, k_avg is more relevant for Peaceman in xy plane.
        # Peaceman's original formula is for 2D. For 3D, dz is the thickness of
        # the layer.

        if kx == 0 or ky == 0:
            return 0.0  # Avoid division by zero if permeability is zero

        # Calculate equivalent radius
        re_num = np.sqrt(np.sqrt(ky / kx) * dx**2 + np.sqrt(kx / ky) * dy**2)
        re_den = (ky / kx) ** 0.25 + (kx / ky) ** 0.25
        re = (
            0.28 * re_num / re_den if re_den != 0 else 0.14 * dx
        )  # Fallback if denominator is zero

        rw = completion.diameter / 2
        if rw <= 0:
            raise ValueError("Well radius (rw) must be positive.")
        if re <= rw:
            re = (
                1.2 * rw
            )  # Ensure re > rw, adjust if Peaceman's re is too small or zero

        # Calculate well index (Oilfield units: 0.00708 factor for md, ft, bbl/day/psi)
        k_avg = np.sqrt(kx * ky)
        wi_denominator = np.log(re / rw) + completion.skin
        if wi_denominator == 0:  # Avoid division by zero
            wi = 0.00708 * k_avg * dz / (1e-6 + completion.skin)  # Add small epsilon
        else:
            wi = 0.00708 * k_avg * dz / wi_denominator

        return wi * completion.transmissibility_factor


class MultisegmentWell(Well):
    """Multisegment well model with advanced flow modeling."""

    def __init__(
        self, name: str, well_type: WellType, heel_i: int, heel_j: int, heel_k: int
    ):
        """Initialize multisegment well."""
        super().__init__(name, well_type, heel_i, heel_j, heel_k)
        self.is_multisegment = True

        self.segment_pressure: List[float] = []
        self.segment_temperature: List[float] = []
        self.segment_flow_rates: Dict[str, List[float]] = {
            "oil": [],
            "gas": [],
            "water": [],
            "total": [],
        }
        self.segment_holdup: List[float] = []
        self.segment_flow_regime: List[str] = []

    def build_segment_topology(self):
        """Build segment topology from segments."""
        if not self.segments:
            return

        self.segments.sort(key=lambda s: s.segment_id)

        for segment in self.segments:
            if segment.inlet_segment is not None:
                if not any(
                    s.segment_id == segment.inlet_segment for s in self.segments
                ):
                    raise ValueError(
                        f"Inlet segment {segment.inlet_segment} for segment {segment.segment_id} not found"
                    )

            if segment.outlet_segment is not None:
                if not any(
                    s.segment_id == segment.outlet_segment for s in self.segments
                ):
                    raise ValueError(
                        f"Outlet segment {segment.outlet_segment} for segment {segment.segment_id} not found"
                    )

    def calculate_pressure_profile(self, fluid_properties: Dict):
        """
        Calculate pressure profile along well.

        Args:
            fluid_properties: Fluid properties dictionary
        """
        if not self.segments:
            return

        self.segment_pressure = [0.0] * len(self.segments)

        if not self.bhp:  # If BHP list is empty
            # Try to get BHP from current control if set, otherwise cannot proceed
            if self.controls and self.current_control < len(self.controls):
                current_ctrl = self.controls[self.current_control]
                if current_ctrl.control_type == ControlType.BHP:
                    self.segment_pressure[-1] = current_ctrl.target_value
                else:  # Cannot determine bottom-hole pressure
                    print(
                        f"Warning: BHP not available for well {self.name} to calculate pressure profile."
                    )
                    return
            else:
                print(
                    f"Warning: No BHP data or active control for well {self.name} to calculate pressure profile."
                )
                return
        else:  # BHP list has data
            self.segment_pressure[-1] = self.bhp[-1]

        for i in range(len(self.segments) - 2, -1, -1):
            segment = self.segments[i]

            # Find the outlet segment object
            outlet_segment_obj = None
            if segment.outlet_segment is not None:
                for seg_obj_idx, seg_obj in enumerate(self.segments):
                    if seg_obj.segment_id == segment.outlet_segment:
                        outlet_segment_obj = seg_obj
                        outlet_pressure = self.segment_pressure[seg_obj_idx]
                        break

            if outlet_segment_obj is None:
                # This case should ideally not happen if topology is correct and heel/toe is handled
                print(
                    f"Warning: Outlet segment for segment {segment.segment_id} not found or pressure not set."
                )
                continue  # Or handle as error

            dp = self._calculate_segment_pressure_drop(segment, fluid_properties)
            self.segment_pressure[i] = (
                outlet_pressure + dp
            )  # Pressure increases upwards from BHP

    def _calculate_segment_pressure_drop(
        self, segment: WellSegment, fluid_properties: Dict
    ) -> float:
        """
        Calculate pressure drop across segment. Positive for pressure loss
        against flow.

        Args:
            segment: Well segment
            fluid_properties: Fluid properties

        Returns:
            Pressure drop (psi)
        """
        if segment.pressure_drop_model == "no_pressure_drop":
            return 0.0

        fluid_density = fluid_properties.get(
            "density_avg", 62.4
        )  # lb/ft³, average density in segment
        dp_hydrostatic = (
            0.433 * fluid_density * segment.depth_change
        )  # psi; depth_change is positive if segment goes deeper

        dp_friction = 0.0  # Placeholder
        if segment.pressure_drop_model == "beggs_brill":
            dp_friction = self._beggs_brill_pressure_drop(segment, fluid_properties)
        elif segment.pressure_drop_model == "hagedorn_brown":
            dp_friction = self._hagedorn_brown_pressure_drop(segment, fluid_properties)

        return dp_hydrostatic + dp_friction  # Total pressure change (loss if positive)

    def _beggs_brill_pressure_drop(
        self, segment: WellSegment, fluid_properties: Dict
    ) -> float:
        """Calculate pressure drop using Beggs-Brill correlation."""
        return 0.0  # Placeholder

    def _hagedorn_brown_pressure_drop(
        self, segment: WellSegment, fluid_properties: Dict
    ) -> float:
        """Calculate pressure drop using Hagedorn-Brown correlation."""
        return 0.0  # Placeholder


class IntelligentWell(MultisegmentWell):
    """Intelligent well with ICD/ICV completions and downhole monitoring."""

    def __init__(
        self, name: str, well_type: WellType, heel_i: int, heel_j: int, heel_k: int
    ):
        """Initialize intelligent well."""
        super().__init__(name, well_type, heel_i, heel_j, heel_k)
        self.is_intelligent = True
        self.icd_settings: Dict[int, Dict] = {}
        self.icv_settings: Dict[int, Dict] = {}
        self.downhole_sensors: Dict[str, Dict] = {}
        self.control_strategy: Optional[callable] = None

    def add_icd(self, completion_id: int, strength: float, type_: str = "autonomous"):
        """Add inflow control device (ICD)."""
        # Find completion index by completion_id if completions are identified by an ID
        # Assuming completion_id is the index in self.completions for now
        if completion_id < 0 or completion_id >= len(self.completions):
            raise ValueError(f"Completion ID {completion_id} is out of range.")
        self.icd_settings[completion_id] = {
            "type": type_,
            "strength": strength,
            "status": "OPEN",
        }

    def add_icv(
        self, completion_id: int, positions: int = 10, current_position: int = 10
    ):
        """Add interval control valve (ICV)."""
        if completion_id < 0 or completion_id >= len(self.completions):
            raise ValueError(f"Completion ID {completion_id} is out of range.")
        self.icv_settings[completion_id] = {
            "positions": positions,
            "current_position": current_position,
            "status": "OPEN",
        }

    def add_downhole_sensor(
        self,
        name: str,
        location_segment_id: int,
        sensor_type: str,
        frequency: float = 1.0,
    ):
        """Add downhole sensor."""
        # Ensure location_segment_id is valid
        if not any(s.segment_id == location_segment_id for s in self.segments):
            raise ValueError(
                f"Segment ID {location_segment_id} for sensor {name} not found."
            )
        self.downhole_sensors[name] = {
            "segment_id": location_segment_id,
            "type": sensor_type,
            "frequency": frequency,
            "data": [],
        }

    def set_control_strategy(self, strategy_func: callable):
        """Set control strategy function."""
        self.control_strategy = strategy_func

    def update_controls(self, reservoir_state: Dict, time: float):
        """Update well controls based on strategy."""
        if self.control_strategy is None:
            return

        sensor_data = {}
        for name, sensor_info in self.downhole_sensors.items():
            # Placeholder: fetch actual sensor reading based on segment_id and
            # sensor_type. For now, just indicate data would be here
            sensor_data[name] = sensor_info["data"][-1] if sensor_info["data"] else None

        control_updates = self.control_strategy(
            self, sensor_data, reservoir_state, time
        )

        if control_updates:
            if "icv_positions" in control_updates:
                for comp_idx, position in control_updates["icv_positions"].items():
                    if comp_idx in self.icv_settings:
                        self.icv_settings[comp_idx]["current_position"] = position

            if "well_control" in control_updates:
                new_control = control_updates["well_control"]
                if isinstance(new_control, WellControl):
                    self.controls.append(new_control)
                    self.current_control = len(self.controls) - 1


class WellManager:
    """Manager for all wells in the simulation."""

    def __init__(self):
        """Initialize well manager."""
        self.wells: Dict[str, Well] = {}
        self.well_groups: Dict[str, List[str]] = {}
        self.group_controls: Dict[str, List[WellControl]] = {}

    def add_well(self, well: Well):
        """Add well to manager."""
        self.wells[well.name] = well

    def create_well_group(self, group_name: str, well_names: List[str]):
        """Create well group."""
        # Validate well_names
        for name in well_names:
            if name not in self.wells:
                raise ValueError(
                    f"Well {name} not found in manager, cannot add to group "
                    f"{group_name}."
                )
        self.well_groups[group_name] = well_names

    def add_group_control(self, group_name: str, control: WellControl):
        """Add control to well group."""
        if group_name not in self.well_groups:
            raise ValueError(f"Well group {group_name} not found.")
        if group_name not in self.group_controls:
            self.group_controls[group_name] = []
        self.group_controls[group_name].append(control)

    def initialize_wells(self, grid_properties: Dict):
        """Initialize all wells."""
        for well in self.wells.values():
            well.calculate_well_index(grid_properties)
            if isinstance(well, MultisegmentWell):
                well.build_segment_topology()

    def update_well_controls(self, time: float):
        """Update well controls based on time."""
        for well in self.wells.values():
            applicable_controls = []
            for i, control_event in enumerate(well.controls):
                if control_event.start_time <= time and (
                    control_event.end_time is None or time <= control_event.end_time
                ):
                    applicable_controls.append((i, control_event))

            if applicable_controls:
                # Sort by start_time (desc) to get the latest applicable if multiple
                # overlap
                applicable_controls.sort(key=lambda x: x[1].start_time, reverse=True)
                well.current_control = applicable_controls[0][0]

        for group_name, well_names in self.well_groups.items():
            if group_name in self.group_controls:
                applicable_group_controls = []
                for control_event in self.group_controls[group_name]:
                    if control_event.start_time <= time and (
                        control_event.end_time is None or time <= control_event.end_time
                    ):
                        applicable_group_controls.append(control_event)

                if applicable_group_controls:
                    applicable_group_controls.sort(
                        key=lambda x: x.start_time, reverse=True
                    )
                    self._apply_group_control(group_name, applicable_group_controls[0])

    def _apply_group_control(self, group_name: str, group_control: WellControl):
        """Apply group control to wells."""
        if group_name not in self.well_groups:
            return

        target_wells = [
            self.wells[name]
            for name in self.well_groups[group_name]
            if name in self.wells
        ]
        if not target_wells:
            return

        if group_control.control_type == ControlType.RATE:
            # Distribute rate among wells; simple equal distribution here
            # More complex logic could be based on PI, current rates, etc.
            num_active_wells = len([w for w in target_wells if w.status == "OPEN"])
            if num_active_wells == 0:
                return

            rate_per_well = group_control.target_value / num_active_wells

            for well in target_wells:
                if well.status == "OPEN":
                    # Create a new control instance for this well
                    # This assumes group control overrides individual well control for
                    # its duration
                    well_control = WellControl(
                        control_type=group_control.control_type,
                        target_value=rate_per_well,  # Distribute target
                        phase=group_control.phase,
                        min_bhp=group_control.min_bhp,
                        max_bhp=group_control.max_bhp,
                        start_time=group_control.start_time,  # Use group control timing
                        end_time=group_control.end_time,
                    )
                    # This logic might need refinement: does it add to existing controls,
                    # or temporarily override? For now, add and set current.
                    well.controls.append(well_control)
                    well.current_control = len(well.controls) - 1
        else:
            # For BHP, THP etc., apply target value directly to all wells in group
            for well in target_wells:
                if well.status == "OPEN":
                    well_control = WellControl(
                        control_type=group_control.control_type,
                        target_value=group_control.target_value,  # Apply same target
                        phase=group_control.phase,
                        min_bhp=group_control.min_bhp,
                        max_bhp=group_control.max_bhp,
                        start_time=group_control.start_time,
                        end_time=group_control.end_time,
                    )
                    well.controls.append(well_control)
                    well.current_control = len(well.controls) - 1
