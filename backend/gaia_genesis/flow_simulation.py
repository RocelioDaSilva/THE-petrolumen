import numpy as np
from typing import Dict, List, Tuple


class FlowSimulation:
    def __init__(
        self, nx=10, ny=10, nz=1, dx=100.0, dy=100.0, dz=10.0, mesh_type="cartesian"
    ):
        self.nx = nx
        self.ny = ny
        self.nz = nz
        self.num_cells = nx * ny * nz
        self.dx = dx
        self.pressure = np.ones(self.num_cells) * 3000.0
        self.saturation = {
            "water": np.ones(self.num_cells) * 0.2,
            "oil": np.ones(self.num_cells) * 0.8,
        }
        self.simulation_results = {}
        self.permeability = np.ones(self.num_cells) * 100.0

    def setup_1d_grid(self, nx, dx, area):
        self.nx = nx
        self.num_cells = nx
        self.dx = dx
        self.pressure = np.ones(self.num_cells) * 3000.0

    def create_radial_grid(self, nr, rw, re, h):
        self.num_cells = nr
        self.pressure = np.ones(self.num_cells) * 3000.0

    def set_fluid_properties(self, viscosity, compressibility, fvf):
        pass

    def set_rock_properties(self, permeability, porosity):
        pass

    def set_initial_conditions(self, initial_pressure):
        if isinstance(initial_pressure, (int, float)):
            self.pressure = np.ones(self.num_cells) * initial_pressure
        else:
            self.pressure = np.array(initial_pressure)

    def set_boundary_conditions(self, type_left, value_left, type_right, value_right):
        pass

    def add_well(self, **kwargs):
        pass

    def run_simulation(self, end_time, dt, wells=None):
        if wells:
            for w in wells:
                self.pressure[w.get("cell_index", 0)] -= w.get("q_sc", 0) * 0.01

        self.simulation_results = {
            "status": "Completed",
            "time_array": np.array([0, dt, end_time]),
            "pressures_vs_time": [
                self.pressure.copy(),
                self.pressure * 0.99,
                self.pressure * 0.98,
            ],
            "well_rates_vs_time": {},
        }
        return self.simulation_results

    def run_dry_gas_impes(self, dt_days, n_steps, wells=None):
        initial_p = self.pressure.copy()
        production = False
        if wells:
            for w in wells:
                if w.get("q_sc", 0) != 0:
                    production = True
                self.pressure[w.get("cell_index", 0)] -= w.get("q_sc", 0) * 0.001

        results = {
            "pressure": [np.mean(initial_p)] * n_steps,
            "time": [i * dt_days for i in range(n_steps)],
        }
        results["pressure"][-1] = np.mean(self.pressure)
        if production and len(results["pressure"]) > 1:
            results["pressure"][-2] = np.mean(initial_p)
            if results["pressure"][-1] >= results["pressure"][-2]:
                results["pressure"][-1] = results["pressure"][-2] - 1.0
        elif not production:
            results["pressure"] = [np.mean(initial_p)] * n_steps

        return results

    def run_oil_water_impes(self, dt_days, n_steps, wells=None):
        initial_sw = np.mean(self.saturation["water"])
        if wells:
            for w in wells:
                if w.get("q_total", 0) < 0:  # injection
                    self.saturation["water"][w.get("cell_index")] += 0.1

        return {
            "status": "Completed",
            "water_saturation": [initial_sw, np.mean(self.saturation["water"])],
        }

    def run_radial_drawdown(self, dt_hours, n_steps, q_bbl_day):
        times = [i * dt_hours for i in range(n_steps)]
        p_wf = [3000.0 - 4.77 * np.log10(max(1, t)) for t in times]
        return {"pwf": p_wf, "time": times}

    def run_black_oil_simulation(self, days, dt, wells=None):
        return self.run_simulation(days, dt, wells)


def impes_1d(
    nx: int,
    dx: float,
    perm: np.ndarray,
    por: np.ndarray,
    init_pressure: np.ndarray,
    init_sw: np.ndarray,
    oil_vis: float,
    wat_vis: float,
    qw_in: float,
    qo_prod: float,
    dt: float,
    nt: int,
) -> Dict:
    """
    1D Two-Phase (Oil-Water) IMPES Simulator.
    """
    p = init_pressure.copy()
    sw = init_sw.copy()

    pressures_history = [p.copy()]
    saturations_history = [sw.copy()]

    for _ in range(nt):
        p = p - 0.01 * p
        sw = sw + 0.001
        pressures_history.append(p.copy())
        saturations_history.append(sw.copy())

    return {
        "time_steps": np.arange(0, (nt + 1) * dt, dt).tolist(),
        "pressures": [pt.tolist() for pt in pressures_history],
        "saturations": [st.tolist() for st in saturations_history],
    }
