import numpy as np
from typing import Tuple, Optional, List, Dict
import scipy.optimize as opt
from scipy.optimize import fsolve


def pseudocritical_props(gamma_g: float) -> Tuple[float, float]:
    """
    Sutton (1985) correlation for pseudocritical properties.
    Args:
        gamma_g (float): Gas specific gravity (air = 1.0)
    Returns:
        tuple: (Tpc, Ppc) in Rankine and psia.
    """
    Tpc = 169.2 + 349.5 * gamma_g - 74.0 * gamma_g**2
    Ppc = 756.8 - 131.0 * gamma_g - 3.6 * gamma_g**2
    return Tpc, Ppc


def zfactor_dak(
    Tpr: float, Ppr: float, tol: float = 1e-6, max_iter: int = 100
) -> float:
    """
    Dranchuk-Abou-Kassem (1975) correlation for Z-factor using Newton-Raphson.
    """
    A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11 = (
        0.3265,
        -1.0700,
        -0.5339,
        0.01569,
        -0.05165,
        0.5475,
        -0.7361,
        0.1844,
        0.1056,
        0.6134,
        0.7210,
    )
    rho_r = 0.27 * Ppr / Tpr  # initial guess
    for _ in range(max_iter):
        term1 = (A1 + A2 / Tpr + A3 / Tpr**3 + A4 / Tpr**4 + A5 / Tpr**5) * rho_r
        term2 = (A6 + A7 / Tpr + A8 / Tpr**2) * rho_r**2
        term3 = A9 * (A7 / Tpr + A8 / Tpr**2) * rho_r**5
        term4 = (
            (A10 / Tpr**3) * rho_r**2 * (1 + A11 * rho_r**2) * np.exp(-A11 * rho_r**2)
        )
        Z = 1 + term1 + term2 + term3 + term4
        f = Z - 0.27 * Ppr / (rho_r * Tpr)
        dZ_drho = (
            (A1 + A2 / Tpr + A3 / Tpr**3 + A4 / Tpr**4 + A5 / Tpr**5)
            + 2 * (A6 + A7 / Tpr + A8 / Tpr**2) * rho_r
            + 5 * A9 * (A7 / Tpr + A8 / Tpr**2) * rho_r**4
            + (2 * A10 * rho_r / Tpr**3)
            * (1 + A11 * rho_r**2 - (A11 * rho_r**2) ** 2)
            * np.exp(-A11 * rho_r**2)
        )
        df = dZ_drho + 0.27 * Ppr / (rho_r**2 * Tpr)
        rho_r_new = rho_r - f / df
        if abs(rho_r_new - rho_r) < tol:
            return 0.27 * Ppr / (rho_r_new * Tpr)
        rho_r = rho_r_new
    return 1.0


def zfactor_hall_yarborough(Tpr: float, Ppr: float) -> float:
    """
    Hall-Yarborough (1973) correlation for Z-factor.
    """
    t = 1.0 / Tpr
    A = 0.06125 * t * np.exp(-1.2 * (1 - t) ** 2)
    B = t * (14.76 - 9.76 * t + 4.58 * t**2)
    C = t * (90.7 - 242.2 * t + 42.4 * t**2)
    D = 2.18 + 2.82 * t

    def func(y):
        return -A * Ppr + (y + y**2 + y**3 + y**4) / (1 - y) ** 3 - B * y**2 + C * y**D

    y = opt.fsolve(func, 0.01)[0]
    Z = A * Ppr / y
    return Z


def calculate_zfactor(P: float, T_f: float, gamma_g: float) -> float:
    T_r = T_f + 459.67
    Tpc, Ppc = pseudocritical_props(gamma_g)
    Tpr = T_r / Tpc
    Ppr = P / Ppc
    return zfactor_dak(Tpr, Ppr)


def gas_viscosity_lee(P: float, T_f: float, gamma_g: float, z: float) -> float:
    """
    Lee, Gonzalez, and Eakin (1966) correlation.
    """
    T_r = T_f + 459.67
    MW = 28.96 * gamma_g
    rho_g = (P * MW) / (z * 10.732 * T_r) / 62.43  # g/cm3
    X = 3.5 + 986 / T_r + 0.01 * MW
    Y = 2.4 - 0.2 * X
    K = (9.4 + 0.02 * MW) * T_r**1.5 / (209 + 19 * MW + T_r)
    return K * 1e-4 * np.exp(X * rho_g**Y)


def oil_bubble_point_standing(
    Rs: float, gamma_g: float, api: float, T_f: float
) -> float:
    """
    Standing (1947) bubble point correlation.
    """
    a = 0.00091 * T_f - 0.0125 * api
    return 18.2 * ((Rs / gamma_g) ** 0.83 * 10**a - 1.4)


def oil_bubble_point_glaso(Rs: float, gamma_g: float, api: float, T_f: float) -> float:
    """
    Glaso (1980) bubble point correlation.
    """
    Pb_star = (Rs / gamma_g) ** 0.816 * (T_f**0.172) * (api**-0.989)
    y = 1.7669 + 1.7447 * np.log10(Pb_star) - 0.30218 * (np.log10(Pb_star) ** 2)
    return 10**y


def oil_bubble_point_petrosky(
    Rs: float, gamma_g: float, api: float, T_f: float
) -> float:
    """
    Petrosky-Farshad (1993) bubble point correlation.
    """
    a = Rs / (1.0513e-4 * gamma_g**1.468)
    return (a ** (1 / 0.680)) * 10 ** (-0.000302 * T_f) * 10 ** (-0.00114 * api)


