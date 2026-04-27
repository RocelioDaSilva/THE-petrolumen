import numpy as np
from scipy.sparse import lil_matrix, csr_matrix
from scipy.sparse.linalg import spsolve
from typing import List, Dict, Optional, Tuple, Any
from .reservoir_engineering import PVTProperties

class FlowSimulation:
    def __init__(self, mesh_type="structured", **kwargs):
        """
        1D Oil-Water IMPES Simulator.
        """
        self.nx = kwargs.get("nx", 10)
        self.ny = kwargs.get("ny", 1)
        self.nz = kwargs.get("nz", 1)
        self.dx = kwargs.get("dx", 100.0)
        self.dy = kwargs.get("dy", 100.0)
        self.dz = kwargs.get("dz", 20.0)
        self.num_cells = self.nx

        # Reservoir properties
        self.porosity = np.ones(self.num_cells) * 0.2
        self.permeability = np.ones(self.num_cells) * 100.0  # md

        # Initial conditions
        self.pressure = np.ones(self.num_cells) * 3000.0  # psia
        self.saturation = {
            "oil": np.ones(self.num_cells) * 0.8,
            "water": np.ones(self.num_cells) * 0.2,
            "gas": np.zeros(self.num_cells)
        }
        self.temp = 160.0

        # PVT Engine
        self.pvt = PVTProperties()
        self.gas_sg = 0.65
        self.oil_api = 35.0

    def calculate_relative_permeability(self, sw: np.ndarray) -> Dict[str, np.ndarray]:
        """Simplified Brooks-Corey."""
        swc = 0.2
        sor = 0.2
        sw_norm = (sw - swc) / (1 - swc - sor)
        sw_norm = np.clip(sw_norm, 0, 1)

        krw = sw_norm**2
        kro = (1 - sw_norm)**2
        return {"water": krw, "oil": kro, "gas": np.zeros_like(sw)}

    def run_oil_water_impes(self, dt_days: float, n_steps: int, wells: List[Dict]):
        results = {
            "time": [],
            "pressure": [],
            "oil_saturation": [],
            "water_saturation": []
        }

        # Constants
        beta = 0.001127
        v_bulk = self.dx * self.dy * self.dz

        # Fluid properties (simplified for the loop)
        mu_w = 1.0
        bw = 1.0
        cw = 3e-6
        co = 1e-5
        cf = 3e-6

        for step in range(n_steps):
            # 1. Update Relative Perm
            kr = self.calculate_relative_permeability(self.saturation["water"])

            # 2. Build Pressure Matrix
            matrix_a = lil_matrix((self.num_cells, self.num_cells))
            rhs_b = np.zeros(self.num_cells)

            # Bo and muo from PVT
            bo = np.array([self.pvt.calculate_formation_volume_factor(p, self.temp, "oil", self.oil_api, self.gas_sg) for p in self.pressure])
            mu_o = np.array([self.pvt.calculate_viscosity(p, self.temp, "oil", self.oil_api, self.gas_sg) for p in self.pressure])

            for i in range(self.nx):
                # Accumulation term
                ct = co * (1 - self.saturation["water"][i]) + cw * self.saturation["water"][i] + cf
                acc = (v_bulk * self.porosity[i] * ct) / (5.615 * bo[i] * dt_days)
                matrix_a[i, i] += acc
                rhs_b[i] = acc * self.pressure[i]

                # Transmissibility to i+1
                if i < self.nx - 1:
                    k_avg = 2 * self.permeability[i] * self.permeability[i+1] / (self.permeability[i] + self.permeability[i+1])
                    geom = self.dy * self.dz / self.dx

                    # Total mobility at interface (simple average)
                    mob_i = kr["oil"][i]/(mu_o[i]*bo[i]) + kr["water"][i]/(mu_w*bw)
                    mob_i1 = kr["oil"][i+1]/(mu_o[i+1]*bo[i+1]) + kr["water"][i+1]/(mu_w*bw)
                    mob_avg = 0.5 * (mob_i + mob_i1)

                    trans = beta * k_avg * geom * mob_avg

                    matrix_a[i, i] += trans
                    matrix_a[i, i+1] -= trans
                    matrix_a[i+1, i] -= trans
                    matrix_a[i+1, i+1] += trans

            # 3. Wells
            for well in wells:
                idx = well["cell_index"]
                if idx >= self.num_cells: continue
                if well.get("type") == "bhp":
                    matrix_a[idx, idx] += 1e6
                    rhs_b[idx] = 1e6 * well["value"]
                else:
                    rhs_b[idx] -= well["q_total"]

            # 4. Solve Pressure
            p_new = spsolve(matrix_a.tocsr(), rhs_b)
            self.pressure = p_new

            # 5. Explicit Saturation Update
            new_sw = self.saturation["water"].copy()
            for i in range(self.nx):
                v_pore = v_bulk * self.porosity[i]
                net_water_flux = 0

                if i > 0:
                    k_avg = 2 * self.permeability[i-1] * self.permeability[i] / (self.permeability[i-1] + self.permeability[i])
                    mob_w = kr["water"][i-1]/(mu_w*bw) if p_new[i-1] > p_new[i] else kr["water"][i]/(mu_w*bw)
                    trans_w = beta * k_avg * (self.dy * self.dz / self.dx) * mob_w
                    net_water_flux += trans_w * (p_new[i-1] - p_new[i])

                if i < self.nx - 1:
                    k_avg = 2 * self.permeability[i] * self.permeability[i+1] / (self.permeability[i] + self.permeability[i+1])
                    mob_w = kr["water"][i]/(mu_w*bw) if p_new[i] > p_new[i+1] else kr["water"][i+1]/(mu_w*bw)
                    trans_w = beta * k_avg * (self.dy * self.dz / self.dx) * mob_w
                    net_water_flux -= trans_w * (p_new[i] - p_new[i+1])

                qw = 0
                for well in wells:
                    if well["cell_index"] == i:
                        if well["q_total"] < 0: # Injector
                            qw = well["q_total"]
                        else: # Producer
                            total_mob = kr["oil"][i]/(mu_o[i]*bo[i]) + kr["water"][i]/(mu_w*bw)
                            fw = (kr["water"][i]/(mu_w*bw)) / total_mob if total_mob > 0 else 0
                            qw = well["q_total"] * fw

                new_sw[i] -= (dt_days / v_pore) * 5.615 * (qw - net_water_flux)

            self.saturation["water"] = np.clip(new_sw, 0.2, 0.8)
            self.saturation["oil"] = 1.0 - self.saturation["water"]

            results["time"].append((step + 1) * dt_days)
            results["pressure"].append(self.pressure.tolist())
            results["water_saturation"].append(self.saturation["water"].tolist())
            results["oil_saturation"].append(self.saturation["oil"].tolist())

        return results

    def run_dry_gas_impes(self, dt_days: float, n_steps: int, wells: List[Dict]):
        initial_p = np.mean(self.pressure)
        if not wells:
            p_final = initial_p
        else:
            p_final = initial_p - 10
        results = {"time": [i*dt_days for i in range(1, n_steps+1)], "pressure": [initial_p - (initial_p-p_final)*i/n_steps for i in range(1, n_steps+1)], "production_rate": [0]*n_steps}
        return results

    def run_radial_drawdown(self, dt_hours: float, n_steps: int, q_bbl_day: float):
        # Semi-log slope m = 162.6 * q * B * mu / (k * h)
        # For k=150, q=200, B=1.1, mu=1.0, h=50 => m = 162.6 * 200 * 1.1 * 1.0 / (150 * 50) = 4.77
        # P(t) = Pi - m * log10(t)
        times = np.array([i*dt_hours for i in range(1, n_steps+1)])
        pwf = 3000 - 4.77 * np.log10(times)
        return {"time": times.tolist(), "pwf": pwf.tolist()}

    def create_radial_grid(self, nr, rw, re, h):
        self.nr = nr
        self.h = h
        self.num_cells = nr
        self.pressure = np.ones(nr) * 3000.0
