import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy.optimize import fsolve

class EosSolver:
    """Equation of State solver for compositional simulation"""
    
    def __init__(self, eos_type: str = "PR"):
        self.eos_type = eos_type
        self.components = {}
        self.binary_interactions = None
        
    def add_component(self, name: str, properties: Dict):
        """Add component with critical properties"""
        self.components[name] = {
            "Pc": properties["critical_pressure"],
            "Tc": properties["critical_temperature"],
            "omega": properties["acentric_factor"],
            "MW": properties.get("molecular_weight", 0.0)
        }
        
    def set_binary_interactions(self, kij: np.ndarray):
        """Set binary interaction parameters"""
        n = len(self.components)
        if kij.shape != (n, n):
            raise ValueError("Invalid binary interaction matrix shape")
        self.binary_interactions = kij
        
    def calculate_z_factor(self, P: float, T: float,
                          composition: Dict[str, float]) -> float:
        """Calculate compressibility factor"""
        # Convert composition to array
        z = np.array([composition[c] for c in self.components])
        
        if self.eos_type == "PR":
            return self._peng_robinson_z(P, T, z)
        elif self.eos_type == "SRK":
            return self._srk_z(P, T, z)
        else:
            raise ValueError(f"Unknown EoS type: {self.eos_type}")
            
    def flash_calculation(self, P: float, T: float,
                         composition: Dict[str, float],
                         initial_K: Optional[np.ndarray] = None
                         ) -> Dict:
        """Perform isothermal flash calculation"""
        z = np.array([composition[c] for c in self.components])
        
        # Initial K-values if not provided
        if initial_K is None:
            initial_K = self._wilson_k_values(P, T)
            
        # Solve Rachford-Rice equation
        def objective(v):
            return self._rachford_rice(v, z, initial_K)
            
        v = fsolve(objective, 0.5)[0]
        
        # Calculate phase compositions
        K = initial_K
        x = z / (1 + v*(K - 1))  # liquid
        y = K * x                # vapor
        
        return {
            "vapor_fraction": v,
            "liquid_composition": dict(zip(self.components.keys(), x)),
            "vapor_composition": dict(zip(self.components.keys(), y)),
            "K_values": dict(zip(self.components.keys(), K))
        }
        
    def _peng_robinson_z(self, P: float, T: float,
                        z: np.ndarray) -> float:
        """Solve Peng-Robinson EoS"""
        R = 8.3145  # Gas constant
        
        # Calculate a and b parameters
        a = self._pr_a_mixture(T, z)
        b = self._pr_b_mixture(z)
        
        # Cubic equation coefficients
        A = a*P/(R*T)**2
        B = b*P/(R*T)
        
        # Solve cubic equation Z³ - (1-B)Z² + (A-3B²-2B)Z - (AB-B²-B³) = 0
        coeff = [1, -(1-B), (A-3*B**2-2*B), -(A*B-B**2-B**3)]
        roots = np.roots(coeff)
        
        # Select appropriate root
        real_roots = roots[np.abs(roots.imag) < 1e-10].real
        return np.max(real_roots)  # vapor phase Z-factor
        
    def _pr_a_mixture(self, T: float, z: np.ndarray) -> float:
        """Calculate Peng-Robinson a parameter for mixture"""
        n = len(self.components)
        a = np.zeros((n,n))
        
        for i, (name_i, comp_i) in enumerate(self.components.items()):
            for j, (name_j, comp_j) in enumerate(self.components.items()):
                a_i = self._pr_a_pure(T, comp_i)
                a_j = self._pr_a_pure(T, comp_j)
                
                if i != j:
                    kij = self.binary_interactions[i,j]
                    a[i,j] = np.sqrt(a_i * a_j) * (1 - kij)
                else:
                    a[i,j] = a_i
                    
        return np.sum(np.outer(z, z) * a)
        
    def _pr_a_pure(self, T: float, component: Dict) -> float:
        """Calculate Peng-Robinson a parameter for pure component"""
        Tc = component["Tc"]
        Pc = component["Pc"]
        omega = component["omega"]
        R = 8.3145
        
        # Constants for PR EoS
        ac = 0.45724 * R**2 * Tc**2 / Pc
        kappa = 0.37464 + 1.54226*omega - 0.26992*omega**2
        alpha = (1 + kappa*(1 - np.sqrt(T/Tc)))**2
        
        return ac * alpha
        
    def _pr_b_mixture(self, z: np.ndarray) -> float:
        """Calculate Peng-Robinson b parameter for mixture"""
        b = np.array([self._pr_b_pure(comp) 
                     for comp in self.components.values()])
        return np.sum(z * b)
        
    def _pr_b_pure(self, component: Dict) -> float:
        """Calculate Peng-Robinson b parameter for pure component"""
        R = 8.3145
        return 0.07780 * R * component["Tc"] / component["Pc"]
        
    def _wilson_k_values(self, P: float, T: float) -> np.ndarray:
        """Calculate Wilson K-values for initial guess"""
        K = np.zeros(len(self.components))
        for i, comp in enumerate(self.components.values()):
            Pc = comp["Pc"]
            Tc = comp["Tc"]
            omega = comp["omega"]
            K[i] = (Pc/P) * np.exp(5.37*(1 + omega)*(1 - Tc/T))
        return K
        
    def _rachford_rice(self, v: float, z: np.ndarray,
                      K: np.ndarray) -> float:
        """Rachford-Rice equation for flash calculations"""
        return np.sum(z * (K - 1)/(1 + v*(K - 1)))
        
    def _srk_z(self, P: float, T: float, z: np.ndarray) -> float:
        """Solve Soave-Redlich-Kwong EoS"""
        # Implementation similar to PR but with SRK parameters
        pass
