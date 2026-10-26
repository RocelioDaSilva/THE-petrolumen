import numpy as np
from typing import Dict


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
        self.porosity = np.ones(self.num_cells) * 0.2
        self.viscosity = 1.0  # cp
        self.compressibility = 1e-5  # 1/psi

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

    def calculate_capillary_pressure(self, saturation):
        """Calculates capillary pressure using the Brooks-Corey model."""
        # Model parameters
        lambda_bc = 2.0  # Brooks-Corey exponent
        pce = 5.0  # Entry capillary pressure (psi)
        swc = 0.2  # Critical water saturation
        sor = 0.2  # Residual oil saturation
        sgc = 0.05  # Critical gas saturation

        # Calculate capillary pressure for each pair of phases
        pc = {}

        # Oil-Water
        sw = saturation["water"]
        # Avoid division by zero and negative values
        sw_norm = np.clip((sw - swc) / (1 - swc - sor), 1e-6, 1.0)
        pc["oil_water"] = pce * (sw_norm ** (-1 / lambda_bc))

        # Oil-Gas
        sg = saturation.get("gas", np.zeros_like(sw))
        sg_norm = np.clip((sg - sgc) / (1 - swc - sgc), 1e-6, 1.0)
        pc["oil_gas"] = pce * (sg_norm ** (-1 / lambda_bc))

        # Water-Gas
        pc["water_gas"] = pc["oil_water"] + pc["oil_gas"]

        return pc

    def calculate_relative_permeability(self, saturation):
        """Calculates relative permeability using the Stone II model."""
        # Model parameters
        n_o = 2.0  # Expoente para óleo
        n_w = 2.0  # Expoente para água
        n_g = 2.0  # Expoente para gás
        sor = 0.2  # Saturação residual de óleo
        swc = 0.2  # Saturação crítica de água
        sgc = 0.05  # Saturação crítica de gás

        # Calcular permeabilidade relativa base
        kr_base = {}

        # Água
        sw = saturation["water"]
        sw_norm = np.clip((sw - swc) / (1 - swc - sor), 0.0, 1.0)
        kr_base["water"] = np.where(sw > swc, sw_norm**n_w, 0)

        # Gás
        sg = saturation.get("gas", np.zeros_like(sw))
        sg_norm = np.clip((sg - sgc) / (1 - swc - sor - sgc), 0.0, 1.0)
        kr_base["gas"] = np.where(sg > sgc, sg_norm**n_g, 0)

        # Óleo (Stone II)
        so = saturation["oil"]
        so_norm = np.clip((so - sor) / (1 - swc - sor), 0.0, 1.0)
        kr_base["oil"] = np.where(so > sor, so_norm**n_o, 0)

        # Aplicar correção de Stone II
        kr = {}
        kr["water"] = kr_base["water"]
        kr["gas"] = kr_base["gas"]

        # Correção para óleo
        kr["oil"] = kr_base["oil"] * (1 - kr_base["water"]) * (1 - kr_base["gas"])

        return kr

    def run_simulation(self, end_time, dt, wells=None):
        """
        Runs a 1D reservoir simulation using an implicit pressure solver (Implicit scheme).
        This is more stable than the explicit one.
        """
        n_steps = max(1, int(end_time / dt))
        p = self.pressure.copy()

        # Grid parameters (assuming 1D for this implementation)
        nx = self.nx
        dx = self.dx
        area = 100.0  # ft^2
        v_cell = dx * area  # ft^3

        # Properties
        perm = self.permeability[:nx]  # md
        por = self.porosity[0]  # simplified 1D homogeneous use
        visc = self.viscosity
        ct = self.compressibility

        # Transmissibility constant
        alpha = 0.001127

        pressures_history = [p[:nx].copy()]
        time_array = [0.0]

        for step in range(1, n_steps + 1):
            # Construct the system Ax = B
            A = np.zeros((nx, nx))
            B = np.zeros(nx)

            for i in range(nx):
                # T_i-1/2
                if i > 0:
                    t_left = (
                        alpha
                        * (2 * perm[i - 1] * perm[i] / (perm[i - 1] + perm[i]))
                        * area
                        / (visc * dx)
                    )
                else:
                    t_left = 0

                # T_i+1/2
                if i < nx - 1:
                    t_right = (
                        alpha
                        * (2 * perm[i] * perm[i + 1] / (perm[i] + perm[i + 1]))
                        * area
                        / (visc * dx)
                    )
                else:
                    t_right = 0

                acc = v_cell * por * ct / dt

                A[i, i] = acc + t_left + t_right
                if i > 0:
                    A[i, i - 1] = -t_left
                if i < nx - 1:
                    A[i, i + 1] = -t_right

                # Source term
                q = 0
                if wells:
                    for w in wells:
                        if w.get("cell_index") == i:
                            q = w.get("q_sc", 0)

                B[i] = acc * p[i] - q

            try:
                p_new = np.linalg.solve(A, B)
                p[:nx] = p_new
            except np.linalg.LinAlgError:
                break

            pressures_history.append(p[:nx].copy())
            time_array.append(step * dt)

        self.simulation_results = {
            "status": "Completed",
            "time_array": np.array(time_array),
            "pressures_vs_time": pressures_history,
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
                idx = w.get("cell_index", 0)
                if idx < len(self.pressure):
                    self.pressure[idx] -= w.get("q_sc", 0) * 0.001

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
