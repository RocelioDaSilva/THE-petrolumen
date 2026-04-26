import numpy as np
from scipy.sparse import lil_matrix, csr_matrix
from scipy.sparse.linalg import spsolve
import matplotlib.pyplot as plt
from typing import List, Dict, Optional, Tuple
from .geology.mesh import Mesh
from .reservoir_engineering import PVTProperties
import pyvista as pv


class FlowSimulation:
    def __init__(self, mesh_type="structured", **kwargs):
        """
        Inicializa o simulador de fluxo.
        """
        self.mesh_type = mesh_type
        self.mesh = Mesh()
        if mesh_type == "structured":
            # Default values if not provided
            self.nx = kwargs.get("nx", 10)
            self.ny = kwargs.get("ny", 10)
            self.nz = kwargs.get("nz", 1)
            self.dx = kwargs.get("dx", 100.0)
            self.dy = kwargs.get("dy", 100.0)
            self.dz = kwargs.get("dz", 20.0)
            self.mesh.create_structured_mesh(
                self.nx, self.ny, self.nz, self.dx, self.dy, self.dz
            )
            self.num_cells = len(self.mesh.cells)
        elif mesh_type == "radial":
            # Radial grid is initialized via create_radial_grid
            self.num_cells = 0
        else:
            self.mesh.create_unstructured_mesh(**kwargs)
            self.num_cells = len(self.mesh.cells)

        # Inicializar propriedades do reservatório
        self.porosity = np.ones(self.num_cells) * 0.2
        self.permeability = np.ones(self.num_cells) * 100.0  # md
        self.depth = np.zeros(self.num_cells)

        # Inicializar condições iniciais
        self.pressure = np.ones(self.num_cells) * 3000.0  # psia
        self.temperature = np.ones(self.num_cells) * 180.0  # °F
        self.saturation = {
            "oil": np.zeros(self.num_cells),
            "water": np.zeros(self.num_cells),
            "gas": np.ones(self.num_cells),
        }

        # PVT Engine
        self.pvt = PVTProperties()
        self.gas_sg = 0.65
        self.oil_api = 35.0
        self.water_sg = 1.0

        # Inicializar composição para simulação composicional
        self.composition = None

        # Inicializar propriedades térmicas
        self.rock_heat_capacity = 0.2  # Btu/lb-°F
        self.rock_density = 165  # lb/ft³
        self.fluid_heat_capacity = {"oil": 0.5, "water": 1.0, "gas": 0.5}

        # Inicializar propriedades de interação entre fases
        self.interfacial_tension = {
            "oil_water": 30.0,  # dynes/cm
            "oil_gas": 20.0,
            "water_gas": 50.0,
        }
        self.contact_angle = {
            "oil_water": 30.0,  # graus
            "oil_gas": 0.0,
            "water_gas": 0.0,
        }
        self.capillary_pressure = None
        self.relative_permeability = None

        # Inicializar propriedades de empuxo
        self.drive_mechanisms = {
            "gas_cap": False,
            "aquifer": False,
            "solution_gas": False,
        }
        self.gas_cap_properties = {
            "initial_pressure": 3000,  # psia
            "initial_gas_saturation": 0.8,
            "gas_oil_contact": None,  # profundidade do contato gás-óleo
            "gas_cap_volume": None,  # volume do cap de gás
        }
        self.aquifer_properties = {
            "type": "pot",  # pot, fetkovich, carter-tracy
            "initial_pressure": 3000,  # psia
            "water_oil_contact": None,  # profundidade do contato água-óleo
            "aquifer_volume": None,  # volume do aquífero
            "aquifer_compressibility": 3e-6,  # 1/psi
            "water_compressibility": 3e-6,  # 1/psi
            "aquifer_porosity": 0.2,
            "aquifer_permeability": 100,  # md
        }
        self.solution_gas_properties = {
            "initial_gas_oil_ratio": 500,  # scf/STB
            "bubble_point_pressure": 2500,  # psia
            "solution_gas_oil_ratio": None,  # função de pressão
        }

    def set_reservoir_properties(self, porosity, permeability, depth):
        """Define propriedades do reservatório."""
        self.porosity = porosity
        self.permeability = permeability
        self.depth = depth

    def set_initial_conditions(self, pressure, temperature, saturation):
        """Define condições iniciais."""
        self.pressure = pressure
        self.temperature = temperature
        self.saturation = saturation

    def set_pvt_data(self, pvt_data):
        """Define dados PVT."""
        self.pvt_data = pvt_data

    def set_composition(self, composition):
        """Define composição para simulação composicional."""
        self.composition = composition

    def set_phase_interaction_properties(
        self, interfacial_tension=None, contact_angle=None
    ):
        """Define propriedades de interação entre fases."""
        if interfacial_tension:
            self.interfacial_tension.update(interfacial_tension)
        if contact_angle:
            self.contact_angle.update(contact_angle)

    def calculate_capillary_pressure(self, saturation):
        """Calcula pressão capilar usando modelo de Brooks-Corey."""
        # Parâmetros do modelo
        lambda_bc = 2.0  # Expoente de Brooks-Corey
        pce = 5.0  # Pressão capilar de entrada (psi)

        # Calcular pressão capilar para cada par de fases
        pc = {}

        # Óleo-Água
        sw = saturation["water"]
        sw_norm = (sw - 0.2) / (1 - 0.2 - 0.2)  # Normalizar saturação
        pc["oil_water"] = pce * (sw_norm ** (-1 / lambda_bc))

        # Óleo-Gás
        sg = saturation["gas"]
        sg_norm = (sg - 0.05) / (1 - 0.2 - 0.05)  # Normalizar saturação
        pc["oil_gas"] = pce * (sg_norm ** (-1 / lambda_bc))

        # Água-Gás
        pc["water_gas"] = pc["oil_water"] + pc["oil_gas"]

        return pc

    def calculate_relative_permeability(self, saturation):
        """Calcula permeabilidade relativa usando modelo de Stone II."""
        # Parâmetros do modelo
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
        sw_norm = (sw - swc) / (1 - swc - sor)
        kr_base["water"] = np.where(sw > swc, sw_norm**n_w, 0)

        # Gás
        sg = saturation["gas"]
        sg_norm = (sg - sgc) / (1 - swc - sor - sgc)
        kr_base["gas"] = np.where(sg > sgc, sg_norm**n_g, 0)

        # Óleo (Stone II)
        so = saturation["oil"]
        so_norm = (so - sor) / (1 - swc - sor)
        kr_base["oil"] = np.where(so > sor, so_norm**n_o, 0)

        # Aplicar correção de Stone II
        kr = {}
        kr["water"] = kr_base["water"]
        kr["gas"] = kr_base["gas"]

        # Correção para óleo
        kr["oil"] = kr_base["oil"] * (1 - kr_base["water"]) * (1 - kr_base["gas"])

        return kr

    def calculate_phase_mobility(self, kr, mu):
        """Calcula mobilidade de cada fase."""
        return {phase: kr[phase] / mu[phase] for phase in kr.keys()}

    def calculate_phase_velocity(self, pressure, mobility, gravity):
        """Calcula velocidade de cada fase usando lei de Darcy generalizada."""
        # Calcular gradiente de pressão
        grad_p = np.gradient(pressure)

        # Calcular velocidade para cada fase
        velocity = {}
        for phase in mobility.keys():
            # Termo de pressão
            v_p = -mobility[phase] * grad_p

            # Termo gravitacional
            v_g = mobility[phase] * gravity

            # Velocidade total
            velocity[phase] = v_p + v_g

        return velocity

    def calculate_phase_transfer(self, pressure, temperature, composition):
        """Calcula transferência de massa entre fases."""
        # Implementar cálculo de transferência de massa
        # Usar equação de estado (ex: Peng-Robinson)
        pass

    def calculate_pvt_properties(self, pressure, temperature):
        """Calcula propriedades PVT usando interpolação."""
        if self.pvt_data is None:
            raise ValueError("Dados PVT não definidos")

        # Interpolar propriedades
        pvt = {}
        for prop in ["Bo", "Bg", "Bw", "Rs", "Rsw", "muo", "mug", "muw"]:
            if prop in self.pvt_data.columns:
                f = interp1d(self.pvt_data["pressure"], self.pvt_data[prop])
                pvt[prop] = f(pressure)

        return pvt

    def calculate_compositional_properties(self, pressure, temperature):
        """Calcula propriedades para simulação composicional."""
        if self.composition is None:
            raise ValueError("Composição não definida")

        # Implementar cálculo de propriedades composicionais
        # Usar equação de estado (ex: Peng-Robinson)
        pass

    def calculate_thermal_properties(self, pressure, temperature):
        """Calcula propriedades térmicas."""
        # Calcular condutividade térmica
        k_rock = 1.5  # Btu/ft-dia-°F
        k_fluid = {"oil": 0.1, "water": 0.3, "gas": 0.05}

        # Calcular capacidade térmica
        cp = {
            "rock": self.rock_heat_capacity * self.rock_density,
            "oil": self.fluid_heat_capacity["oil"] * 50,  # lb/ft³
            "water": self.fluid_heat_capacity["water"] * 62.4,
            "gas": self.fluid_heat_capacity["gas"] * 0.1,
        }

        return k_rock, k_fluid, cp

    def update_phase_saturation(self, velocity, dt):
        """Atualiza saturação das fases usando equação de continuidade."""
        # Calcular divergência do fluxo
        div_flux = {}
        for phase in velocity.keys():
            div_flux[phase] = np.divergence(velocity[phase])

        # Atualizar saturação
        for phase in self.saturation.keys():
            self.saturation[phase] += dt * div_flux[phase]

        # Normalizar saturações
        total_sat = sum(self.saturation.values())
        for phase in self.saturation.keys():
            self.saturation[phase] /= total_sat

    def set_drive_mechanism(self, mechanism, properties=None):
        """
        Configura mecanismo de empuxo.

        Args:
            mechanism (str): 'gas_cap', 'aquifer', ou 'solution_gas'
            properties (dict): Propriedades específicas do mecanismo
        """
        if mechanism in self.drive_mechanisms:
            self.drive_mechanisms[mechanism] = True
            if properties:
                if mechanism == "gas_cap":
                    self.gas_cap_properties.update(properties)
                elif mechanism == "aquifer":
                    self.aquifer_properties.update(properties)
                elif mechanism == "solution_gas":
                    self.solution_gas_properties.update(properties)

    def calculate_gas_cap_drive(self, pressure, saturation):
        """Calcula efeito do empuxo por cap de gás."""
        if not self.drive_mechanisms["gas_cap"]:
            return 0

        # Calcular pressão no cap de gás
        # goc_depth = self.gas_cap_properties["gas_oil_contact"] # F841: Unused
        goc_pressure = self.gas_cap_properties["initial_pressure"]

        # Calcular expansão do gás
        z_initial = self.calculate_z_factor(goc_pressure, self.temperature)
        z_current = self.calculate_z_factor(pressure, self.temperature)

        # Calcular volume de gás expandido
        gas_expansion = (z_initial / z_current) * (pressure / goc_pressure)

        # Calcular influxo de gás
        gas_influx = self.gas_cap_properties["gas_cap_volume"] * (gas_expansion - 1)

        return gas_influx

    def calculate_aquifer_drive(self, pressure, time):
        """Calcula efeito do empuxo por aquífero."""
        if not self.drive_mechanisms["aquifer"]:
            return 0

        aquifer_type = self.aquifer_properties["type"]

        if aquifer_type == "pot":
            # Modelo de aquífero pot
            c_t = (
                self.aquifer_properties["aquifer_compressibility"]
                + self.aquifer_properties["water_compressibility"]
            )
            dp = self.aquifer_properties["initial_pressure"] - pressure
            water_influx = self.aquifer_properties["aquifer_volume"] * c_t * dp

        elif aquifer_type == "fetkovich":
            # Modelo de aquífero de Fetkovich
            # Implementar modelo de Fetkovich
            pass

        elif aquifer_type == "carter-tracy":
            # Modelo de aquífero de Carter-Tracy
            # Implementar modelo de Carter-Tracy
            pass

        return water_influx

    def calculate_solution_gas_drive(self, pressure, saturation):
        """Calcula efeito do empuxo por gás em solução."""
        if not self.drive_mechanisms["solution_gas"]:
            return 0

        # Calcular razão gás-óleo em solução
        if pressure >= self.solution_gas_properties["bubble_point_pressure"]:
            rs = self.solution_gas_properties["initial_gas_oil_ratio"]
        else:
            # Interpolar Rs da tabela PVT
            rs = self.interpolate_pvt_property("Rs", pressure)

        # Calcular gás liberado
        rs_initial = self.solution_gas_properties["initial_gas_oil_ratio"]
        gas_liberated = (rs_initial - rs) * saturation["oil"]

        return gas_liberated

    def calculate_z_factor(self, pressure, temperature):
        """Calcula fator Z usando correlação de Hall-Yarborough."""
        # Implementar correlação de Hall-Yarborough
        # Por enquanto, retorna valor constante
        return 0.9

    def interpolate_pvt_property(self, property_name, pressure):
        """Interpola propriedade PVT para uma dada pressão."""
        if self.pvt_data is None:
            return None

        if property_name in self.pvt_data.columns:
            f = interp1d(self.pvt_data["pressure"], self.pvt_data[property_name])
            return f(pressure)
        return None

    def create_radial_grid(self, nr, rw, re, h, dtheta=360):
        """Cria uma malha radial simplificada para testes de poço."""
        # dr calculation (logarithmic spacing)
        r = np.logspace(np.log10(rw), np.log10(re), nr + 1)
        self.r_centers = 0.5 * (r[:-1] + r[1:])
        self.dr = np.diff(r)
        self.nr = nr
        self.h = h
        self.num_cells = nr

        # Reset properties for nr cells
        self.porosity = np.ones(nr) * 0.2
        self.permeability = np.ones(nr) * 100.0
        self.pressure = np.ones(nr) * 3000.0
        self.saturation = {"oil": np.ones(nr), "water": np.zeros(nr), "gas": np.zeros(nr)}

    def run_radial_drawdown(self, dt_hours: float, n_steps: int, q_bbl_day: float):
        """Simulação de drawdown em malha radial (monofásico óleo)."""
        results = {"time": [], "pwf": [], "pressure_profile": []}

        # Field units constants
        beta = 0.001127
        dt = dt_hours / 24.0 # hours to days

        for step in range(n_steps):
            # Matrix for radial flow
            matrix_a = lil_matrix((self.nr, self.nr))
            rhs_b = np.zeros(self.nr)

            # PVT (Simplified constant for drawdown)
            mu = 1.0; bo = 1.1; ct = 1e-5

            for i in range(self.nr):
                # Bulk volume of shell
                r_outer = self.r_centers[i] + self.dr[i]/2
                r_inner = self.r_centers[i] - self.dr[i]/2
                v_bulk = np.pi * (r_outer**2 - r_inner**2) * self.h

                acc = (v_bulk * self.porosity[i] * ct) / (5.615 * bo * dt)
                matrix_a[i, i] += acc
                rhs_b[i] = acc * self.pressure[i]

                # Transmissibility to neighbor i+1
                if i < self.nr - 1:
                    r_interface = r_outer
                    area = 2 * np.pi * r_interface * self.h
                    dist = self.r_centers[i+1] - self.r_centers[i]
                    k_avg = 2 * self.permeability[i] * self.permeability[i+1] / (self.permeability[i] + self.permeability[i+1])

                    trans = beta * k_avg * area / (mu * bo * dist)

                    matrix_a[i, i] += trans
                    matrix_a[i, i+1] -= trans
                    matrix_a[i+1, i] -= trans
                    matrix_a[i+1, i+1] += trans

            # Well at i=0
            rhs_b[0] -= q_bbl_day

            self.pressure = spsolve(matrix_a.tocsr(), rhs_b)
            results["time"].append((step+1) * dt_hours)
            results["pwf"].append(self.pressure[0])

        return results

    def run_oil_water_impes(self, dt_days: float, n_steps: int, wells: List[Dict]):
        """
        Executa simulação de óleo e água usando IMPES.
        Implicit Pressure, Explicit Saturation.
        """
        results = {
            "time": [],
            "pressure": [],
            "oil_saturation": [],
            "water_saturation": [],
            "oil_rate": [],
            "water_rate": []
        }

        for step in range(n_steps):
            # 1. Update PVT and Relative Permeability
            # For simplicity, using constant Bw and muw for now, but Bo and muo dynamic
            bo = np.array([self.pvt.calculate_formation_volume_factor(p, self.temperature[0], "oil", api_gravity=self.oil_api, gas_specific_gravity=self.gas_sg) for p in self.pressure])
            mu_o = np.array([self.pvt.calculate_viscosity(p, self.temperature[0], "oil", api_gravity=self.oil_api, gas_specific_gravity=self.gas_sg) for p in self.pressure])

            bw = 1.03 # Constant water FVF
            mu_w = 0.5 # Constant water viscosity (cp)

            kr = self.calculate_relative_permeability(self.saturation)

            # 2. Build Pressure Matrix (Total Transmissibility)
            matrix_a = lil_matrix((self.num_cells, self.num_cells))
            rhs_b = np.zeros(self.num_cells)
            beta = 0.001127

            for i in range(self.nx):
                for j in range(self.ny):
                    idx = i + j * self.nx

                    neighbors = []
                    if i < self.nx - 1: neighbors.append((idx + 1, self.dy * self.dz / self.dx))
                    if j < self.ny - 1: neighbors.append((idx + self.nx, self.dx * self.dz / self.dy))

                    for idx_n, geom_factor in neighbors:
                        # Harmonic average of k
                        k_avg = 2 * self.permeability[idx] * self.permeability[idx_n] / (self.permeability[idx] + self.permeability[idx_n])

                        # Total mobility at interface (upstream weighting)
                        # Simplified: use average of mobility for now
                        mob_idx = kr["oil"][idx]/(mu_o[idx]*bo[idx]) + kr["water"][idx]/(mu_w*bw)
                        mob_n = kr["oil"][idx_n]/(mu_o[idx_n]*bo[idx_n]) + kr["water"][idx_n]/(mu_w*bw)
                        mob_avg = 0.5 * (mob_idx + mob_n)

                        trans = beta * k_avg * geom_factor * mob_avg

                        matrix_a[idx, idx] += trans
                        matrix_a[idx, idx_n] -= trans
                        matrix_a[idx_n, idx] -= trans
                        matrix_a[idx_n, idx_n] += trans

            # 3. Accumulation and Well Terms
            # Simplified compressibility
            co = 1e-5
            cw = 3e-6
            cf = 3e-6

            for idx in range(self.num_cells):
                v_bulk = self.dx * self.dy * self.dz
                ct = co * self.saturation["oil"][idx] + cw * self.saturation["water"][idx] + cf
                acc = (v_bulk * self.porosity[idx] * ct) / (5.615 * dt_days)

                matrix_a[idx, idx] += acc
                rhs_b[idx] = acc * self.pressure[idx]

            for well in wells:
                w_idx = well["cell_index"]
                rhs_b[w_idx] -= well["q_total"] # Total reservoir rate

            # 4. Solve Pressure
            p_new = spsolve(matrix_a.tocsr(), rhs_b)

            # 5. Explicit Saturation Update (Water Phase)
            # Sw(n+1) = Sw(n) + dt/(V*phi) * [ Sum(Tw*(Pn - Pi)) - qw*Bw ]
            new_sw = self.saturation["water"].copy()
            for i in range(self.nx):
                for j in range(self.ny):
                    idx = i + j * self.nx
                    v_pore = (self.dx * self.dy * self.dz) * self.porosity[idx]

                    net_water_flux = 0

                    # Sum fluxes from neighbors
                    neighbor_indices = []
                    if i > 0: neighbor_indices.append((idx - 1, self.dy * self.dz / self.dx))
                    if i < self.nx - 1: neighbor_indices.append((idx + 1, self.dy * self.dz / self.dx))
                    if j > 0: neighbor_indices.append((idx - self.nx, self.dx * self.dz / self.dy))
                    if j < self.ny - 1: neighbor_indices.append((idx + self.nx, self.dx * self.dz / self.dy))

                    for idx_n, geom_factor in neighbor_indices:
                        k_avg = 2 * self.permeability[idx] * self.permeability[idx_n] / (self.permeability[idx] + self.permeability[idx_n])

                        # Upstream weighting for water mobility
                        if p_new[idx_n] > p_new[idx]:
                            # Flow into cell idx
                            mob_w = kr["water"][idx_n] / (mu_w * bw)
                        else:
                            # Flow out of cell idx
                            mob_w = kr["water"][idx] / (mu_w * bw)

                        water_trans = beta * k_avg * geom_factor * mob_w
                        net_water_flux += water_trans * (p_new[idx_n] - p_new[idx])

                    # Add well term for water (if it's an injector or producer)
                    # For now, assume production wells produce water based on fractional flow
                    qw = 0
                    for well in wells:
                        if well["cell_index"] == idx:
                            if well["q_total"] > 0:
                                # Producer
                                fw = (kr["water"][idx] / (mu_w * bw)) / (
                                    kr["oil"][idx] / (mu_o[idx] * bo[idx])
                                    + kr["water"][idx] / (mu_w * bw)
                                )
                                qw = well["q_total"] * fw
                            else:
                                # Injector (all water)
                                qw = well["q_total"]

                    new_sw[idx] += (dt_days / v_pore) * (5.615 * (net_water_flux - qw))

            self.pressure = p_new
            self.saturation["water"] = np.clip(new_sw, 0.2, 0.8) # Clipped to Swc and 1-Sor
            self.saturation["oil"] = 1.0 - self.saturation["water"]

            results["time"].append((step + 1) * dt_days)
            results["pressure"].append(np.mean(self.pressure))
            results["oil_saturation"].append(np.mean(self.saturation["oil"]))
            results["water_saturation"].append(np.mean(self.saturation["water"]))

        return results

    def run_dry_gas_impes(self, dt_days: float, n_steps: int, wells: List[Dict]):
        """
        Executa simulação de gás seco usando IMPES (Implicit Pressure).
        """
        results = {
            "time": [],
            "pressure": [],
            "production_rate": []
        }

        for step in range(n_steps):
            # 1. Update PVT Properties (Z, Bg, Viscosity)
            z = np.array([self.pvt.calculate_z_factor(p, self.temperature[0], self.gas_sg) for p in self.pressure])
            bg = np.array([self.pvt.calculate_formation_volume_factor(p, self.temperature[0], "gas", gas_specific_gravity=self.gas_sg) for p in self.pressure])
            mu_g = np.array([self.pvt.calculate_viscosity(p, self.temperature[0], "gas", gas_specific_gravity=self.gas_sg) for p in self.pressure])

            # 2. Build Transmissibility Matrix (T)
            # T = 0.001127 * k * A / (mu * B * L)
            matrix_a = lil_matrix((self.num_cells, self.num_cells))
            rhs_b = np.zeros(self.num_cells)

            # Transmissibility constant (field units)
            beta = 0.001127

            for i in range(self.nx):
                for j in range(self.ny):
                    idx = i + j * self.nx

                    # Connection to right (i+1)
                    if i < self.nx - 1:
                        idx_r = (i + 1) + j * self.nx
                        # Harmonic average of k
                        k_avg = 2 * self.permeability[idx] * self.permeability[idx_r] / (self.permeability[idx] + self.permeability[idx_r])
                        trans = beta * k_avg * (self.dy * self.dz) / (mu_g[idx] * bg[idx] * self.dx)

                        matrix_a[idx, idx] += trans
                        matrix_a[idx, idx_r] -= trans
                        matrix_a[idx_r, idx] -= trans
                        matrix_a[idx_r, idx_r] += trans

                    # Connection to top (j+1)
                    if j < self.ny - 1:
                        idx_t = i + (j + 1) * self.nx
                        k_avg = 2 * self.permeability[idx] * self.permeability[idx_t] / (self.permeability[idx] + self.permeability[idx_t])
                        trans = beta * k_avg * (self.dx * self.dz) / (mu_g[idx] * bg[idx] * self.dy)

                        matrix_a[idx, idx] += trans
                        matrix_a[idx, idx_t] -= trans
                        matrix_a[idx_t, idx] -= trans
                        matrix_a[idx_t, idx_t] += trans

            # 3. Add Accumulation Term (V/dt * d(phi/B)/dP)
            # Simplified: V * phi * c_t / (B * dt)
            for idx in range(self.num_cells):
                v_bulk = self.dx * self.dy * self.dz
                c_g = self.pvt.calculate_gas_compressibility(self.pressure[idx], self.temperature[0], self.gas_sg)
                acc = (v_bulk * self.porosity[idx] * c_g) / (5.615 * bg[idx] * dt_days)

                matrix_a[idx, idx] += acc
                rhs_b[idx] = acc * self.pressure[idx]

            # 4. Add Well Terms (Sink/Source)
            total_q = 0
            for well in wells:
                w_idx = well["cell_index"]
                q_sc = well["q_sc"] # scf/day
                rhs_b[w_idx] -= q_sc / 1000.0 # Convert to Mscf/day if Bg units match
                total_q += q_sc

            # 5. Solve for P(n+1)
            p_new = spsolve(matrix_a.tocsr(), rhs_b)
            self.pressure = p_new

            results["time"].append((step + 1) * dt_days)
            results["pressure"].append(np.mean(self.pressure))
            results["production_rate"].append(total_q)

        return results

    def run_compositional_simulation(self, dt, n_steps):
        """
        Executa simulação composicional.

        Args:
            dt (float): Passo de tempo
            n_steps (int): Número de passos
        """
        results = {
            "time": [],
            "pressure": [],
            "temperature": [],
            "saturation": {"oil": [], "water": [], "gas": []},
            "composition": [],
            "production": {"oil": [], "water": [], "gas": []},
        }

        for step in range(n_steps):
            # Calcular pressão capilar
            _ = self.calculate_capillary_pressure(self.saturation)  # pc F841: Unused

            # Calcular permeabilidade relativa
            kr = self.calculate_relative_permeability(self.saturation)

            # Calcular propriedades composicionais
            pvt = self.calculate_compositional_properties(
                self.pressure, self.temperature
            )

            # Calcular transferência de massa entre fases
            phase_transfer = self.calculate_phase_transfer(
                self.pressure, self.temperature, self.composition
            )

            # Calcular mobilidade
            mobility = self.calculate_phase_mobility(kr, pvt)

            # Calcular velocidade das fases
            gravity = 32.2  # ft/s²
            velocity = self.calculate_phase_velocity(self.pressure, mobility, gravity)

            # Atualizar saturação
            self.update_phase_saturation(velocity, dt)

            # Atualizar composição
            self.update_compositional_variables(phase_transfer)

            # Calcular produção
            production = self.calculate_compositional_production(pvt)

            # Atualizar resultados
            results["time"].append(step * dt)
            results["pressure"].append(self.pressure.copy())
            results["temperature"].append(self.temperature.copy())
            for phase in ["oil", "water", "gas"]:
                results["saturation"][phase].append(self.saturation[phase].copy())
            results["composition"].append(self.composition.copy())
            for phase in ["oil", "water", "gas"]:
                results["production"][phase].append(production[phase])

        return results

    def run_thermal_simulation(self, dt, n_steps):
        """
        Executa simulação térmica.

        Args:
            dt (float): Passo de tempo
            n_steps (int): Número de passos
        """
        results = {
            "time": [],
            "pressure": [],
            "temperature": [],
            "saturation": {"oil": [], "water": [], "gas": []},
            "production": {"oil": [], "water": [], "gas": []},
        }

        for step in range(n_steps):
            # Calcular pressão capilar
            _ = self.calculate_capillary_pressure(self.saturation)  # pc F841: Unused

            # Calcular permeabilidade relativa
            kr = self.calculate_relative_permeability(self.saturation)

            # Calcular propriedades térmicas
            k_rock, k_fluid, cp = self.calculate_thermal_properties(
                self.pressure, self.temperature
            )

            # Calcular propriedades PVT
            pvt = self.calculate_pvt_properties(self.pressure, self.temperature)

            # Calcular mobilidade
            mobility = self.calculate_phase_mobility(kr, pvt)

            # Calcular velocidade das fases
            gravity = 32.2  # ft/s²
            velocity = self.calculate_phase_velocity(self.pressure, mobility, gravity)

            # Atualizar saturação
            self.update_phase_saturation(velocity, dt)

            # Atualizar temperatura
            self.update_thermal_variables(velocity, k_rock, k_fluid, cp)

            # Calcular produção
            production = self.calculate_thermal_production(pvt)

            # Atualizar resultados
            results["time"].append(step * dt)
            results["pressure"].append(self.pressure.copy())
            results["temperature"].append(self.temperature.copy())
            for phase in ["oil", "water", "gas"]:
                results["saturation"][phase].append(self.saturation[phase].copy())
                results["production"][phase].append(production[phase])

        return results

    def plot_results(self, results):
        """Plota resultados da simulação."""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        # Pressão
        axes[0, 0].plot(results["time"], [np.mean(p) for p in results["pressure"]])
        axes[0, 0].set_title("Pressão Média")
        axes[0, 0].set_xlabel("Tempo")
        axes[0, 0].set_ylabel("Pressão (psia)")

        # Saturação
        for phase in ["oil", "water", "gas"]:
            axes[0, 1].plot(
                results["time"],
                [np.mean(s) for s in results["saturation"][phase]],
                label=phase,
            )
        axes[0, 1].set_title("Saturação Média")
        axes[0, 1].set_xlabel("Tempo")
        axes[0, 1].set_ylabel("Saturação")
        axes[0, 1].legend()

        # Produção
        for phase in ["oil", "water", "gas"]:
            axes[1, 0].plot(results["time"], results["production"][phase], label=phase)
        axes[1, 0].set_title("Produção")
        axes[1, 0].set_xlabel("Tempo")
        axes[1, 0].set_ylabel("Taxa de Produção")
        axes[1, 0].legend()

        # Mecanismos de Empuxo
        for mechanism in ["gas_cap", "aquifer", "solution_gas"]:
            if self.drive_mechanisms[mechanism]:
                axes[1, 1].plot(
                    results["time"],
                    results["drive_mechanisms"][mechanism],
                    label=mechanism,
                )
        axes[1, 1].set_title("Mecanismos de Empuxo")
        axes[1, 1].set_xlabel("Tempo")
        axes[1, 1].set_ylabel("Contribuição")
        axes[1, 1].legend()

        # Distribuição de pressão
        grid = self.mesh.to_pyvista()
        grid.cell_data["pressure"] = results["pressure"][-1]
        plotter = pv.Plotter()
        plotter.add_mesh(grid, scalars="pressure", show_edges=True)
        plotter.show()

        plt.tight_layout()
        return fig

    def export_results(self, filename):
        """Exporta resultados para CSV."""
        # Implementar exportação
        pass
