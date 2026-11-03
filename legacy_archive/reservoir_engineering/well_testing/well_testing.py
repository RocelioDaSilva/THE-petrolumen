import numpy as np
from typing import Dict, Tuple
import logging
from ..pvt.pvt_properties import PVTProperties

class WellTesting:
    """Classe para análise de testes de pressão."""
    
    def __init__(self):
        self.pvt = PVTProperties()
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('WellTesting')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def analyze_buildup(self,
                       time: np.ndarray,
                       pressure: np.ndarray,
                       flow_rate: float,
                       wellbore_radius: float,
                       reservoir_type: str,
                       pvt_data: Dict) -> Dict:
        """
        Análise de teste de build-up pelo método de Horner.
        
        Args:
            time: Array com tempos
            pressure: Array com pressões
            flow_rate: Vazão antes do build-up
            wellbore_radius: Raio do poço (ft)
            reservoir_type: Tipo do reservatório ('oil' ou 'gas')
            pvt_data: Dicionário com dados PVT
            
        Returns:
            Dicionário com resultados da análise
        """
        self.logger.info("Iniciando análise de build-up")
        
        # Cálculo do tempo de Horner
        tp = time[-1]  # Tempo de produção antes do build-up
        horner_time = (tp + time) / time
        
        # Ajuste linear na região de fluxo radial
        mask = (horner_time > 1.5) & (horner_time < 3.0)  # Região de fluxo radial
        slope, intercept = np.polyfit(np.log10(horner_time[mask]), pressure[mask], 1)
        
        # Cálculo da permeabilidade
        if reservoir_type == 'oil':
            mu = self.pvt.calculate_viscosity(
                np.mean(pressure[mask]),
                pvt_data['temperature'],
                'oil',
                pvt_data['api_gravity'],
                pvt_data['gas_specific_gravity']
            )
            bo = self.pvt.calculate_formation_volume_factor(
                np.mean(pressure[mask]),
                pvt_data['temperature'],
                'oil',
                pvt_data['api_gravity'],
                pvt_data['gas_specific_gravity']
            )
            k = 162.6 * mu * bo * flow_rate / (slope * pvt_data['thickness'])
        else:  # gas
            mu = self.pvt.calculate_viscosity(
                np.mean(pressure[mask]),
                pvt_data['temperature'],
                'gas',
                None,
                pvt_data['gas_specific_gravity']
            )
            z = self.pvt.calculate_z_factor(
                np.mean(pressure[mask]),
                pvt_data['temperature'],
                pvt_data['gas_specific_gravity']
            )
            k = 1637 * mu * z * flow_rate / (slope * pvt_data['thickness'])
            
        # Cálculo do skin
        p1hr = slope * np.log10((tp + 1) / 1) + intercept
        if reservoir_type == 'oil':
            skin = 1.151 * ((p1hr - pressure[0]) / slope - np.log10(k / (pvt_data['porosity'] * mu * pvt_data['total_compressibility'] * wellbore_radius**2)) - 3.23)
        else:  # gas
            skin = 1.151 * ((p1hr - pressure[0]) / slope - np.log10(k / (pvt_data['porosity'] * mu * pvt_data['total_compressibility'] * wellbore_radius**2)) - 3.23)
            
        return {
            'permeability': k,
            'skin': skin,
            'slope': slope,
            'intercept': intercept,
            'p1hr': p1hr
        }
        
    def analyze_drawdown(self,
                        time: np.ndarray,
                        pressure: np.ndarray,
                        flow_rate: float,
                        wellbore_radius: float,
                        reservoir_type: str,
                        pvt_data: Dict) -> Dict:
        """
        Análise de teste de drawdown.
        
        Args:
            time: Array com tempos
            pressure: Array com pressões
            flow_rate: Vazão constante
            wellbore_radius: Raio do poço (ft)
            reservoir_type: Tipo do reservatório ('oil' ou 'gas')
            pvt_data: Dicionário com dados PVT
            
        Returns:
            Dicionário com resultados da análise
        """
        self.logger.info("Iniciando análise de drawdown")
        
        # Ajuste linear na região de fluxo radial
        mask = (time > 1.0) & (time < 10.0)  # Região de fluxo radial
        slope, intercept = np.polyfit(np.log10(time[mask]), pressure[mask], 1)
        
        # Cálculo da permeabilidade
        if reservoir_type == 'oil':
            mu = self.pvt.calculate_viscosity(
                np.mean(pressure[mask]),
                pvt_data['temperature'],
                'oil',
                pvt_data['api_gravity'],
                pvt_data['gas_specific_gravity']
            )
            bo = self.pvt.calculate_formation_volume_factor(
                np.mean(pressure[mask]),
                pvt_data['temperature'],
                'oil',
                pvt_data['api_gravity'],
                pvt_data['gas_specific_gravity']
            )
            k = 162.6 * mu * bo * flow_rate / (slope * pvt_data['thickness'])
        else:  # gas
            mu = self.pvt.calculate_viscosity(
                np.mean(pressure[mask]),
                pvt_data['temperature'],
                'gas',
                None,
                pvt_data['gas_specific_gravity']
            )
            z = self.pvt.calculate_z_factor(
                np.mean(pressure[mask]),
                pvt_data['temperature'],
                pvt_data['gas_specific_gravity']
            )
            k = 1637 * mu * z * flow_rate / (slope * pvt_data['thickness'])
            
        # Cálculo do skin
        p1hr = slope * np.log10(1) + intercept
        if reservoir_type == 'oil':
            skin = 1.151 * ((pvt_data['initial_pressure'] - p1hr) / slope - np.log10(k / (pvt_data['porosity'] * mu * pvt_data['total_compressibility'] * wellbore_radius**2)) - 3.23)
        else:  # gas
            skin = 1.151 * ((pvt_data['initial_pressure'] - p1hr) / slope - np.log10(k / (pvt_data['porosity'] * mu * pvt_data['total_compressibility'] * wellbore_radius**2)) - 3.23)
            
        return {
            'permeability': k,
            'skin': skin,
            'slope': slope,
            'intercept': intercept,
            'p1hr': p1hr
        }
        
    def calculate_radius_of_investigation(self,
                                        time: float,
                                        permeability: float,
                                        porosity: float,
                                        total_compressibility: float,
                                        viscosity: float) -> float:
        """
        Calcula raio de investigação.
        
        Args:
            time: Tempo (horas)
            permeability: Permeabilidade (md)
            porosity: Porosidade (fração)
            total_compressibility: Compressibilidade total (1/psi)
            viscosity: Viscosidade (cp)
            
        Returns:
            Raio de investigação (ft)
        """
        ri = np.sqrt(0.00105 * permeability * time / (porosity * total_compressibility * viscosity))
        self.logger.info(f"Raio de investigação calculado: {ri:.2f} ft")
        return ri 