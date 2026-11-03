import unittest
import numpy as np
from gaia_genesis.simulation.black_oil_simulator import BlackOilSimulator
from gaia_genesis.simulation.thermal_simulator import ThermalSimulator
from gaia_genesis.simulation.proxy_models import WellProductionProxy
from gaia_genesis.visualization.visualizer3d import Visualizer3D
from gaia_genesis.reservoir_engineering.well_testing.well_test import WellTest
from gaia_genesis.reservoir_engineering.economics.economic_analysis import EconomicAnalysis, EconomicParameters

class TestSystemIntegration(unittest.TestCase):
    """Testes de integração para o sistema Gaia Genesis"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        # Dimensões do grid
        self.nx, self.ny, self.nz = 10, 10, 5
        self.dx = self.dy = self.dz = 10.0
        
        # Configurar simulador black-oil
        self.black_oil = BlackOilSimulator()
        self.black_oil.setup_grid(self.nx, self.ny, self.nz,
                                self.dx, self.dy, self.dz)
        
        # Propriedades básicas
        self.porosity = np.full((self.nx, self.ny, self.nz), 0.2)
        self.permeability = np.full((self.nx, self.ny, self.nz), 100.0)
        
        # PVT
        self.pvt_data = {
            "oil_viscosity": 1.0,
            "water_viscosity": 0.5,
            "gas_viscosity": 0.01,
            "formation_volume_factor": 1.2
        }
        
    def test_black_oil_simulation(self):
        """Teste do simulador black-oil"""
        # Configurar propriedades
        self.black_oil.set_rock_properties(
            self.porosity,
            self.permeability,
            1e-6  # compressibilidade
        )
        
        self.black_oil.set_fluid_properties(self.pvt_data)
        
        # Adicionar poço produtor
        self.black_oil.add_well(
            "PROD1",
            5, 5,  # localização i,j
            [2, 3],  # camadas perfuradas
            "producer",
            {"bhp": 200.0}  # controle de pressão de fundo
        )
        
        # Inicializar
        initial_pressure = 300.0
        initial_saturations = {
            "water": np.full((self.nx, self.ny, self.nz), 0.2),
            "oil": np.full((self.nx, self.ny, self.nz), 0.8),
            "gas": np.zeros((self.nx, self.ny, self.nz))
        }
        
        self.black_oil.initialize(initial_pressure, initial_saturations)
        
        # Rodar timestep
        self.black_oil.run_timestep(1.0)
        
        # Verificar resultados
        results = self.black_oil.get_results()
        self.assertIsNotNone(results["pressure"])
        self.assertIsNotNone(results["saturations"])
        
    def test_thermal_simulation(self):
        """Teste do simulador térmico"""
        thermal = ThermalSimulator()
        thermal.setup_grid(self.nx, self.ny, self.nz,
                         self.dx, self.dy, self.dz)
        
        # Configurar propriedades térmicas
        thermal.set_thermal_properties(
            rock_heat_capacity=2000.0,
            rock_thermal_conductivity=2.0,
            fluid_heat_capacities={
                "water": 4200.0,
                "oil": 2000.0,
                "gas": 1000.0
            },
            fluid_thermal_conductivities={
                "water": 0.6,
                "oil": 0.15,
                "gas": 0.024
            }
        )
        
        # Adicionar fonte de calor
        thermal.add_heat_source(5, 5, 2, 1000.0, 350.0)
        
        # Inicializar temperatura
        thermal.initialize_temperature(300.0)
        
        # Rodar timestep
        thermal.run_timestep(1.0)
        
        # Verificar resultados
        results = thermal.get_results()
        self.assertIsNotNone(results["temperature"])
        
    def test_proxy_model(self):
        """Teste do modelo proxy"""
        proxy = WellProductionProxy()
        proxy.build_model()
        
        # Dados de treinamento
        X = np.random.rand(100, 5)  # [P, k, phi, Sw, t]
        y = np.random.rand(100, 3)  # [qo, qw, qg]
        
        # Treinar modelo
        history = proxy.train(X, y, epochs=5)
        self.assertTrue(isinstance(history.history, dict))
        
        # Fazer predições
        X_test = np.random.rand(10, 5)
        predictions = proxy.predict(X_test)
        self.assertEqual(predictions.shape, (10, 3))
        
    def test_well_testing(self):
        """Teste do módulo de teste de poços"""
        well_test = WellTest()
        
        # Dados sintéticos
        time = np.linspace(0, 100, 100)
        pressure = 300 - 50 * np.log(time + 1) + np.random.rand(100)
        
        well_test.load_data(time, pressure)
        well_test.calculate_pressure_derivative()
        
        # Análise
        results = well_test.pressure_buildup_analysis()
        self.assertIsNotNone(results)
        
    def test_visualization(self):
        """Teste do sistema de visualização"""
        vis = Visualizer3D()
        vis.create_grid(self.nx, self.ny, self.nz,
                       self.dx, self.dy, self.dz)
        
        # Adicionar propriedade
        property_data = np.random.rand(self.nx, self.ny, self.nz)
        vis.add_property("pressure", property_data)
        
        # Adicionar poço
        trajectory = np.array([
            [0, 0, 0],
            [50, 50, 50]
        ])
        vis.add_well("WELL1", trajectory)
        
    def test_economic_analysis(self):
        """Teste da análise econômica"""
        params = EconomicParameters(
            oil_price=70.0,
            gas_price=3.0,
            water_cost=5.0,
            opex=1000.0,
            capex=1e6,
            tax_rate=0.3,
            discount_rate=0.1
        )
        
        econ = EconomicAnalysis(params)
        
        # Dados de produção sintéticos
        production_data = {
            "oil": np.random.rand(100) * 1000,
            "gas": np.random.rand(100) * 5000,
            "water": np.random.rand(100) * 500
        }
        
        timesteps = np.arange(100)
        econ.calculate_cash_flows(production_data, timesteps)
        
        npv = econ.calculate_npv()
        self.assertIsInstance(npv, float)
        
        irr = econ.calculate_irr()
        self.assertIsInstance(irr, float)
        
    def test_full_workflow(self):
        """Teste do fluxo de trabalho completo"""
        # 1. Simulação black-oil
        self.test_black_oil_simulation()
        
        # 2. Análise de teste de poço
        self.test_well_testing()
        
        # 3. Treinamento de modelo proxy
        self.test_proxy_model()
        
        # 4. Visualização de resultados
        self.test_visualization()
        
        # 5. Análise econômica
        self.test_economic_analysis()
        
if __name__ == '__main__':
    unittest.main()
