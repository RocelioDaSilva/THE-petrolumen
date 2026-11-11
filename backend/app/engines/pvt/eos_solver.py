import math
from typing import Dict, Optional

import numpy as np

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
        interactions = np.asarray(kij, dtype=float)
        if interactions.shape != (n, n) or not np.all(np.isfinite(interactions)):
            raise ValueError("Invalid binary interaction matrix shape")
        self.binary_interactions = interactions

    def _composition_vector(self, composition: Dict[str, float]) -> np.ndarray:
        if not self.components:
            raise ValueError("At least one component must be configured.")
        if set(composition) != set(self.components):
            raise ValueError("Composition keys must match configured components.")
        values = np.asarray([composition[name] for name in self.components], dtype=float)
        if (
            not np.all(np.isfinite(values))
            or np.any(values < 0)
            or not math.isclose(float(values.sum()), 1.0, rel_tol=1e-6, abs_tol=1e-8)
        ):
            raise ValueError("Mole fractions must be finite, non-negative, and sum to 1.")
        return values

    def calculate_z_factor(self, P: float, T: float,
                          composition: Dict[str, float]) -> float:
        """Calculate compressibility factor"""
        if not math.isfinite(P) or P <= 0 or not math.isfinite(T) or T <= 0:
            raise ValueError("Pressure and temperature must be finite and positive.")
        z = self._composition_vector(composition)
        
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
        """Perform a Wilson-K/Rachford-Rice isothermal flash.

        Wilson K-values are held fixed; this is a screening flash, not a
        fugacity-iterated thermodynamic-equilibrium calculation.
        """
        if not math.isfinite(P) or P <= 0 or not math.isfinite(T) or T <= 0:
            raise ValueError("Pressure and temperature must be finite and positive.")
        z = self._composition_vector(composition)
        K = (
            self._wilson_k_values(P, T)
            if initial_K is None
            else np.asarray(initial_K, dtype=float)
        )
        if K.shape != z.shape or not np.all(np.isfinite(K)) or np.any(K <= 0):
            raise ValueError("K-values must be finite, positive, and match the mixture.")

        rr_at_liquid = self._rachford_rice(0.0, z, K)
        rr_at_vapor = self._rachford_rice(1.0, z, K)
        if rr_at_liquid <= 0:
            vapor_fraction = 0.0
            phase = "liquid"
            liquid = z
            vapor = None
        elif rr_at_vapor >= 0:
            vapor_fraction = 1.0
            phase = "vapor"
            liquid = None
            vapor = z
        else:
            lower, upper = 0.0, 1.0
            for _ in range(100):
                vapor_fraction = (lower + upper) / 2.0
                residual = self._rachford_rice(vapor_fraction, z, K)
                if abs(residual) <= 1e-12:
                    break
                if residual > 0:
                    lower = vapor_fraction
                else:
                    upper = vapor_fraction
            else:
                raise ArithmeticError("Rachford-Rice flash did not converge.")

            liquid = z / (1.0 + vapor_fraction * (K - 1.0))
            vapor = K * liquid
            liquid /= liquid.sum()
            vapor /= vapor.sum()
            phase = "two_phase"

        names = list(self.components)
        return {
            "phase": phase,
            "vapor_fraction": float(vapor_fraction),
            "liquid_composition": (
                dict(zip(names, liquid.tolist())) if liquid is not None else None
            ),
            "vapor_composition": (
                dict(zip(names, vapor.tolist())) if vapor is not None else None
            ),
            "K_values": dict(zip(names, K.tolist())),
        }

    def _rachford_rice(
        self, vapor_fraction: float, z: np.ndarray, K: np.ndarray
    ) -> float:
        denominator = 1.0 + vapor_fraction * (K - 1.0)
        return float(np.sum(z * (K - 1.0) / denominator))
        
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
        if real_roots.size == 0:
            raise ValueError("Peng-Robinson EoS produced no real compressibility roots.")
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
                    kij = self._binary_interactions()[i, j]
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
        if not math.isfinite(P) or P <= 0 or not math.isfinite(T) or T <= 0:
            raise ValueError("Pressure and temperature must be finite and positive.")
        K = np.zeros(len(self.components))
        for i, comp in enumerate(self.components.values()):
            Pc = comp["Pc"]
            Tc = comp["Tc"]
            omega = comp["omega"]
            K[i] = (Pc/P) * np.exp(5.37*(1 + omega)*(1 - Tc/T))
        return K

    def _binary_interactions(self) -> np.ndarray:
        if self.binary_interactions is None:
            count = len(self.components)
            return np.zeros((count, count))
        return self.binary_interactions
        
    def _srk_z(self, P: float, T: float, z: np.ndarray) -> float:
        """Calculate vapor-root compressibility from the SRK cubic EOS."""
        R = 8.3145
        a = np.zeros((len(self.components), len(self.components)))
        b = np.zeros(len(self.components))

        for i, component in enumerate(self.components.values()):
            tc = component["Tc"]
            pc = component["Pc"]
            omega = component["omega"]
            m = 0.480 + 1.574 * omega - 0.176 * omega**2
            alpha = (1.0 + m * (1.0 - math.sqrt(T / tc))) ** 2
            a[i, i] = 0.42747 * R**2 * tc**2 / pc * alpha
            b[i] = 0.08664 * R * tc / pc

        interactions = self._binary_interactions()
        for i in range(len(self.components)):
            for j in range(i + 1, len(self.components)):
                a_ij = math.sqrt(a[i, i] * a[j, j]) * (1.0 - interactions[i, j])
                a[i, j] = a[j, i] = a_ij

        a_mix = float(np.sum(np.outer(z, z) * a))
        b_mix = float(np.dot(z, b))
        A = a_mix * P / (R * T) ** 2
        B = b_mix * P / (R * T)
        roots = np.roots([1.0, -1.0, A - B - B**2, -A * B])
        real_roots = roots[np.abs(roots.imag) < 1e-10].real
        if real_roots.size == 0:
            raise ValueError("SRK EoS produced no real compressibility roots.")
        return float(np.max(real_roots))