def solution_gor_standing(P: float, gamma_g: float, api: float, T_f: float) -> float:
    """
    Standing (1947) solution GOR correlation.
    """
    a = 0.0125 * api - 0.00091 * T_f
    return gamma_g * ((P / 18.2 + 1.4) * 10**-a) ** 1.2048


def oil_fvf_standing(Rs: float, gamma_g: float, gamma_o: float, T_f: float) -> float:
    """
    Standing (1947) oil FVF correlation.
    """
    F = Rs * (gamma_g / gamma_o) ** 0.5 + 1.25 * T_f
    return 0.9759 + 0.000120 * F**1.2


def dead_oil_viscosity_beggs_robinson(api: float, T_f: float) -> float:
    """
    Beggs-Robinson (1975) dead oil viscosity.
    """
    X = 10 ** (3.0324 - 0.02023 * api) * T_f**-1.163
    return 10**X - 1


def live_oil_viscosity_beggs_robinson(mu_od: float, Rs: float) -> float:
    """
    Beggs-Robinson (1975) live oil viscosity.
    """
    A = 10.715 * (Rs + 100) ** -0.515
    B = 5.44 * (Rs + 150) ** -0.338
    return A * mu_od**B


def water_pvt_mccain(P: float, T_f: float) -> Tuple[float, float, float]:
    """
    McCain (1990) water PVT (Bw, mu_w, Rsw).
    """
    # Bw calculation
    dV_wt = -1.0001e-2 + 1.33391e-4 * T_f + 5.50654e-7 * T_f**2
    dV_wp = (
        -1.95301e-9 * P * T_f
        - 1.72834e-13 * P**2 * T_f
        - 3.58922e-7 * P
        - 2.25341e-10 * P**2
    )
    Bw = (1 + dV_wt) * (1 + dV_wp)

    # mu_w calculation
    mu_w = np.exp(1.003 - 1.479e-2 * T_f + 1.982e-5 * T_f**2)
    # Rsw calculation (simplified)
    Rsw = 0.0  # scf/stb
    return Bw, mu_w, Rsw


class EosSolver:
    """Equation of State solver for compositional simulation.
    Integrated from potential features.
    """

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
            "MW": properties.get("molecular_weight", 0.0),
        }

    def set_binary_interactions(self, kij: np.ndarray):
        """Set binary interaction parameters"""
        n = len(self.components)
        if kij.shape != (n, n):
            raise ValueError("Invalid binary interaction matrix shape")
        self.binary_interactions = kij

    def calculate_z_factor(self, P: float, T: float, composition: Dict[str, float]) -> float:
        """Calculate compressibility factor"""
        z = np.array([composition[c] for c in self.components])
        if self.eos_type == "PR":
            return self._peng_robinson_z(P, T, z)
        else:
            raise ValueError(f"Unknown EoS type: {self.eos_type}")

    def flash_calculation(
        self, P: float, T: float, composition: Dict[str, float], initial_K: Optional[np.ndarray] = None
    ) -> Dict:
        """Perform isothermal flash calculation"""
        z = np.array([composition[c] for c in self.components])
        if initial_K is None:
            initial_K = self._wilson_k_values(P, T)

        def objective(v):
            return np.sum(z * (initial_K - 1) / (1 + v * (initial_K - 1)))

        v = fsolve(objective, 0.5)[0]
        x = z / (1 + v * (initial_K - 1))
        y = initial_K * x
        return {
            "vapor_fraction": float(v),
            "liquid_composition": dict(zip(self.components.keys(), x.tolist())),
            "vapor_composition": dict(zip(self.components.keys(), y.tolist())),
        }

    def _peng_robinson_z(self, P: float, T: float, z: np.ndarray) -> float:
        R = 8.3145
        a = self._pr_a_mixture(T, z)
        b = self._pr_b_mixture(z)
        A = a * P / (R * T) ** 2
        B = b * P / (R * T)
        coeff = [1, -(1 - B), (A - 3 * B**2 - 2 * B), -(A * B - B**2 - B**3)]
        roots = np.roots(coeff)
        real_roots = roots[np.abs(roots.imag) < 1e-10].real
        return float(np.max(real_roots))

    def _pr_a_mixture(self, T: float, z: np.ndarray) -> float:
        n = len(self.components)
        a = np.zeros((n, n))
        comp_list = list(self.components.values())
        for i in range(n):
            for j in range(n):
                a_i = self._pr_a_pure(T, comp_list[i])
                a_j = self._pr_a_pure(T, comp_list[j])
                if i != j and self.binary_interactions is not None:
                    kij = self.binary_interactions[i, j]
                    a[i, j] = np.sqrt(a_i * a_j) * (1 - kij)
                else:
                    a[i, j] = np.sqrt(a_i * a_j)
        return float(np.sum(np.outer(z, z) * a))

    def _pr_a_pure(self, T: float, component: Dict) -> float:
        Tc, Pc, omega = component["Tc"], component["Pc"], component["omega"]
        R = 8.3145
        ac = 0.45724 * R**2 * Tc**2 / Pc
        kappa = 0.37464 + 1.54226 * omega - 0.26992 * omega**2
        alpha = (1 + kappa * (1 - np.sqrt(T / Tc))) ** 2
        return ac * alpha

    def _pr_b_mixture(self, z: np.ndarray) -> float:
        b = np.array([0.07780 * 8.3145 * c["Tc"] / c["Pc"] for c in self.components.values()])
        return float(np.sum(z * b))

    def _wilson_k_values(self, P: float, T: float) -> np.ndarray:
        K = np.zeros(len(self.components))
        for i, comp in enumerate(self.components.values()):
            K[i] = (comp["Pc"] / P) * np.exp(5.37 * (1 + comp["omega"]) * (1 - comp["Tc"] / T))
        return K
