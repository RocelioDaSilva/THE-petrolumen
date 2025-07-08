import numpy as np

# from scipy.sparse import diags, csr_matrix # Unused
# from scipy.sparse.linalg import spsolve # Unused
# import pandas as pd # Unused
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from .geology.mesh import Mesh  # Corrected to relative import
import pyvista as pv


class FlowSimulation:
    def __init__(self, mesh_type="structured", **kwargs):
        """
        Inicializa o simulador de fluxo.

        Args:
            mesh_type (str): Tipo de malha ('structured' ou 'unstructured')
            **kwargs: Parâmetros para criação da malha
                Para malha estruturada: nx, ny, nz, dx, dy, dz
                Para malha não estruturada: points, boundary_points
        """
        # Criar malha
        self.mesh = Mesh()
        if mesh_type == "structured":
            self.mesh.create_structured_mesh(**kwargs)
        else:
            self.mesh.create_unstructured_mesh(**kwargs)

        # Inicializar propriedades do reservatório
        self.porosity = np.ones(len(self.mesh.cells)) * 0.2
        self.permeability = np.ones(len(self.mesh.cells)) * 100  # md
        self.depth = np.zeros(len(self.mesh.cells))

        # Inicializar condições iniciais
        self.pressure = np.ones(len(self.mesh.cells)) * 3000  # psia
        self.temperature = np.ones(len(self.mesh.cells)) * 180  # °F
        self.saturation = {
            "oil": np.ones(len(self.mesh.cells)) * 0.7,
            "water": np.ones(len(self.mesh.cells)) * 0.3,
            "gas": np.zeros(len(self.mesh.cells)),
        }

        # Inicializar propriedades PVT
        self.pvt_data = None

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

    def run_black_oil_simulation(self, dt, n_steps):
        """
        Executa simulação black oil.

        Args:
            dt (float): Passo de tempo
            n_steps (int): Número de passos
        """
        results = {
            "time": [],
            "pressure": [],
            "saturation": {"oil": [], "water": [], "gas": []},
            "production": {"oil": [], "water": [], "gas": []},
            "drive_mechanisms": {"gas_cap": [], "aquifer": [], "solution_gas": []},
        }

        for step in range(n_steps):
            current_time = step * dt

            # Calcular pressão capilar
            _ = self.calculate_capillary_pressure(self.saturation)  # pc F841: Unused

            # Calcular permeabilidade relativa
            kr = self.calculate_relative_permeability(self.saturation)

            # Calcular propriedades PVT
            pvt = self.calculate_pvt_properties(self.pressure, self.temperature)

            # Calcular mobilidade
            mobility = self.calculate_phase_mobility(kr, pvt)

            # Calcular velocidade das fases
            gravity = 32.2  # ft/s²
            velocity = self.calculate_phase_velocity(self.pressure, mobility, gravity)

            # Calcular efeitos de empuxo
            gas_cap_drive = self.calculate_gas_cap_drive(self.pressure, self.saturation)
            aquifer_drive = self.calculate_aquifer_drive(self.pressure, current_time)
            solution_gas_drive = self.calculate_solution_gas_drive(
                self.pressure, self.saturation
            )

            # Atualizar saturação considerando empuxo
            self.update_phase_saturation(velocity, dt)

            # Aplicar efeitos de empuxo
            if self.drive_mechanisms["gas_cap"]:
                self.saturation["gas"] += gas_cap_drive
            if self.drive_mechanisms["aquifer"]:
                self.saturation["water"] += aquifer_drive
            if self.drive_mechanisms["solution_gas"]:
                self.saturation["gas"] += solution_gas_drive

            # Normalizar saturações
            total_sat = sum(self.saturation.values())
            for phase in self.saturation.keys():
                self.saturation[phase] /= total_sat

            # Calcular produção
            production = self.calculate_production(kr, pvt)

            # Atualizar resultados
            results["time"].append(current_time)
            results["pressure"].append(self.pressure.copy())
            for phase in ["oil", "water", "gas"]:
                results["saturation"][phase].append(self.saturation[phase].copy())
                results["production"][phase].append(production[phase])

            # Atualizar resultados de empuxo
            results["drive_mechanisms"]["gas_cap"].append(gas_cap_drive)
            results["drive_mechanisms"]["aquifer"].append(aquifer_drive)
            results["drive_mechanisms"]["solution_gas"].append(solution_gas_drive)

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
