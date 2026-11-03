import numpy as np

# import pandas as pd # Unused
from typing import Dict, Tuple, Optional  # Removed List, Union, Any
import matplotlib.pyplot as plt

# import seaborn as sns # Unused
# from scipy.stats import norm # Unused
from scipy.optimize import minimize  # minimize is used

# from scipy.interpolate import interp1d # Unused

# import streamlit as st # Unused import, causing ModuleNotFoundError if not installed
import datetime  # noqa: F401 # Used as module, but flake8 flags it.
import logging
from dataclasses import dataclass  # noqa: F401 # Used by @dataclass
from enum import Enum  # noqa: F401 # Used by ReserveCategory


class PVTProperties:
    """Classe para cálculo de propriedades PVT."""

    def __init__(self):
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("PVTProperties")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def calculate_formation_volume_factor(
        self,
        pressure: float,
        temperature: float,
        fluid_type: str,
        api_gravity: Optional[float] = None,
        gas_specific_gravity: Optional[float] = None,
    ) -> float:
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
        if fluid_type == "oil":
            # Correlação de Standing para Bo
            rs = self.calculate_solution_gas_ratio(
                pressure, temperature, api_gravity, gas_specific_gravity
            )
            f = rs * (gas_specific_gravity / 0.7) ** 0.5 + 1.25 * temperature
            bo = 0.972 + 0.000147 * f**1.175
            return bo
        else:  # gas
            # Real gas law for Bg. Z-factor from Hall-Yarborough.
            # Temperature must be in Rankine for this formula.
            t_rankine = temperature + 459.67  # Convert °F to °R
            z = self.calculate_z_factor(pressure, temperature, gas_specific_gravity)
            if np.isnan(z) or z <= 0 or pressure <= 0:
                self.logger.warning(
                    f"Invalid inputs for Bg calculation: Z={z}, P={pressure}, T_F={temperature}"
                )
                return np.nan
            bg = 0.02827 * z * t_rankine / pressure
            return bg

    def calculate_viscosity(
        self,
        pressure: float,
        temperature: float,
        fluid_type: str,
        api_gravity: Optional[float] = None,
        gas_specific_gravity: Optional[float] = None,
    ) -> float:
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
        if fluid_type == "oil":
            # Correlação de Beggs-Robinson para viscosidade do óleo
            api = api_gravity
            t = temperature

            # Viscosidade do óleo morto
            a = 10 ** (0.43 + 8.33 / api)
            mu_od = (0.32 + 1.8e7 / api**4.53) * (360 / (t + 200)) ** a

            # Viscosidade do óleo saturado
            rs = self.calculate_solution_gas_ratio(
                pressure, temperature, api_gravity, gas_specific_gravity
            )
            a = 10.715 * (rs + 100) ** -0.515
            b = 5.44 * (rs + 150) ** -0.338
            mu_o = a * mu_od**b

            return mu_o
        else:  # gas
            # Correlação de Lee-Gonzalez-Eakin para viscosidade do gás
            t_rankine = temperature + 460  # temperatura em Rankine
            mw = gas_specific_gravity * 28.97  # peso molecular

            z_gas = self.calculate_z_factor(pressure, temperature, gas_specific_gravity)

            if np.isnan(z_gas) or z_gas <= 0:
                self.logger.warning(
                    f"Invalid Z-factor ({z_gas}) for gas viscosity calculation. P={pressure}, T_F={temperature}, Sg={gas_specific_gravity}"
                )
                return np.nan

            # Gas density rho in lb/ft^3
            # R = 10.73 psia.ft^3/(lb-mol.R)
            # Ensure denominator is not zero
            den_rho = 10.73 * t_rankine * z_gas
            if den_rho == 0:
                self.logger.warning(
                    f"Zero denominator in density calculation for gas viscosity. P={pressure}, T_F={temperature}, Sg={gas_specific_gravity}, Z={z_gas}"
                )
                return np.nan

            rho_lb_ft3 = pressure * mw / den_rho

            # Convert density to g/cm^3 as Lee-Gonzalez-Eakin typically uses it
            rho_g_cm3 = rho_lb_ft3 / 62.428

            if rho_g_cm3 < 0:  # Density cannot be negative
                self.logger.warning(
                    f"Negative gas density ({rho_g_cm3} g/cm^3) for viscosity calc. P={pressure}, T_F={temperature}, Sg={gas_specific_gravity}, Z={z_gas}"
                )
                return np.nan

            # Lee-Gonzalez-Eakin correlation terms:
            # K, X, Y are intermediate parameters
            # Using t_rankine for temperature in these equations
            k_val = (9.4 + 0.02 * mw) * (t_rankine**1.5) / (209 + 19 * mw + t_rankine)
            x_val = 3.5 + (986 / t_rankine) + (0.01 * mw)
            y_val = 2.4 - 0.2 * x_val

            # The term rho_g_cm3**y_val can cause issues
            # If rho_g_cm3 is zero:
            if rho_g_cm3 == 0:
                if y_val > 0:
                    term_rho_pow_y = 0.0
                elif y_val == 0:
                    term_rho_pow_y = 1.0
                else:  # y_val < 0, 0 to a negative power is undefined/infinity
                    self.logger.warning(
                        f"rho_g_cm3 is zero and y_val ({y_val}) is negative in gas viscosity. P={pressure}, T_F={temperature}, Sg={gas_specific_gravity}"
                    )
                    return (
                        np.nan
                    )  # Or handle as appropriate (e.g., very large viscosity if it implies dense phase near zero density)
            else:  # rho_g_cm3 > 0 (negative handled above)
                try:
                    term_rho_pow_y = rho_g_cm3**y_val
                except ValueError:  # Should not happen if rho_g_cm3 is positive
                    self.logger.warning(
                        f"ValueError for rho_g_cm3**y_val with rho_g_cm3={rho_g_cm3}, y_val={y_val}. P={pressure}, T_F={temperature}, Sg={gas_specific_gravity}"
                    )
                    return np.nan

            exp_arg = x_val * term_rho_pow_y

            # Check for overflow before np.exp
            # Max typical float64 exp argument is around 709-710
            if exp_arg > 700:
                self.logger.warning(
                    f"Exponent argument for gas viscosity is too large ({exp_arg}). Result will overflow. P={pressure}, T_F={temperature}, Sg={gas_specific_gravity}"
                )
                # Depending on context, could return np.inf or a capped large value
                # For now, returning NaN as it indicates a likely issue with inputs or correlation applicability
                return np.nan

            try:
                mu_g = 1e-4 * k_val * np.exp(exp_arg)
            except OverflowError:
                self.logger.warning(
                    f"OverflowError during np.exp({exp_arg}) in gas viscosity. P={pressure}, T_F={temperature}, Sg={gas_specific_gravity}"
                )
                return np.nan

            if np.isnan(mu_g) or np.isinf(mu_g) or mu_g < 0:
                self.logger.warning(
                    f"Calculated gas viscosity is invalid: {mu_g}. P={pressure}, T_F={temperature}, Sg={gas_specific_gravity}"
                )
                return np.nan  # Return NaN for clearly non-physical results

            return mu_g

    def calculate_solution_gas_ratio(
        self,
        pressure: float,
        temperature: float,
        api_gravity: float,
        gas_specific_gravity: float,
    ) -> float:
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
        rs = yg * (pressure / 18.2 + 1.4) * 10**x
        return rs

    def calculate_z_factor(
        self, pressure: float, temperature: float, gas_specific_gravity: float
    ) -> float:
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

        if tr <= 0 or tpc <= 0:  # Avoid division by zero or log/exp domain errors
            self.logger.warning(
                f"Invalid T_r ({tr}) or T_pc ({tpc}). Cannot calculate Z-factor."
            )
            return np.nan  # Or raise an error

        # Hall-Yarborough constants
        # Y_const = (0.06125 * pr / tr) * np.exp(-1.2 * (1 - 1 / tr)**2) # This is Y in Z = Y/rho_r
        # The term exp(-1.2 * (1 - 1/Tr)^2) is used multiple times
        exp_term = np.exp(-1.2 * (1 - 1 / tr) ** 2)

        # Term Y from Z = Y / rho_r
        # Y_val = (0.06125 * pr / tr) * exp_term
        # Actually, the equation to solve is for rho_r (y in many texts)
        # f(y) = - (0.06125 * Pr / Tr) * exp_term + (y + y^2 + y^3 - y^4)/(1-y)^3 - C1*y^2 + C2*y^C3 = 0

        # Coefficients for the equation f(y) = 0
        # Note: Some formulations define C1, C2, C3 slightly differently (e.g. divided by Tr terms)
        # The form used here is consistent with many sources for f(rho_r) where rho_r is y.
        # f(y) = -Y_const + term_y_powers - term_C1 + term_C2 = 0

        # Y_const for the f(y) = 0 equation
        Y_const = (0.06125 * pr / tr) * exp_term

        # Newton-Raphson iteration to find reduced density 'y' (rho_r)
        # Initial guess for y (reduced density rho_r)
        # A common initial guess is based on Pr or a small value.
        # Using 0.001 as a simple initial guess, or something more sophisticated.
        # Let's use a slightly better one: y = 0.001 if Pr < 1.0 else 0.1 * Pr
        y = 0.001 if pr < 3.0 else 0.2 * pr  # Initial guess for reduced density rho_r
        if y >= 1.0:  # Ensure (1-y) is not zero or negative initially
            y = 0.5
        if y <= 0:  # Ensure y is positive
            y = 0.001

        # Parameters for f(y)
        # C1_coeff = 14.76 / tr - 9.76 / (tr**2) + 4.58 / (tr**3) # This is C1 in f(y)
        # C2_coeff = 90.7 / tr - 242.2 / (tr**2) + 42.4 / (tr**3) # This is C2 in f(y)
        # C3_exp = 2.18 + 2.82 / tr                             # This is C3 in f(y)

        # Coefficients for f(y) = -Y + A(y) - B(y) + D(y) = 0
        # Where:
        # Y = (0.06125 * Pr / Tr) * exp(-1.2 * (1 - 1/Tr)^2)
        # A(y) = (y + y^2 + y^3 - y^4) / (1-y)^3
        # B(y) = (14.76/Tr - 9.76/Tr^2 + 4.58/Tr^3) * y^2
        # D(y) = (90.7/Tr - 242.2/Tr^2 + 42.4/Tr^3) * y^(2.18 + 2.82/Tr)

        # Renaming for clarity with common literature for Hall-Yarborough
        # Reduced temperature Tr, Reduced pressure Pr
        # Equation for reduced density, rho_r (here, variable 'y')
        # f(rho_r) = - (0.06125 * Pr / Tr) * exp(-1.2*(1-1/Tr)^2) +
        #             (rho_r + rho_r^2 + rho_r^3 - rho_r^4) / (1-rho_r)^3 -
        #             (14.76/Tr - 9.76/Tr^2 + 4.58/Tr^3) * rho_r^2 +
        #             (90.7/Tr - 242.2/Tr^2 + 42.4/Tr^3) * rho_r^(2.18 + 2.82/Tr) = 0

        # Iteration parameters
        max_iter = 20  # Max iterations
        tolerance = 1e-9  # Tolerance for convergence

        for _ in range(max_iter):
            if y >= 1.0 or y <= 0:  # Avoid domain error for (1-y) or y in powers
                self.logger.warning(
                    f"Reduced density y = {y} out of (0,1) range during iteration. Pr={pr}, Tr={tr}"
                )
                return np.nan  # Or handle error appropriately

            # Calculate terms for f(y) and f'(y)
            # f(y) terms:
            term_Y = -Y_const
            term_A_num = y + y**2 + y**3 - y**4
            term_A_den = (1 - y) ** 3
            if term_A_den == 0:
                return np.nan  # Avoid division by zero
            term_A = term_A_num / term_A_den

            term_B_coeff = 14.76 / tr - 9.76 / (tr**2) + 4.58 / (tr**3)
            term_B = -term_B_coeff * y**2

            term_D_coeff = 90.7 / tr - 242.2 / (tr**2) + 42.4 / (tr**3)
            exponent_D = 2.18 + 2.82 / tr
            # Handle y=0 for y^exponent_D if exponent_D is non-integer or small
            if y == 0 and exponent_D <= 0:
                return np.nan  # Avoid math error
            term_D = term_D_coeff * (y**exponent_D if y > 0 else 0)

            f_y = term_Y + term_A + term_B + term_D

            # f'(y) terms (derivative of f(y) w.r.t y):
            # Derivative of term_A: (1 + 4y + 4y^2 - 4y^3 + y^4) / (1-y)^4
            fp_term_A_num = 1 + 4 * y + 4 * y**2 - 4 * y**3 + y**4
            fp_term_A_den = (1 - y) ** 4
            if fp_term_A_den == 0:
                return np.nan
            fp_term_A = fp_term_A_num / fp_term_A_den

            # Derivative of term_B: -2 * term_B_coeff * y
            fp_term_B = -2 * term_B_coeff * y

            # Derivative of term_D: term_D_coeff * exponent_D * y^(exponent_D - 1)
            if y == 0 and (exponent_D - 1) < 0:  # avoid 0 to negative power
                fp_term_D = 0  # or handle as large if exponent_D is between 0 and 1
            elif y > 0:
                fp_term_D = term_D_coeff * exponent_D * (y ** (exponent_D - 1))
            else:  # y is 0 and exponent_D-1 is >=0
                fp_term_D = 0

            f_prime_y = fp_term_A + fp_term_B + fp_term_D

            if (
                abs(f_prime_y) < 1e-12
            ):  # Avoid division by zero if derivative is too small
                self.logger.warning(
                    f"Derivative f'(y) is near zero ({f_prime_y}). Pr={pr}, Tr={tr}, y={y}"
                )
                return np.nan

            y_new = y - f_y / f_prime_y

            if abs(y_new - y) < tolerance:
                y = y_new
                break
            y = y_new
        else:  # Loop finished without break (no convergence)
            self.logger.warning(
                f"Hall-Yarborough Z-factor failed to converge after {max_iter} iterations. Pr={pr}, Tr={tr}, Last y={y}, Last f(y)={f_y}"
            )
            return np.nan  # Return NaN or raise error if convergence fails

        # Final check on y (rho_r)
        if y <= 0 or y >= 1.0:  # Physical range for rho_r in this form of HY is (0,1)
            self.logger.warning(
                f"Converged reduced density y = {y} is outside (0,1). Pr={pr}, Tr={tr}"
            )
            return np.nan

        # Calculate Z factor: Z = Y_const * Tr / Pr (if Y_const was defined without Pr/Tr)
        # Or Z = (0.06125 * Pr) / (y * Tr) * exp_term
        # With Y_const = (0.06125 * pr / tr) * exp_term, then Z = Y_const / y

        z = Y_const / y  # This is Z = ( (0.06125 * Pr / Tr) * exp_term ) / rho_r

        # Sanity check for Z
        if not (0 < z < 2.0):  # Z factor should generally be in this range
            self.logger.warning(
                f"Calculated Z-factor {z} is outside typical range (0-2). Pr={pr}, Tr={tr}, rho_r={y}"
            )
            # Optionally return np.nan or the calculated z
        return z


