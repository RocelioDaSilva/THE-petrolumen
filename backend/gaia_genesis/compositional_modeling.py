"""
Compositional Modeling Module

This module provides advanced compositional modeling capabilities for reservoir simulation,
including equation of state calculations, phase behavior, and component tracking.
"""

import numpy as np
from typing import Dict, List, Tuple  # Removed Optional, Union, Any

# from scipy.optimize import minimize, fsolve # Removed unused import
# import numba # Removed unused import


class Component:
    """Class representing a hydrocarbon component."""

    def __init__(
        self,
        name: str,
        mw: float,
        tc: float,
        pc: float,
        omega: float,
        volume_shift: float = 0.0,
        parachor: float = 0.0,
    ):
        """
        Initialize component.

        Args:
            name: Component name
            mw: Molecular weight (g/mol)
            tc: Critical temperature (K)
            pc: Critical pressure (bar)
            omega: Acentric factor
            volume_shift: Volume shift parameter
            parachor: Parachor parameter for IFT calculation
        """
        self.name = name
        self.mw = mw
        self.tc = tc
        self.pc = pc
        self.omega = omega
        self.volume_shift = volume_shift
        self.parachor = parachor

        # Derived properties
        self.vc = None  # Critical volume
        self.zc = None  # Critical compressibility

        # Binary interaction parameters
        self.kij = {}  # Dictionary of binary interaction parameters


class EquationOfState:
    """Base class for equation of state models."""

    def __init__(self, components: List[Component]):
        """
        Initialize EOS model.

        Args:
            components: List of components
        """
        self.components = components
        self.n_components = len(components)

        # Initialize binary interaction matrix
        self.kij = np.zeros((self.n_components, self.n_components))

        # Set up binary interaction parameters
        for i, comp_i in enumerate(components):
            for j, comp_j in enumerate(components):
                if comp_j.name in comp_i.kij:
                    self.kij[i, j] = comp_i.kij[comp_j.name]
                    self.kij[j, i] = self.kij[i, j]  # Symmetry

    def calculate_z_factor(
        self, p: float, t: float, composition: np.ndarray
    ) -> Tuple[float, float]:
        """
        Calculate compressibility factors for vapor and liquid phases.

        Args:
            p: Pressure (bar)
            t: Temperature (K)
            composition: Mole fractions of components

        Returns:
            Tuple of (z_vapor, z_liquid)
        """
        raise NotImplementedError("Subclasses must implement this method")

    def calculate_fugacity_coefficients(
        self, p: float, t: float, z: float, composition: np.ndarray
    ) -> np.ndarray:
        """
        Calculate fugacity coefficients.

        Args:
            p: Pressure (bar)
            t: Temperature (K)
            z: Compressibility factor
            composition: Mole fractions of components

        Returns:
            Array of fugacity coefficients
        """
        raise NotImplementedError("Subclasses must implement this method")

    def calculate_phase_densities(
        self,
        p: float,
        t: float,
        zv: float,
        zl: float,
        composition_v: np.ndarray,
        composition_l: np.ndarray,
    ) -> Tuple[float, float]:
        """
        Calculate phase densities.

        Args:
            p: Pressure (bar)
            t: Temperature (K)
            zv: Vapor compressibility factor
            zl: Liquid compressibility factor
            composition_v: Vapor phase composition
            composition_l: Liquid phase composition

        Returns:
            Tuple of (vapor_density, liquid_density) in kg/m³
        """
        # Calculate molecular weights
        mw_v = sum(comp.mw * composition_v[i] for i, comp in enumerate(self.components))
        mw_l = sum(comp.mw * composition_l[i] for i, comp in enumerate(self.components))

        # Convert pressure from bar to Pa
        p_pa = p * 1e5

        # Gas constant (J/mol/K)
        R_const = 8.3145

        # Calculate densities
        rho_v = p_pa * mw_v / (zv * R_const * t) / 1000  # kg/m³
        rho_l = p_pa * mw_l / (zl * R_const * t) / 1000  # kg/m³

        return rho_v, rho_l


