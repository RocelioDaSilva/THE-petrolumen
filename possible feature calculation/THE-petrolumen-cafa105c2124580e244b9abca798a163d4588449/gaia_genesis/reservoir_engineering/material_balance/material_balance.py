import numpy as np
from typing import Dict, List, Optional
import logging
from ..pvt.pvt_properties import PVTProperties

class MaterialBalance:
    """Classe para análise de balanço de materiais."""
    
    def __init__(self):
        self.pvt = PVTProperties()
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('MaterialBalance')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def calculate_ogip(self,
                      area: float,
                      thickness: float,
                      porosity: float,
                      water_saturation: float,
                      pressure: float,
                      temperature: float,
                      gas_specific_gravity: float) -> float:
        """
        Calcula OGIP (Original Gas In Place).
        
        Args:
            area: Área do reservatório (acres)
            thickness: Espessura (ft)
            porosity: Porosidade (fração)
            water_saturation: Saturação de água (fração)
            pressure: Pressão inicial (psia)
            temperature: Temperatura (°F)
            gas_specific_gravity: Densidade do gás
            
        Returns:
            OGIP (MMscf)
        """
        # Volume poroso
        vp = area * thickness * porosity * (1 - water_saturation)
        
        # Fator de volume de formação do gás
        z = self.pvt.calculate_z_factor(pressure, temperature, gas_specific_gravity)
        bg = 0.02827 * z * (temperature + 460) / pressure
        
        # OGIP
        ogip = vp / bg / 1000  # Convertendo para MMscf
        self.logger.info(f"OGIP calculado: {ogip:.2f} MMscf")
        
        return ogip
        
    def calculate_stoiip(self,
                        area: float,
                        thickness: float,
                        porosity: float,
                        water_saturation: float,
                        pressure: float,
                        temperature: float,
                        api_gravity: float,
                        gas_specific_gravity: float) -> float:
        """
        Calcula STOIIP (Stock Tank Oil Initially In Place).
        
        Args:
            area: Área do reservatório (acres)
            thickness: Espessura (ft)
            porosity: Porosidade (fração)
            water_saturation: Saturação de água (fração)
            pressure: Pressão inicial (psia)
            temperature: Temperatura (°F)
            api_gravity: Grau API do óleo
            gas_specific_gravity: Densidade do gás
            
        Returns:
            STOIIP (MMstb)
        """
        # Volume poroso
        vp = area * thickness * porosity * (1 - water_saturation)
        
        # Fator de volume de formação do óleo
        bo = self.pvt.calculate_formation_volume_factor(pressure, temperature, 'oil', api_gravity, gas_specific_gravity)
        
        # STOIIP
        stoiip = vp / bo / 1000  # Convertendo para MMstb
        self.logger.info(f"STOIIP calculado: {stoiip:.2f} MMstb")
        
        return stoiip
        
    def analyze_havlena_odeh(self,
                            time: np.ndarray,
                            pressure: np.ndarray,
                            production: np.ndarray,
                            reservoir_type: str,
                            pvt_data: Dict) -> Dict:
        """
        Análise de balanço de materiais pelo método de Havlena-Odeh.
        
        Args:
            time: Array com tempos
            pressure: Array com pressões
            production: Array com produção acumulada
            reservoir_type: Tipo do reservatório ('oil' ou 'gas')
            pvt_data: Dicionário com dados PVT
            
        Returns:
            Dicionário com resultados da análise
        """
        self.logger.info("Iniciando análise de Havlena-Odeh")
        
        if reservoir_type == 'gas':
            # Análise para reservatório de gás
            z = np.array([self.pvt.calculate_z_factor(p, pvt_data['temperature'], pvt_data['gas_specific_gravity'])
                         for p in pressure])
            p_z = pressure / z
            p_z_initial = pvt_data['initial_pressure'] / self.pvt.calculate_z_factor(
                pvt_data['initial_pressure'],
                pvt_data['temperature'],
                pvt_data['gas_specific_gravity']
            )
            
            # Cálculo de F e Eg
            f = production
            eg = p_z_initial - p_z
            
            # Ajuste linear
            slope, intercept = np.polyfit(eg, f, 1)
            
            return {
                'ogip': slope,
                'water_influx': intercept,
                'r_squared': self._calculate_r_squared(eg, f, slope, intercept)
            }
            
        else:  # oil
            # Análise para reservatório de óleo
            bo = np.array([self.pvt.calculate_formation_volume_factor(
                p, pvt_data['temperature'], 'oil',
                pvt_data['api_gravity'], pvt_data['gas_specific_gravity']
            ) for p in pressure])
            
            rs = np.array([self.pvt.calculate_solution_gas_ratio(
                p, pvt_data['temperature'],
                pvt_data['api_gravity'], pvt_data['gas_specific_gravity']
            ) for p in pressure])
            
            # Cálculo de F e Eo
            f = production
            eo = (bo - pvt_data['initial_bo']) + \
                 pvt_data['initial_rs'] * (pvt_data['initial_bg'] - pvt_data['initial_bo'])
            
            # Ajuste linear
            slope, intercept = np.polyfit(eo, f, 1)
            
            return {
                'stoiip': slope,
                'water_influx': intercept,
                'r_squared': self._calculate_r_squared(eo, f, slope, intercept)
            }
            
    def _calculate_r_squared(self, x: np.ndarray, y: np.ndarray, slope: float, intercept: float) -> float:
        """Calcula coeficiente de determinação (R²)."""
        y_pred = slope * x + intercept
        ss_tot = np.sum((y - np.mean(y))**2)
        ss_res = np.sum((y - y_pred)**2)
        return 1 - (ss_res / ss_tot) 