class ReserveCategory(Enum):  # noqa: F401
    PROVED = "P1"
    PROBABLE = "P2"
    POSSIBLE = "P3"


@dataclass  # noqa: F401
class ReservesEstimate:
    category: ReserveCategory
    oil_volume: float  # em bbl
    gas_volume: float  # em mscf
    confidence_level: float  # probabilidade de sucesso
    recovery_factor: float
    net_present_value: float
    date: datetime.datetime  # Changed to datetime.datetime


class MaterialBalance:
    """Classe para análise de balanço de materiais."""

    def __init__(self):
        self.pvt = PVTProperties()

    def calculate_ogip(
        self,
        pressure: np.ndarray,
        production: np.ndarray,
        temperature: float,
        gas_specific_gravity: float,
    ) -> float:
        """
        Calcula OGIP usando balanço de materiais.

        Args:
            pressure: Array de pressões
            production: Array de produção acumulada
            temperature: Temperatura do reservatório
            gas_specific_gravity: Densidade do gás

        Returns:
            OGIP estimado
        """
        # Método de Havlena-Odeh
        p = pressure
        gp = production

        # Calcular Z médio
        z = np.array(
            [
                self.pvt.calculate_z_factor(pi, temperature, gas_specific_gravity)
                for pi in p
            ]
        )

        # Calcular F e Eg
        f = gp
        eg = (p[0] / z[0] - p / z) * 1000  # 1000 para converter para scf

        # Regressão linear
        slope, _ = np.polyfit(eg, f, 1)

        return slope

    def calculate_stoiip(
        self,
        pressure: np.ndarray,
        production: np.ndarray,
        temperature: float,
        api_gravity: float,
        gas_specific_gravity: float,
    ) -> float:
        """
        Calcula STOIIP usando balanço de materiais.

        Args:
            pressure: Array de pressões
            production: Array de produção acumulada
            temperature: Temperatura do reservatório
            api_gravity: Grau API do óleo
            gas_specific_gravity: Densidade do gás

        Returns:
            STOIIP estimado
        """
        # Método de Havlena-Odeh para óleo
        p = pressure
        np = production

        # Calcular Bo e Rs
        bo = np.array(
            [
                self.pvt.calculate_formation_volume_factor(
                    pi, temperature, "oil", api_gravity, gas_specific_gravity
                )
                for pi in p
            ]
        )
        rs = np.array(
            [
                self.pvt.calculate_solution_gas_ratio(
                    pi, temperature, api_gravity, gas_specific_gravity
                )
                for pi in p
            ]
        )

        # Calcular F e Eo
        f = np * (
            bo
            + (rs[0] - rs)
            * self.pvt.calculate_formation_volume_factor(
                p[0], temperature, "gas", None, gas_specific_gravity
            )
        )
        eo = (bo - bo[0]) + (rs[0] - rs) * self.pvt.calculate_formation_volume_factor(
            p[0], temperature, "gas", None, gas_specific_gravity
        )

        # Regressão linear
        slope, _ = np.polyfit(eo, f, 1)

        return slope


