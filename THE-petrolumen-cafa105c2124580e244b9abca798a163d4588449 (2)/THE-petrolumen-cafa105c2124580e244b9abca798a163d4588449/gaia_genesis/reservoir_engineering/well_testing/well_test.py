import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy.optimize import curve_fit
from scipy.signal import savgol_filter

class WellTest:
    """Módulo avançado de teste de poços"""
    
    def __init__(self):
        self.pressure_data = []
        self.rate_data = []
        self.time_data = []
        self.derivatives = []
        self.analysis_results = {}
        
    def load_data(self, time: np.ndarray,
                 pressure: np.ndarray,
                 rate: Optional[np.ndarray] = None):
        """Carrega dados do teste"""
        self.time_data = time
        self.pressure_data = pressure
        self.rate_data = rate if rate is not None else np.zeros_like(time)
        
    def calculate_pressure_derivative(self, smooth_window: int = 11):
        """Calcula derivada de pressão"""
        log_time = np.log10(self.time_data)
        log_delta_p = np.log10(self.pressure_data[0] - self.pressure_data)
        
        # Suavização usando Savitzky-Golay
        smooth_dp = savgol_filter(log_delta_p, smooth_window, 3)
        
        # Calcular derivada
        self.derivatives = np.gradient(smooth_dp, log_time)
        
    def identify_flow_regimes(self) -> Dict[str, Tuple[float, float]]:
        """Identifica regimes de fluxo"""
        regimes = {}
        
        # Early-time region (wellbore storage)
        early_mask = self.derivatives > 0.9
        if np.any(early_mask):
            start_idx = np.where(early_mask)[0][0]
            end_idx = np.where(early_mask)[0][-1]
            regimes["wellbore_storage"] = (
                self.time_data[start_idx],
                self.time_data[end_idx]
            )
        
        # Middle-time region (radial flow)
        radial_mask = np.abs(self.derivatives) < 0.1
        if np.any(radial_mask):
            start_idx = np.where(radial_mask)[0][0]
            end_idx = np.where(radial_mask)[0][-1]
            regimes["radial_flow"] = (
                self.time_data[start_idx],
                self.time_data[end_idx]
            )
        
        # Late-time region (boundary effects)
        late_mask = self.derivatives < -0.1
        if np.any(late_mask):
            start_idx = np.where(late_mask)[0][0]
            end_idx = np.where(late_mask)[0][-1]
            regimes["boundary_dominated"] = (
                self.time_data[start_idx],
                self.time_data[end_idx]
            )
            
        return regimes
    
    def horner_analysis(self) -> Dict:
        """Realiza análise de Horner"""
        # Tempo de produção equivalente
        tp = self.time_data[-1]
        
        # Horner time
        horner_time = (tp + self.time_data) / self.time_data
        
        # Ajuste linear
        coeffs = np.polyfit(np.log(horner_time),
                          self.pressure_data,
                          1)
        
        # Calcular parâmetros
        slope = coeffs[0]
        p_star = coeffs[1]  # Pressão extrapolada infinita
        
        return {
            "slope": slope,
            "p_star": p_star,
            "horner_time": horner_time
        }
    
    def mdh_analysis(self) -> Dict:
        """Realiza análise de Miller-Dyes-Hutchinson"""
        # Tempo desde shut-in
        dt = self.time_data - self.time_data[0]
        
        # Ajuste linear na região de fluxo radial
        regimes = self.identify_flow_regimes()
        if "radial_flow" in regimes:
            start_time, end_time = regimes["radial_flow"]
            mask = (dt >= start_time) & (dt <= end_time)
            
            coeffs = np.polyfit(np.log(dt[mask]),
                              self.pressure_data[mask],
                              1)
            
            slope = coeffs[0]
            intercept = coeffs[1]
            
            return {
                "slope": slope,
                "intercept": intercept,
                "radial_flow_period": (start_time, end_time)
            }
        return {}
    
    def pressure_buildup_analysis(self) -> Dict:
        """Realiza análise de buildup"""
        results = {}
        
        # Análise de Horner
        horner = self.horner_analysis()
        results["horner"] = horner
        
        # Análise MDH
        mdh = self.mdh_analysis()
        results["mdh"] = mdh
        
        # Identificação de regimes de fluxo
        regimes = self.identify_flow_regimes()
        results["flow_regimes"] = regimes
        
        return results
    
    def calculate_reservoir_properties(self, fluid_props: Dict) -> Dict:
        """Calcula propriedades do reservatório"""
        # Obter resultados da análise
        analysis = self.pressure_buildup_analysis()
        
        if "mdh" in analysis and analysis["mdh"]:
            slope = analysis["mdh"]["slope"]
            
            # Permeabilidade
            k = -(162.6 * fluid_props["viscosity"] * fluid_props["rate"] *
                 fluid_props["formation_volume_factor"]) / slope
            
            # Skin factor
            if "horner" in analysis:
                p1hr = np.interp(1.0, analysis["horner"]["horner_time"],
                               self.pressure_data)
                p_star = analysis["horner"]["p_star"]
                skin = 1.151 * ((p_star - p1hr) / slope - np.log(k /
                       (fluid_props["porosity"] * fluid_props["viscosity"] *
                        fluid_props["wellbore_radius"] ** 2)))
                
                return {
                    "permeability": k,
                    "skin_factor": skin
                }
        
        return {}
    
    def generate_report(self) -> Dict:
        """Gera relatório completo do teste"""
        return {
            "analysis_results": self.analysis_results,
            "identified_flow_regimes": self.identify_flow_regimes(),
            "pressure_derivative": self.derivatives.tolist(),
            "quality_indicators": self._calculate_quality_indicators()
        }
    
    def _calculate_quality_indicators(self) -> Dict:
        """Calcula indicadores de qualidade do teste"""
        # Verificar duração dos regimes de fluxo
        regimes = self.identify_flow_regimes()
        
        quality = {}
        if "radial_flow" in regimes:
            start, end = regimes["radial_flow"]
            duration = end - start
            quality["radial_flow_duration"] = duration
            
            # Critério de qualidade
            if duration > 10:  # horas
                quality["test_quality"] = "good"
            elif duration > 5:
                quality["test_quality"] = "fair"
            else:
                quality["test_quality"] = "poor"
                
        return quality
