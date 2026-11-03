import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy.optimize import curve_fit
from scipy.signal import find_peaks
import matplotlib.pyplot as plt

class NMRAnalysis:
    """Análise de Ressonância Magnética Nuclear (similar ao GIT LithoMetrix)"""
    
    def __init__(self):
        self.t2_data = None
        self.t1_data = None
        self.diffusion_data = None
        self.porosity_components = {}
        self.pore_size_dist = None
        self.permeability_estimates = {}
        
    def load_t2_data(self, time: np.ndarray, amplitude: np.ndarray):
        """Carrega dados de relaxação T2"""
        self.t2_data = {
            "time": time,
            "amplitude": amplitude
        }
        
    def load_t1_data(self, time: np.ndarray, amplitude: np.ndarray):
        """Carrega dados de relaxação T1"""
        self.t1_data = {
            "time": time,
            "amplitude": amplitude
        }
        
    def load_diffusion_data(self, gradient: np.ndarray, amplitude: np.ndarray):
        """Carrega dados de difusão"""
        self.diffusion_data = {
            "gradient": gradient,
            "amplitude": amplitude
        }
        
    def invert_t2_distribution(self, num_components: int = 50):
        """Inverte distribuição T2"""
        if self.t2_data is None:
            raise ValueError("Dados T2 não carregados")
            
        # Criar tempos de relaxação logaritmicamente espaçados
        t2_bins = np.logspace(-4, 0, num_components)
        
        # Matriz do kernel
        kernel = np.zeros((len(self.t2_data["time"]), len(t2_bins)))
        for i, t in enumerate(self.t2_data["time"]):
            kernel[i, :] = np.exp(-t / t2_bins)
            
        # Inversão usando NNLS (Non-Negative Least Squares)
        from scipy.optimize import nnls
        distribution, _ = nnls(kernel, self.t2_data["amplitude"])
        
        self.t2_distribution = {
            "bins": t2_bins,
            "amplitude": distribution
        }
        
    def decompose_porosity(self):
        """Decompõe porosidade em componentes"""
        if not hasattr(self, 't2_distribution'):
            raise ValueError("Execute inversão T2 primeiro")
            
        # Limites típicos para componentes de porosidade
        limits = {
            "clay_bound": (0.0001, 0.003),
            "capillary": (0.003, 0.03),
            "free_fluid": (0.03, 1.0)
        }
        
        total_amplitude = np.sum(self.t2_distribution["amplitude"])
        
        for comp_name, (t2_min, t2_max) in limits.items():
            mask = (self.t2_distribution["bins"] >= t2_min) & (
                self.t2_distribution["bins"] <= t2_max
            )
            comp_amplitude = np.sum(self.t2_distribution["amplitude"][mask])
            self.porosity_components[comp_name] = comp_amplitude / total_amplitude
            
    def estimate_permeability(self):
        """Estima permeabilidade usando modelos de RMN"""
        if not hasattr(self, 't2_distribution'):
            raise ValueError("Execute inversão T2 primeiro")
            
        # Média logarítmica de T2
        t2_log_mean = np.exp(np.average(
            np.log(self.t2_distribution["bins"]),
            weights=self.t2_distribution["amplitude"]
        ))
        
        # Modelos de permeabilidade
        phi = np.sum(self.t2_distribution["amplitude"])  # porosidade total
        
        # Modelo SDR (Schlumberger-Doll Research)
        self.permeability_estimates["SDR"] = 4 * (phi ** 2) * (t2_log_mean ** 2)
        
        # Modelo Coates
        if hasattr(self, 'porosity_components'):
            ffv = self.porosity_components["free_fluid"]
            bfv = self.porosity_components["clay_bound"] + self.porosity_components["capillary"]
            self.permeability_estimates["Coates"] = (phi ** 4) * ((ffv / bfv) ** 2)
            
    def analyze_pore_size_distribution(self, surface_relaxivity: float = 10.0):
        """Analisa distribuição de tamanho de poros"""
        if not hasattr(self, 't2_distribution'):
            raise ValueError("Execute inversão T2 primeiro")
            
        # Conversão de T2 para tamanho de poro
        # r = ρ * T2, onde ρ é a relaxividade superficial
        pore_sizes = surface_relaxivity * self.t2_distribution["bins"]
        
        self.pore_size_dist = {
            "sizes": pore_sizes,
            "amplitude": self.t2_distribution["amplitude"]
        }
        
    def analyze_wettability(self):
        """Analisa molhabilidade usando dados de RMN"""
        if self.t1_data is None or self.t2_data is None:
            raise ValueError("Dados T1 e T2 necessários")
            
        # Calcular razão T1/T2
        t1_mean = np.average(self.t1_data["time"],
                           weights=self.t1_data["amplitude"])
        t2_mean = np.average(self.t2_data["time"],
                           weights=self.t2_data["amplitude"])
        
        t1t2_ratio = t1_mean / t2_mean
        
        # Interpretação da molhabilidade
        if t1t2_ratio < 1.5:
            wettability = "water_wet"
        elif t1t2_ratio > 2.5:
            wettability = "oil_wet"
        else:
            wettability = "mixed_wet"
            
        self.wettability = {
            "t1t2_ratio": t1t2_ratio,
            "interpretation": wettability
        }
        
    def analyze_diffusion(self, temperature: float = 298.0):
        """Analisa dados de difusão"""
        if self.diffusion_data is None:
            raise ValueError("Dados de difusão não carregados")
            
        # Ajuste para equação de difusão
        def diffusion_model(g, D):
            return np.exp(-D * g ** 2)
        
        # Normalizar amplitude
        norm_amplitude = self.diffusion_data["amplitude"] / np.max(
            self.diffusion_data["amplitude"]
        )
        
        # Ajustar modelo
        popt, _ = curve_fit(diffusion_model,
                           self.diffusion_data["gradient"],
                           norm_amplitude)
        
        D = popt[0]
        
        # Correção para temperatura
        D_corrected = D * (temperature / 298.0)
        
        self.diffusion_coefficients = {
            "D": D,
            "D_corrected": D_corrected
        }
        
    def plot_results(self):
        """Plota resultados da análise"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # T2 distribution
        if hasattr(self, 't2_distribution'):
            axes[0,0].semilogx(self.t2_distribution["bins"],
                             self.t2_distribution["amplitude"])
            axes[0,0].set_xlabel('T2 (s)')
            axes[0,0].set_ylabel('Amplitude')
            axes[0,0].set_title('T2 Distribution')
            
        # Pore size distribution
        if hasattr(self, 'pore_size_dist'):
            axes[0,1].semilogx(self.pore_size_dist["sizes"],
                             self.pore_size_dist["amplitude"])
            axes[0,1].set_xlabel('Pore Size (μm)')
            axes[0,1].set_ylabel('Amplitude')
            axes[0,1].set_title('Pore Size Distribution')
            
        # Porosity components
        if hasattr(self, 'porosity_components'):
            axes[1,0].pie(list(self.porosity_components.values()),
                         labels=list(self.porosity_components.keys()),
                         autopct='%1.1f%%')
            axes[1,0].set_title('Porosity Components')
            
        # Diffusion data
        if hasattr(self, 'diffusion_coefficients'):
            axes[1,1].plot(self.diffusion_data["gradient"],
                         self.diffusion_data["amplitude"], 'o')
            axes[1,1].set_xlabel('Gradient Strength')
            axes[1,1].set_ylabel('Amplitude')
            axes[1,1].set_title('Diffusion Data')
            
        plt.tight_layout()
        return fig
        
    def export_results(self, filename: str):
        """Exporta resultados da análise"""
        results = {
            "porosity_components": self.porosity_components,
            "permeability_estimates": self.permeability_estimates,
            "wettability": getattr(self, 'wettability', None),
            "diffusion_coefficients": getattr(self, 'diffusion_coefficients', None)
        }
        
        import json
        with open(filename, 'w') as f:
            json.dump(results, f)