class WellTesting:
    """Classe para análise de testes de pressão."""

    def __init__(self):
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("WellTesting")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def analyze_buildup(
        self,
        time: np.ndarray,
        pressure: np.ndarray,
        rate: float,
        viscosity: float,
        compressibility: float,
        porosity: float,
        wellbore_radius: float,
    ) -> Dict:
        """
        Analisa teste de build-up.

        Args:
            time: Array de tempos
            pressure: Array de pressões
            rate: Vazão antes do build-up
            viscosity: Viscosidade do fluido
            compressibility: Compressibilidade total
            porosity: Porosidade
            wellbore_radius: Raio do poço

        Returns:
            Dicionário com resultados da análise
        """
        # Método de Horner
        tp = time[-1]  # tempo de produção
        dt = time - time[0]  # delta t
        tda = (tp + dt) / dt  # tempo de Horner

        # Regressão linear
        slope, intercept = np.polyfit(np.log(tda), pressure, 1)

        # Calcular parâmetros
        k = 162.6 * rate * viscosity / (slope * 1)  # permeabilidade
        skin = 1.151 * (
            (intercept - pressure[0]) / slope
            - np.log10(
                k / (porosity * viscosity * compressibility * wellbore_radius**2)
            )
            + 3.23
        )

        return {"permeability": k, "skin": skin, "slope": slope, "intercept": intercept}

    def analyze_drawdown(
        self,
        time: np.ndarray,
        pressure: np.ndarray,
        rate: float,
        viscosity: float,
        compressibility: float,
        porosity: float,
        wellbore_radius: float,
    ) -> Dict:
        """
        Analisa teste de drawdown.

        Args:
            time: Array de tempos
            pressure: Array de pressões
            rate: Vazão constante
            viscosity: Viscosidade do fluido
            compressibility: Compressibilidade total
            porosity: Porosidade
            wellbore_radius: Raio do poço

        Returns:
            Dicionário com resultados da análise
        """
        # Método de semilog
        dt = time - time[0]  # delta t

        # Regressão linear
        slope, intercept = np.polyfit(np.log(dt), pressure, 1)

        # Calcular parâmetros
        k = 162.6 * rate * viscosity / (slope * 1)  # permeabilidade
        skin = 1.151 * (
            (pressure[0] - intercept) / slope
            - np.log10(
                k / (porosity * viscosity * compressibility * wellbore_radius**2)
            )
            + 3.23
        )

        return {"permeability": k, "skin": skin, "slope": slope, "intercept": intercept}


