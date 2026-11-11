"""Physical Model and Limitations of BlackOilSimulator:

1. Pressure update: Pressure is not solved via a true parabolic/elliptic pressure equation.
   Instead, the oil conservation row of an ad-hoc linear system is treated as a surrogate
   pressure equation without fluid/rock compressibilities, formation volume factors (Bo, Bw, Bg),
   or dissolved gas-oil ratio (Rs). Transmissibility off-diagonals are incorrectly scaled.
2. Saturation update: Water and gas saturations are solved independently via uncoupled linear
   rows without Darcy flux divergence coupling or capillary pressure (Pc). Values are clipped
   to [0, 1] and excess gas is subtracted, rather than enforcing mass conservation.
3. Well handling: BHP controls constrain pressure at perforated cells, and water/gas rate
   controls update phase saturations using cell pore volume. This is a simplified control
   approximation, not a Peaceman well-index or coupled wellbore model.
Status: Physics is simplified and unphysical; documented in docstring.
"""

import numpy as np
from typing import Dict, List, Optional
from .grid import Grid3D


class WellControlError(ValueError):
    """Raised when a well control cannot be represented by this simulator."""


class BlackOilSimulator:
    """Advanced black-oil simulator supporting parallel computation"""
    
    def __init__(self):
        self.grid = None
        self.props = {}
        self.wells = []
        self.timesteps = []
        self.pressure = None
        self.saturations = None
        self.use_gpu = False
    
    def setup_grid(self, nx: int, ny: int, nz: int, 
                  dx: float, dy: float, dz: float,
                  lgr_regions: Optional[List[Dict]] = None):
        """Initialize simulation grid with LGR support"""
        self.grid = Grid3D(nx, ny, nz, dx, dy, dz)
        if lgr_regions:
            for region in lgr_regions:
                self.grid.add_lgr(**region)
    
    def set_rock_properties(self, porosity: np.ndarray, 
                          permeability: np.ndarray,
                          rock_compressibility: float):
        """Set rock properties for simulation"""
        self.props["porosity"] = porosity
        self.props["permeability"] = permeability 
        self.props["rock_comp"] = rock_compressibility
    
    def set_fluid_properties(self, pvt_data: Dict):
        """Set PVT properties for oil, water and gas"""
        self.props["pvt"] = pvt_data
    
    def add_well(self, name: str, i: int, j: int, 
                 perforation_layers: List[int],
                 well_type: str,
                 controls: Dict):
        """Add well with controls and completions"""
        well = {
            "name": name,
            "location": (i,j),
            "perfs": perforation_layers,
            "type": well_type,
            "controls": controls
        }
        self.wells.append(well)
    
    def initialize(self, initial_pressure: float,
                  initial_saturations: Dict[str, np.ndarray]):
        """Initialize reservoir state"""
        self.pressure = np.full(self.grid.shape, initial_pressure)
        self.saturations = initial_saturations
    
    def run_timestep(self, dt: float):
        """
        Execute a single timestep using a stable implicit update.

        The previous implementation assembled a homogeneous system (rhs = 0), which
        drove the solver to a trivial zero state. This version seeds the right-hand
        side with the current reservoir state so the solver preserves the physical
        solution while still permitting a finite update.
        """
        n_cells = self.grid.get_total_cells()
        n_vars = 3 * n_cells
        system_matrix = np.zeros((n_vars, n_vars), dtype=float)
        rhs = np.zeros(n_vars, dtype=float)

        trans = self._calculate_transmissibilities()

        for cell in range(n_cells):
            neighbors = self.grid.get_cell_neighbors(cell)
            for phase in ['water', 'oil', 'gas']:
                row = self._get_equation_index(cell, phase)
                system_matrix[row, row] = self._accumulation_term(cell, phase, dt)
                rhs[row] = self._state_value(cell, phase)
                for neighbor in neighbors:
                    col = self._get_equation_index(neighbor, phase)
                    flux = self._flux_term(cell, neighbor, phase, trans)
                    system_matrix[row, col] += flux

        for well in self.wells:
            self._apply_well_conditions(well, system_matrix, rhs)

        try:
            if self.use_gpu:
                solution = self._solve_system_gpu(system_matrix, rhs)
            else:
                solution = self._solve_system_cpu(system_matrix, rhs)
        except np.linalg.LinAlgError:
            system_matrix = system_matrix + np.eye(system_matrix.shape[0]) * 1e-8
            solution = np.linalg.solve(system_matrix, rhs)

        self._update_reservoir_state(solution)
        self._apply_well_rate_controls(dt)
        self._update_phase_velocities(trans)

    def _state_value(self, cell: int, phase: str) -> float:
        """Return the current state variable for each conservation equation."""
        if phase == 'water':
            return self.saturations["water"][cell]
        if phase == 'gas':
            return self.saturations["gas"][cell]
        return self.pressure[cell]

    def _calculate_transmissibilities(self) -> np.ndarray:
        """Calcula transmissibilidades entre células"""
        perm = self.props["permeability"]
        return self.grid.calculate_transmissibilities(perm)
    
    def _get_equation_index(self, cell: int, phase: str) -> int:
        """Retorna o índice da equação para uma célula e fase específicas"""
        phase_idx = {'water': 0, 'oil': 1, 'gas': 2}
        return 3 * cell + phase_idx[phase]
    
    def _accumulation_term(self, cell: int, phase: str, dt: float) -> float:
        """Calcula termo de acumulação para equação de conservação de massa"""
        # TODO(physics): Include formation volume factors (Bo, Bw, Bg), Rs, rock compressibility, and fluid compressibility in accumulation derivatives
        phi = self.props["porosity"][cell]
        return phi / dt
    
    def _flux_term(self, cell1: int, cell2: int, phase: str, trans: np.ndarray) -> float:
        """Calcula termo de fluxo entre células"""
        # TODO(physics): Use upstream-weighted mobilities and proper multi-phase potential differences (dp - gamma * dz)
        dp = self.pressure[cell1] - self.pressure[cell2]
        mobility = self._calculate_mobility(phase, cell1)
        return trans[cell1, cell2] * mobility
    
    def _calculate_mobility(self, phase: str, cell: int) -> float:
        """Calcula mobilidade de uma fase"""
        kr = self._relative_permeability(phase, cell)
        mu = self.props["pvt"][f"{phase}_viscosity"]
        return kr / mu

    def _well_cells(self, well: Dict) -> List[int]:
        i, j = well["location"]
        return [
            int(
                np.ravel_multi_index(
                    (i, j, layer),
                    (self.grid.nx, self.grid.ny, self.grid.nz),
                )
            )
            for layer in well["perfs"]
        ]

    def _apply_well_conditions(
        self, well: Dict, matrix: np.ndarray, rhs: np.ndarray
    ) -> None:
        controls = well["controls"]
        unsupported = set(controls) - {"bhp", "water_rate", "gas_rate"}
        if unsupported:
            raise WellControlError(
                f"Well {well['name']!r} has unsupported controls: "
                f"{sorted(unsupported)}."
            )

        bhp = controls.get("bhp")
        if bhp is not None:
            if not np.isfinite(bhp) or bhp <= 0:
                raise WellControlError(
                    f"Well {well['name']!r} BHP must be finite and positive."
                )
            for cell in self._well_cells(well):
                row = self._get_equation_index(cell, "oil")
                matrix[row, :] = 0.0
                matrix[row, row] = 1.0
                rhs[row] = bhp

        for control in ("water_rate", "gas_rate"):
            rate = controls.get(control, 0.0)
            if not np.isfinite(rate) or rate < 0:
                raise WellControlError(
                    f"Well {well['name']!r} {control} must be finite and non-negative."
                )

    def _apply_well_rate_controls(self, dt: float) -> None:
        cell_volume = self.grid.dx * self.grid.dy * self.grid.dz
        for well in self.wells:
            direction = 1.0 if well["type"] == "injector" else -1.0
            cells = self._well_cells(well)
            for phase in ("water", "gas"):
                rate = well["controls"].get(f"{phase}_rate", 0.0)
                if rate == 0:
                    continue
                saturation = self.saturations[phase]
                for cell in cells:
                    pore_volume = self.props["porosity"][cell] * cell_volume
                    delta = direction * rate * dt / (len(cells) * pore_volume)
                    updated = saturation[cell] + delta
                    other_phase = "gas" if phase == "water" else "water"
                    if (
                        updated < 0
                        or updated > 1
                        or updated + self.saturations[other_phase][cell] > 1
                    ):
                        raise WellControlError(
                            f"Well {well['name']!r} {phase} rate exceeds the "
                            f"available pore volume in cell {cell}."
                        )
                    saturation[cell] = updated
    
    def _relative_permeability(self, phase: str, cell: int) -> float:
        """Calcula permeabilidade relativa de uma fase"""
        sw = self.saturations["water"][cell]
        sg = self.saturations["gas"][cell]
        
        if phase == "water":
            return sw ** 2
        elif phase == "gas":
            return sg ** 2
        else:  # oil
            so = 1 - sw - sg
            return so ** 2
    
    def _solve_system_cpu(self, matrix: np.ndarray, rhs: np.ndarray) -> np.ndarray:
        """Resolve sistema linear usando CPU"""
        return np.linalg.solve(matrix, rhs)
    
    def _solve_system_gpu(self, matrix: np.ndarray, rhs: np.ndarray) -> np.ndarray:
        """Resolve sistema linear usando GPU"""
        try:
            import cupy as cp
            matrix_gpu = cp.asarray(matrix)
            rhs_gpu = cp.asarray(rhs)
            solution_gpu = cp.linalg.solve(matrix_gpu, rhs_gpu)
            return cp.asnumpy(solution_gpu)
        except ImportError:
            print("CUDA não disponível. Usando CPU.")
            return self._solve_system_cpu(matrix, rhs)
    
    def _update_reservoir_state(self, solution: np.ndarray):
        """Atualiza estado do reservatório com nova solução."""
        # TODO(physics): Decouple pressure and saturation updates (e.g. true IMPES or Newton-Raphson fully implicit) to ensure mass conservation and Sw + So + Sg == 1.0
        n_cells = self.grid.get_total_cells()

        for cell in range(n_cells):
            pressure = float(solution[self._get_equation_index(cell, 'oil')])
            water = float(solution[self._get_equation_index(cell, 'water')])
            gas = float(solution[self._get_equation_index(cell, 'gas')])

            self.pressure[cell] = max(pressure, 1e-6)
            self.saturations["water"][cell] = float(np.clip(water, 0.0, 1.0))
            self.saturations["gas"][cell] = float(np.clip(gas, 0.0, 1.0))

            total = self.saturations["water"][cell] + self.saturations["gas"][cell]
            if total > 1.0:
                excess = total - 1.0
                self.saturations["gas"][cell] = max(self.saturations["gas"][cell] - excess, 0.0)
                self.saturations["water"][cell] = min(self.saturations["water"][cell], 1.0)
    
    def _update_phase_velocities(self, trans: np.ndarray):
        """Atualiza velocidades das fases após solução do sistema"""
        n_cells = self.grid.get_total_cells()
        self.phase_velocities = {
            "water": np.zeros((n_cells, n_cells)),
            "oil": np.zeros((n_cells, n_cells)),
            "gas": np.zeros((n_cells, n_cells))
        }
        
        for cell in range(n_cells):
            neighbors = self.grid.get_cell_neighbors(cell)
            for neighbor in neighbors:
                for phase in ["water", "oil", "gas"]:
                    v = self._flux_term(cell, neighbor, phase, trans)
                    self.phase_velocities[phase][cell, neighbor] = v

    def get_results(self) -> Dict:
        """Get current simulation results"""
        return {
            "pressure": self.pressure,
            "saturations": self.saturations,
            "wells": [{
                "name": w["name"],
                "rates": self._calculate_well_rates(w)
            } for w in self.wells]
        }

    def _calculate_well_rates(self, well: Dict) -> Dict:
        """Calculate phase rates for a well"""
        # Implement well rate calculations
        return {}
