import numpy as np
from typing import Optional
import logging

class PVTProperties:
    """Classe para cálculo de propriedades PVT."""
    
    def __init__(self):
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('PVTProperties')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def calculate_formation_volume_factor(self,
                                        pressure: float,
                                        temperature: float,
                                        fluid_type: str,
                                        api_gravity: Optional[float] = None,
                                        gas_specific_gravity: Optional[float] = None) -> float:
        """
        Calcula fator de volume de formação (Bo, Bg).
        
        Args:
            pressure: Pressão (psia)
            temperature: Temperatura (°F)
            fluid_type: Tipo de fluido ('oil' ou 'gas')
            api_gravity: Grau API do óleo
            gas_specific_gravity: Densidade do gás
            
        Returns:
            Fator de volume de formação
        """
        if fluid_type == 'oil':
            # Correlação de Standing para Bo
            rs = self.calculate_solution_gas_ratio(pressure, temperature, api_gravity, gas_specific_gravity)
            f = rs * (gas_specific_gravity/0.7)**0.5 + 1.25 * temperature
            bo = 0.972 + 0.000147 * f**1.175
            return bo
        else:  # gas
            # Correlação de Dranchuk-Abu-Kassem para Bg
            z = self.calculate_z_factor(pressure, temperature, gas_specific_gravity)
            bg = 0.02827 * z * temperature / pressure
            return bg
            
    def calculate_viscosity(self,
                          pressure: float,
                          temperature: float,
                          fluid_type: str,
                          api_gravity: Optional[float] = None,
                          gas_specific_gravity: Optional[float] = None) -> float:
        """
        Calcula viscosidade dos fluidos.
        
        Args:
            pressure: Pressão (psia)
            temperature: Temperatura (°F)
            fluid_type: Tipo de fluido ('oil' ou 'gas')
            api_gravity: Grau API do óleo
            gas_specific_gravity: Densidade do gás
            
        Returns:
            Viscosidade (cp)
        """
        if fluid_type == 'oil':
            # Correlação de Beggs-Robinson para viscosidade do óleo
            api = api_gravity
            t = temperature
            
            # Viscosidade do óleo morto
            a = 10**(0.43 + 8.33/api)
            mu_od = (0.32 + 1.8e7/api**4.53) * (360/(t + 200))**a
            
            # Viscosidade do óleo saturado
            rs = self.calculate_solution_gas_ratio(pressure, temperature, api_gravity, gas_specific_gravity)
            a = 10.715 * (rs + 100)**-0.515
            b = 5.44 * (rs + 150)**-0.338
            mu_o = a * mu_od**b
            
            return mu_o
        else:  # gas
            # Correlação de Lee-Gonzalez-Eakin para viscosidade do gás
            t = temperature + 460  # temperatura em Rankine
            mw = gas_specific_gravity * 28.97  # peso molecular
            rho = pressure * mw / (10.73 * t * self.calculate_z_factor(pressure, temperature, gas_specific_gravity))
            
            k = (9.4 + 0.02 * mw) * t**1.5 / (209 + 19 * mw + t)
            x = 3.5 + 986/t + 0.01 * mw
            y = 2.4 - 0.2 * x
            
            mu_g = 1e-4 * k * np.exp(x * rho**y)
            return mu_g
            
    def calculate_solution_gas_ratio(self,
                                   pressure: float,
                                   temperature: float,
                                   api_gravity: float,
                                   gas_specific_gravity: float) -> float:
        """
        Calcula relação gás-óleo em solução (Rs).
        
        Args:
            pressure: Pressão (psia)
            temperature: Temperatura (°F)
            api_gravity: Grau API do óleo
            gas_specific_gravity: Densidade do gás
            
        Returns:
            Relação gás-óleo (scf/stb)
        """
        # Correlação de Standing
        api = api_gravity
        t = temperature
        yg = gas_specific_gravity
        
        x = 0.0125 * api - 0.00091 * t
        rs = yg * (pressure/18.2 + 1.4) * 10**x
        return rs
        
    def calculate_z_factor(self,
                          pressure: float,
                          temperature: float,
                          gas_specific_gravity: float) -> float:
        """
        Calcula fator de compressibilidade (Z).
        
        Args:
            pressure: Pressão (psia)
            temperature: Temperatura (°F)
            gas_specific_gravity: Densidade do gás
            
        Returns:
            Fator de compressibilidade
        """
        # Correlação de Hall-Yarborough
        t = temperature + 460  # temperatura em Rankine
        tpc = 168 + 325 * gas_specific_gravity - 12.5 * gas_specific_gravity**2
        ppc = 677 + 15 * gas_specific_gravity - 37.5 * gas_specific_gravity**2
        
        tr = t / tpc
        pr = pressure / ppc
        
        t1 = 0.06125 * pr * np.exp(-1.2 * (1 - 1/tr)**2)
        t2 = 14.76 * tr - 9.76 * tr**2 + 4.58 * tr**3
        t3 = 90.7 * tr - 242.2 * tr**2 + 42.4 * tr**3
        t4 = 2.18 + 2.82 * tr
        
        y = t1 / (t2 + t3 + t4)
        
        z = 0.06125 * pr * np.exp(-1.2 * (1 - 1/tr)**2) / y
        return z 