class DeclineAnalysis:
    """Classe para análise de declínio de produção."""

    def __init__(self):
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("DeclineAnalysis")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def fit_arps(
        self, time: np.ndarray, rate: np.ndarray, method: str = "hyperbolic"
    ) -> Dict:
        """
        Ajusta curva de declínio de Arps.

        Args:
            time: Array de tempos
            rate: Array de vazões
            method: Método de declínio ('exponential', 'harmonic' ou 'hyperbolic')

        Returns:
            Dicionário com parâmetros ajustados
        """
        if method == "exponential":
            # q = qi * exp(-Di * t)
            log_rate = np.log(rate)
            slope, intercept = np.polyfit(time, log_rate, 1)
            di = -slope
            qi = np.exp(intercept)
            b = 0

        elif method == "harmonic":
            # q = qi / (1 + Di * t)
            inv_rate = 1 / rate
            slope, intercept = np.polyfit(time, inv_rate, 1)
            di = slope / intercept
            qi = 1 / intercept
            b = 1

        else:  # hyperbolic
            # q = qi / (1 + b * Di * t)^(1/b)
            def objective(params):
                qi, di, b = params
                q_pred = qi / (1 + b * di * time) ** (1 / b)
                return np.sum((rate - q_pred) ** 2)

            # Otimização
            result = minimize(
                objective, [rate[0], 0.1, 0.5], bounds=[(0, None), (0, None), (0, 1)]
            )
            qi, di, b = result.x

        return {"qi": qi, "di": di, "b": b, "method": method}

    def forecast_production(self, params: Dict, time: np.ndarray) -> np.ndarray:
        """
        Gera previsão de produção.

        Args:
            params: Parâmetros do ajuste
            time: Array de tempos para previsão

        Returns:
            Array com vazões previstas
        """
        qi = params["qi"]
        di = params["di"]
        b = params["b"]

        if params["method"] == "exponential":
            rate = qi * np.exp(-di * time)
        elif params["method"] == "harmonic":
            rate = qi / (1 + di * time)
        else:  # hyperbolic
            rate = qi / (1 + b * di * time) ** (1 / b)

        return rate

    def calculate_eur(self, params: Dict) -> float:
        """
        Calcula EUR (Estimated Ultimate Recovery).

        Args:
            params: Parâmetros do ajuste

        Returns:
            EUR estimado
        """
        qi = params["qi"]
        di = params["di"]
        b = params["b"]

        if params["method"] == "exponential":
            eur = qi / di
        elif params["method"] == "harmonic":
            eur = qi / di * np.log(1 + di * 365 * 30)  # 30 anos
        else:  # hyperbolic
            eur = (
                qi / ((1 - b) * di) * (1 - (1 + b * di * 365 * 30) ** (1 - 1 / b))
            )  # 30 anos

        return eur