class PengRobinsonEOS(EquationOfState):
    """Peng-Robinson equation of state."""

    def __init__(self, components: List[Component]):
        """Initialize Peng-Robinson EOS."""
        super().__init__(components)

        # Peng-Robinson constants
        self.omega_a = 0.45724
        self.omega_b = 0.07780

    def calculate_z_factor(
        self, p: float, t: float, composition: np.ndarray
    ) -> Tuple[float, float]:
        """Calculate compressibility factors for vapor and liquid phases."""
        # Calculate mixture parameters
        a_mix, b_mix = self._calculate_mixture_parameters(p, t, composition)

        # Convert pressure to Pa
        p_pa = p * 1e5

        # Gas constant (J/mol/K)
        R_const = 8.3145

        # Calculate coefficients for cubic equation
        A = a_mix * p_pa / (R_const * t) ** 2
        B = b_mix * p_pa / (R_const * t)

        # Cubic equation coefficients: Z³ - (1-B)Z² + (A-3B²-2B)Z - (AB-B²-B³) = 0
        a2 = -(1 - B)
        a1 = A - 3 * B**2 - 2 * B
        a0 = -(A * B - B**2 - B**3)

        # Solve cubic equation
        roots = np.roots([1, a2, a1, a0])

        # Filter real roots
        real_roots = roots[np.isreal(roots)].real

        if len(real_roots) == 1:
            # Only one real root - single phase
            return real_roots[0], real_roots[0]
        else:
            # Multiple real roots - two phases
            # Vapor phase has highest Z, liquid phase has lowest Z
            z_vapor = np.max(real_roots)
            z_liquid = np.min(real_roots)
            return z_vapor, z_liquid

    def calculate_fugacity_coefficients(
        self, p: float, t: float, z: float, composition: np.ndarray
    ) -> np.ndarray:
        """Calculate fugacity coefficients."""
        R_const = 8.3145  # Define R_const at the beginning of the method scope

        # Calculate mixture parameters
        a_mix, b_mix = self._calculate_mixture_parameters(p, t, composition)

        # Calculate individual a and b parameters
        a_i = np.zeros(self.n_components)
        b_i = np.zeros(self.n_components)

        for i, comp in enumerate(self.components):
            # Calculate a_i and b_i
            Tr = t / comp.tc
            alpha = (
                1
                + (0.37464 + 1.54226 * comp.omega - 0.26992 * comp.omega**2)
                * (1 - np.sqrt(Tr))
            ) ** 2
            # R_const was defined at the start of this method.
            a_i[i] = (
                self.omega_a * (R_const * comp.tc) ** 2 / comp.pc * alpha
            )  # noqa: F821
            b_i[i] = self.omega_b * R_const * comp.tc / comp.pc  # noqa: F821

        # Calculate a_ij matrix
        a_ij = np.zeros((self.n_components, self.n_components))
        for i in range(self.n_components):
            for j in range(self.n_components):
                a_ij[i, j] = np.sqrt(a_i[i] * a_i[j]) * (1 - self.kij[i, j])

        # Calculate fugacity coefficients
        ln_phi = np.zeros(self.n_components)

        # R_const is now defined at the top of the method.
        # Gas constant (J/mol/K) - needs to be defined in this scope
        # R_const = 8.3145 # Removed redundant definition
        # Convert pressure to Pa for A and B calculation
        p_pa = p * 1e5

        # Calculate A and B for the mixture (similar to calculate_z_factor)
        # a_mix, b_mix are already available from _calculate_mixture_parameters call
        A_param = a_mix * p_pa / (R_const * t) ** 2
        B_param = b_mix * p_pa / (R_const * t)

        for i in range(self.n_components):
            # Calculate sum terms
            sum_a = 0
            for j in range(self.n_components):
                sum_a += (
                    composition[j] * a_ij[i, j]
                )  # a_ij is correctly calculated above

            # Calculate fugacity coefficient using A_param and B_param
            term1 = b_i[i] / b_mix * (z - 1)
            term2 = -np.log(z - B_param)  # Use B_param

            # Check for B_param being close to zero to avoid division by zero
            if abs(B_param) < 1e-9:  # or some small epsilon
                term3 = (
                    0  # or handle appropriately, this part of equation might simplify
                )
            else:
                term3 = (
                    A_param  # Use A_param
                    / (2 * np.sqrt(2) * B_param)  # Use B_param
                    * (b_i[i] / b_mix - 2 * sum_a / a_mix)
                    * np.log(
                        (z + (1 + np.sqrt(2)) * B_param)
                        / (z + (1 - np.sqrt(2)) * B_param)
                    )  # Use B_param
                )

            ln_phi[i] = term1 + term2 + term3

        return np.exp(ln_phi)

    def _calculate_mixture_parameters(
        self, p: float, t: float, composition: np.ndarray
    ) -> Tuple[float, float]:
        """Calculate mixture parameters a_mix and b_mix."""
        # Gas constant (J/mol/K)
        R_const = 8.3145

        # Initialize mixture parameters
        a_mix = 0.0
        b_mix = 0.0

        # Calculate individual a and b parameters
        a_i = np.zeros(self.n_components)
        b_i = np.zeros(self.n_components)

        for i, comp in enumerate(self.components):
            # Calculate a_i and b_i
            Tr = t / comp.tc
            alpha = (
                1
                + (0.37464 + 1.54226 * comp.omega - 0.26992 * comp.omega**2)
                * (1 - np.sqrt(Tr))
            ) ** 2
            a_i[i] = self.omega_a * (R_const * comp.tc) ** 2 / comp.pc * alpha
            b_i[i] = self.omega_b * R_const * comp.tc / comp.pc

            # Add to b_mix
            b_mix += composition[i] * b_i[i]

        # Calculate a_mix
        for i in range(self.n_components):
            for j in range(self.n_components):
                a_mix += (
                    composition[i]
                    * composition[j]
                    * np.sqrt(a_i[i] * a_i[j])
                    * (1 - self.kij[i, j])
                )

        return a_mix, b_mix


