from history_matching import HistoryMatching
from flow_simulation import FlowSimulation
import numpy as np
from typing import Dict, Optional

class FlowHistoryMatching(HistoryMatching):
    def __init__(self, simulation: FlowSimulation):
        """
        Inicializa o ajuste de histórico para simulação de fluxo.
        
        Args:
            simulation: Objeto de simulação de fluxo
        """
        super().__init__()
        self.simulation = simulation
        
    def add_reservoir_parameters(self):
        """Adiciona parâmetros do reservatório para ajuste."""
        # Porosidade
        self.add_parameter(
            'porosity_multiplier',
            initial_value=1.0,
            bounds=(0.5, 2.0),
            description="Multiplicador de porosidade"
        )
        
        # Permeabilidade
        self.add_parameter(
            'permeability_multiplier',
            initial_value=1.0,
            bounds=(0.1, 10.0),
            description="Multiplicador de permeabilidade"
        )
        
        # Saturação residual
        self.add_parameter(
            'sor',
            initial_value=0.2,
            bounds=(0.1, 0.4),
            description="Saturação residual de óleo"
        )
        
        self.add_parameter(
            'swc',
            initial_value=0.2,
            bounds=(0.1, 0.4),
            description="Saturação crítica de água"
        )
        
        self.add_parameter(
            'sgc',
            initial_value=0.05,
            bounds=(0.01, 0.2),
            description="Saturação crítica de gás"
        )
        
    def add_relative_permeability_parameters(self):
        """Adiciona parâmetros de permeabilidade relativa para ajuste."""
        # Expoentes de Corey
        self.add_parameter(
            'n_o',
            initial_value=2.0,
            bounds=(1.0, 4.0),
            description="Expoente de Corey para óleo"
        )
        
        self.add_parameter(
            'n_w',
            initial_value=2.0,
            bounds=(1.0, 4.0),
            description="Expoente de Corey para água"
        )
        
        self.add_parameter(
            'n_g',
            initial_value=2.0,
            bounds=(1.0, 4.0),
            description="Expoente de Corey para gás"
        )
        
    def add_capillary_pressure_parameters(self):
        """Adiciona parâmetros de pressão capilar para ajuste."""
        # Parâmetros de Brooks-Corey
        self.add_parameter(
            'lambda_bc',
            initial_value=2.0,
            bounds=(1.0, 4.0),
            description="Expoente de Brooks-Corey"
        )
        
        self.add_parameter(
            'pce',
            initial_value=5.0,
            bounds=(1.0, 20.0),
            description="Pressão capilar de entrada (psi)"
        )
        
    def add_aquifer_parameters(self):
        """Adiciona parâmetros de aquífero para ajuste."""
        self.add_parameter(
            'aquifer_volume_multiplier',
            initial_value=1.0,
            bounds=(0.1, 10.0),
            description="Multiplicador de volume do aquífero"
        )
        
        self.add_parameter(
            'aquifer_compressibility_multiplier',
            initial_value=1.0,
            bounds=(0.1, 10.0),
            description="Multiplicador de compressibilidade do aquífero"
        )
        
    def add_gas_cap_parameters(self):
        """Adiciona parâmetros de cap de gás para ajuste."""
        self.add_parameter(
            'gas_cap_volume_multiplier',
            initial_value=1.0,
            bounds=(0.1, 10.0),
            description="Multiplicador de volume do cap de gás"
        )
        
        self.add_parameter(
            'gas_oil_contact_shift',
            initial_value=0.0,
            bounds=(-100.0, 100.0),
            description="Deslocamento do contato gás-óleo (ft)"
        )
        
    def add_solution_gas_parameters(self):
        """Adiciona parâmetros de gás em solução para ajuste."""
        self.add_parameter(
            'initial_gas_oil_ratio_multiplier',
            initial_value=1.0,
            bounds=(0.5, 2.0),
            description="Multiplicador da razão gás-óleo inicial"
        )
        
        self.add_parameter(
            'bubble_point_pressure_shift',
            initial_value=0.0,
            bounds=(-500.0, 500.0),
            description="Deslocamento da pressão de bolha (psi)"
        )
        
    def update_simulation_parameters(self):
        """Atualiza parâmetros da simulação com valores otimizados."""
        # Atualizar propriedades do reservatório
        if 'porosity_multiplier' in self.parameters:
            self.simulation.porosity *= self.parameters['porosity_multiplier']['value']
            
        if 'permeability_multiplier' in self.parameters:
            self.simulation.permeability *= self.parameters['permeability_multiplier']['value']
            
        # Atualizar saturações residuais
        if 'sor' in self.parameters:
            self.simulation.saturation['oil'] = np.maximum(
                self.simulation.saturation['oil'],
                self.parameters['sor']['value']
            )
            
        if 'swc' in self.parameters:
            self.simulation.saturation['water'] = np.maximum(
                self.simulation.saturation['water'],
                self.parameters['swc']['value']
            )
            
        if 'sgc' in self.parameters:
            self.simulation.saturation['gas'] = np.maximum(
                self.simulation.saturation['gas'],
                self.parameters['sgc']['value']
            )
            
        # Atualizar parâmetros de permeabilidade relativa
        if 'n_o' in self.parameters:
            self.simulation.relative_permeability['n_o'] = self.parameters['n_o']['value']
            
        if 'n_w' in self.parameters:
            self.simulation.relative_permeability['n_w'] = self.parameters['n_w']['value']
            
        if 'n_g' in self.parameters:
            self.simulation.relative_permeability['n_g'] = self.parameters['n_g']['value']
            
        # Atualizar parâmetros de pressão capilar
        if 'lambda_bc' in self.parameters:
            self.simulation.capillary_pressure['lambda_bc'] = self.parameters['lambda_bc']['value']
            
        if 'pce' in self.parameters:
            self.simulation.capillary_pressure['pce'] = self.parameters['pce']['value']
            
        # Atualizar parâmetros de aquífero
        if 'aquifer_volume_multiplier' in self.parameters:
            self.simulation.aquifer_properties['aquifer_volume'] *= (
                self.parameters['aquifer_volume_multiplier']['value']
            )
            
        if 'aquifer_compressibility_multiplier' in self.parameters:
            self.simulation.aquifer_properties['aquifer_compressibility'] *= (
                self.parameters['aquifer_compressibility_multiplier']['value']
            )
            
        # Atualizar parâmetros de cap de gás
        if 'gas_cap_volume_multiplier' in self.parameters:
            self.simulation.gas_cap_properties['gas_cap_volume'] *= (
                self.parameters['gas_cap_volume_multiplier']['value']
            )
            
        if 'gas_oil_contact_shift' in self.parameters:
            self.simulation.gas_cap_properties['gas_oil_contact'] += (
                self.parameters['gas_oil_contact_shift']['value']
            )
            
        # Atualizar parâmetros de gás em solução
        if 'initial_gas_oil_ratio_multiplier' in self.parameters:
            self.simulation.solution_gas_properties['initial_gas_oil_ratio'] *= (
                self.parameters['initial_gas_oil_ratio_multiplier']['value']
            )
            
        if 'bubble_point_pressure_shift' in self.parameters:
            self.simulation.solution_gas_properties['bubble_point_pressure'] += (
                self.parameters['bubble_point_pressure_shift']['value']
            )
            
    def run_simulation(self) -> Dict[str, np.ndarray]:
        """
        Executa simulação com parâmetros atuais.
        
        Returns:
            Dicionário com resultados simulados
        """
        # Atualizar parâmetros da simulação
        self.update_simulation_parameters()
        
        # Executar simulação
        results = self.simulation.run_black_oil_simulation(
            dt=self.historical_data['time'][1] - self.historical_data['time'][0],
            n_steps=len(self.historical_data['time'])
        )
        
        # Preparar resultados
        simulated = {
            'pressure': np.array([np.mean(p) for p in results['pressure']]),
            'production': {
                phase: np.array(results['production'][phase])
                for phase in ['oil', 'water', 'gas']
            }
        }
        
        return simulated 