class HistoryMatching:
    """Classe para ajuste de histórico."""

    # def __init__(self, simulation: ReservoirSimulation): # Original depended on the removed ReservoirSimulation
    def __init__(
        self, simulation_object: object
    ):  # Changed to accept a generic simulation object
        # The user of this class will need to ensure the simulation_object
        # has the methods and attributes that match_history expects (e.g., run_simulation, grid)
        self.simulation = simulation_object
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("HistoryMatching")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def match_history(
        self,
        historical_data: Dict[str, np.ndarray],
        parameters: Dict[str, Tuple[float, float]],
        objective_function: callable,
    ) -> Dict:
        """
        Realiza ajuste de histórico.

        Args:
            historical_data: Dicionário com dados históricos
            parameters: Dicionário com parâmetros a ajustar e seus limites
            objective_function: Função objetivo

        Returns:
            Dicionário com parâmetros otimizados
        """

        def objective(params):
            # Atualizar parâmetros do modelo
            for i, (param, _) in enumerate(parameters.items()):
                setattr(self.simulation, param, params[i])

            # Rodar simulação
            self.simulation.run_simulation(timesteps=len(historical_data["time"]), dt=1)

            # Calcular erro
            error = objective_function(historical_data, self.simulation.grid)
            return error

        # Otimização
        initial_guess = [
            0.5 * (min_val + max_val) for _, (min_val, max_val) in parameters.items()
        ]
        bounds = [bounds for _, bounds in parameters.items()]

        result = minimize(objective, initial_guess, bounds=bounds)

        # Retornar parâmetros otimizados
        optimized_params = {}
        for i, (param, _) in enumerate(parameters.items()):
            optimized_params[param] = result.x[i]

        return optimized_params