class FlashCalculation:
    """Class for performing flash calculations."""

    def __init__(self, eos: EquationOfState):
        """
        Initialize flash calculation.

        Args:
            eos: Equation of state model
        """
        self.eos = eos
        self.tolerance = 1e-8
        self.max_iterations = 100

    def perform_flash(
        self, p: float, t: float, overall_composition: np.ndarray
    ) -> Dict:
        """
        Perform flash calculation.

        Args:
            p: Pressure (bar)
            t: Temperature (K)
            overall_composition: Overall composition (mole fractions)

        Returns:
            Dictionary with flash results
        """
        # Normalize composition
        z = overall_composition / np.sum(overall_composition)

        # Check for trivial cases
        if np.all(z < self.tolerance):
            return {
                "phase": "none",
                "vapor_fraction": 0.0,
                "vapor_composition": z,
                "liquid_composition": z,
            }

        # Calculate K-values
        k_values = self._estimate_k_values(p, t, z)

        # Perform Rachford-Rice iteration
        vapor_fraction, converged = self._rachford_rice(z, k_values)

        if not converged:
            # Try with different initial K-values
            k_values = self._estimate_k_values_wilson(p, t)
            vapor_fraction, converged = self._rachford_rice(z, k_values)

        # Calculate phase compositions
        vapor_composition = np.zeros_like(z)
        liquid_composition = np.zeros_like(z)

        for i in range(len(z)):
            vapor_composition[i] = (
                z[i] * k_values[i] / (1 + vapor_fraction * (k_values[i] - 1))
            )
            liquid_composition[i] = z[i] / (1 + vapor_fraction * (k_values[i] - 1))

        # Normalize phase compositions
        vapor_composition /= np.sum(vapor_composition)
        liquid_composition /= np.sum(liquid_composition)

        # Calculate compressibility factors
        z_vapor, z_liquid = self.eos.calculate_z_factor(p, t, vapor_composition)

        # Calculate phase densities
        rho_vapor, rho_liquid = self.eos.calculate_phase_densities(
            p, t, z_vapor, z_liquid, vapor_composition, liquid_composition
        )

        # Determine phase state
        if vapor_fraction < self.tolerance:
            phase = "liquid"
        elif vapor_fraction > 1 - self.tolerance:
            phase = "vapor"
        else:
            phase = "two-phase"

        return {
            "phase": phase,
            "vapor_fraction": vapor_fraction,
            "vapor_composition": vapor_composition,
            "liquid_composition": liquid_composition,
            "z_vapor": z_vapor,
            "z_liquid": z_liquid,
            "rho_vapor": rho_vapor,
            "rho_liquid": rho_liquid,
            "k_values": k_values,
        }

    def _estimate_k_values(self, p: float, t: float, z: np.ndarray) -> np.ndarray:
        """Estimate K-values using EOS."""
        # Calculate compressibility factors
        z_vapor, z_liquid = self.eos.calculate_z_factor(p, t, z)

        # Calculate fugacity coefficients
        phi_vapor = self.eos.calculate_fugacity_coefficients(p, t, z_vapor, z)
        phi_liquid = self.eos.calculate_fugacity_coefficients(p, t, z_liquid, z)

        # Calculate K-values
        k_values = phi_liquid / phi_vapor

        return k_values

    def _estimate_k_values_wilson(self, p: float, t: float) -> np.ndarray:
        """Estimate K-values using Wilson correlation."""
        k_values = np.zeros(self.eos.n_components)

        for i, comp in enumerate(self.eos.components):
            # Wilson correlation
            k_values[i] = (comp.pc / p) * np.exp(
                5.37 * (1 + comp.omega) * (1 - comp.tc / t)
            )

        return k_values

    def _rachford_rice(self, z: np.ndarray, k_values: np.ndarray) -> Tuple[float, bool]:
        """
        Solve Rachford-Rice equation.

        Args:
            z: Overall composition
            k_values: K-values

        Returns:
            Tuple of (vapor_fraction, converged)
        """
        # Find bounds for vapor fraction
        beta_min = max(
            0,
            max(
                (k_values * z - 1) / (k_values - 1)
                for i, k in enumerate(k_values)
                if k < 1
            ),
        )
        beta_max = min(
            1, min((1 - z) / (1 - k_values) for i, k in enumerate(k_values) if k > 1)
        )

        if beta_min >= beta_max:
            # Single phase
            if np.sum(z * k_values) > 1:
                return 1.0, True  # All vapor
            else:
                return 0.0, True  # All liquid

        # Initial guess
        beta = (beta_min + beta_max) / 2

        # Rachford-Rice iteration
        for iteration in range(self.max_iterations):
            # Calculate function value
            f = np.sum(z * (k_values - 1) / (1 + beta * (k_values - 1)))

            if abs(f) < self.tolerance:
                return beta, True

            # Calculate derivative
            df = -np.sum(z * (k_values - 1) ** 2 / (1 + beta * (k_values - 1)) ** 2)

            # Newton update
            delta_beta = -f / df

            # Limit step size
            if abs(delta_beta) > 0.1:
                delta_beta = 0.1 * np.sign(delta_beta)

            # Update beta
            beta_new = beta + delta_beta

            # Check bounds
            if beta_new < beta_min:
                beta = (beta + beta_min) / 2
            elif beta_new > beta_max:
                beta = (beta + beta_max) / 2
            else:
                beta = beta_new

        return beta, False