class ReservoirVisualization:
    """Classe para visualização do reservatório."""

    # def __init__(self, simulation: ReservoirSimulation): # Original depended on the removed ReservoirSimulation
    def __init__(
        self, simulation_object: object
    ):  # Changed to accept a generic simulation object
        # The user of this class will need to ensure the simulation_object
        # has the necessary attributes like 'grid' with 'saturation' and 'pressure'
        self.simulation = simulation_object

    def plot_saturation_map(self, layer: int, time_step: int = -1) -> plt.Figure:
        """
        Plota mapa de saturação.

        Args:
            layer: Camada a ser plotada
            time_step: Passo de tempo

        Returns:
            Figura do matplotlib
        """
        fig, ax = plt.subplots(figsize=(10, 8))

        # Ensure the simulation object has the expected structure
        if (
            not hasattr(self.simulation, "grid")
            or not isinstance(self.simulation.grid, dict)
            or "saturation" not in self.simulation.grid
            or not isinstance(self.simulation.grid["saturation"], np.ndarray)
        ):
            ax.text(
                0.5,
                0.5,
                "Saturation data not available or in unexpected format.",
                horizontalalignment="center",
                verticalalignment="center",
            )
            return fig

        saturation_data = self.simulation.grid["saturation"]
        if saturation_data.ndim == 3 and layer < saturation_data.shape[2]:
            saturation_slice = saturation_data[:, :, layer]
        elif saturation_data.ndim == 2:  # Assuming it might be a 2D slice already
            saturation_slice = saturation_data
        else:
            ax.text(
                0.5,
                0.5,
                f"Saturation data has {saturation_data.ndim} dimensions or layer {layer} is out of bounds.",
                horizontalalignment="center",
                verticalalignment="center",
            )
            return fig

        im = ax.imshow(saturation_slice, cmap="jet", origin="lower")  # Added origin
        plt.colorbar(im, ax=ax, label="Saturação de Óleo")

        ax.set_title(f"Mapa de Saturação - Camada {layer}")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")

        return fig

    def plot_pressure_map(self, layer: int, time_step: int = -1) -> plt.Figure:
        """
        Plota mapa de pressão.

        Args:
            layer: Camada a ser plotada
            time_step: Passo de tempo

        Returns:
            Figura do matplotlib
        """
        fig, ax = plt.subplots(figsize=(10, 8))

        if (
            not hasattr(self.simulation, "grid")
            or not isinstance(self.simulation.grid, dict)
            or "pressure" not in self.simulation.grid
            or not isinstance(self.simulation.grid["pressure"], np.ndarray)
        ):
            ax.text(
                0.5,
                0.5,
                "Pressure data not available or in unexpected format.",
                horizontalalignment="center",
                verticalalignment="center",
            )
            return fig

        pressure_data = self.simulation.grid["pressure"]
        if pressure_data.ndim == 3 and layer < pressure_data.shape[2]:
            pressure_slice = pressure_data[:, :, layer]
        elif pressure_data.ndim == 2:
            pressure_slice = pressure_data
        else:
            ax.text(
                0.5,
                0.5,
                f"Pressure data has {pressure_data.ndim} dimensions or layer {layer} is out of bounds.",
                horizontalalignment="center",
                verticalalignment="center",
            )
            return fig

        im = ax.imshow(pressure_slice, cmap="jet", origin="lower")  # Added origin
        plt.colorbar(im, ax=ax, label="Pressão (psia)")

        ax.set_title(f"Mapa de Pressão - Camada {layer}")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")

        return fig

    def plot_well_performance(
        self, well_name: str, time: np.ndarray, rate: np.ndarray, pressure: np.ndarray
    ) -> plt.Figure:
        """
        Plota performance do poço.

        Args:
            well_name: Nome do poço
            time: Array de tempos
            rate: Array de vazões
            pressure: Array de pressões

        Returns:
            Figura do matplotlib
        """
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(10, 8), sharex=True
        )  # Share x-axis

        # Vazão
        ax1.plot(time, rate, "b-")
        ax1.set_ylabel("Vazão (bbl/d)")  # Or appropriate units
        ax1.set_title(f"Performance do Poço {well_name}")
        ax1.grid(True)

        # Pressão
        ax2.plot(time, pressure, "r-")
        ax2.set_xlabel("Tempo")  # Or appropriate units
        ax2.set_ylabel("Pressão (psia)")
        ax2.grid(True)

        plt.tight_layout()
        return fig