class CompositionalModel:
    """Compositional model for reservoir simulation."""

    def __init__(self, components: List[Component], eos_type: str = "PR"):
        """
        Initialize compositional model.

        Args:
            components: List of components
            eos_type: Equation of state type ('PR' for Peng-Robinson)
        """
        self.components = components
        self.n_components = len(components)

        # Initialize EOS
        if eos_type == "PR":
            self.eos = PengRobinsonEOS(components)
        else:
            raise ValueError(f"Unsupported EOS type: {eos_type}")

        # Initialize flash calculation
        self.flash = FlashCalculation(self.eos)

        # Initialize component properties
        self.component_names = [comp.name for comp in components]
        self.molecular_weights = np.array([comp.mw for comp in components])

    def perform_flash(self, p: float, t: float, composition: np.ndarray) -> Dict:
        """
        Perform flash calculation.

        Args:
            p: Pressure (bar)
            t: Temperature (K)
            composition: Composition (mole fractions)

        Returns:
            Flash results
        """
        return self.flash.perform_flash(p, t, composition)

    def calculate_phase_properties(
        self, p: float, t: float, flash_results: Dict
    ) -> Dict:
        """
        Calculate phase properties.

        Args:
            p: Pressure (bar)
            t: Temperature (K)
            flash_results: Flash calculation results

        Returns:
            Dictionary of phase properties
        """
        # Extract phase compositions
        y = flash_results["vapor_composition"]
        x = flash_results["liquid_composition"]

        # Calculate molecular weights
        mw_vapor = np.sum(y * self.molecular_weights)
        mw_liquid = np.sum(x * self.molecular_weights)

        # Calculate phase densities
        rho_vapor = flash_results["rho_vapor"]
        rho_liquid = flash_results["rho_liquid"]

        # Calculate phase viscosities (simplified correlations)
        mu_vapor = self._calculate_gas_viscosity(p, t, y)
        mu_liquid = self._calculate_liquid_viscosity(p, t, x)

        return {
            "molecular_weight": {"vapor": mw_vapor, "liquid": mw_liquid},
            "density": {"vapor": rho_vapor, "liquid": rho_liquid},
            "viscosity": {"vapor": mu_vapor, "liquid": mu_liquid},
            "compressibility": {
                "vapor": flash_results["z_vapor"],
                "liquid": flash_results["z_liquid"],
            },
        }

    def _calculate_gas_viscosity(
        self, p: float, t: float, composition: np.ndarray
    ) -> float:
        """Calculate gas viscosity using simplified correlation."""
        # This is a placeholder - in a real simulator, this would use
        # a more sophisticated model like the Lohrenz-Bray-Clark correlation
        return 0.02  # cP

    def _calculate_liquid_viscosity(
        self, p: float, t: float, composition: np.ndarray
    ) -> float:
        """Calculate liquid viscosity using simplified correlation."""
        # This is a placeholder - in a real simulator, this would use
        # a more sophisticated model
        return 0.5  # cP
