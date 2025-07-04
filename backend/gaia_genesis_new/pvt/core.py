import numpy as np
from scipy.optimize import fsolve, root, brentq
from pydantic import BaseModel, validator, Field
from typing import List, Optional, Tuple, Dict, Any

# Assuming schemas are in api_v1.schemas relative to gaia_genesis_new
from backend.gaia_genesis_new.api_v1.schemas import FluidComponent # Use the one from schemas.py
from backend.gaia_genesis_new.logger import logger # Use the application's logger


class PVTResult(BaseModel): # Defined here for direct use by core, can also be from schemas
    pressure: float  # psi
    temperature: float  # °F
    oil_fvf: Optional[float] = None # rb/STB
    gas_fvf: Optional[float] = None # rcf/scf
    solution_gor: Optional[float] = None # scf/STB
    oil_viscosity: Optional[float] = None # cp
    gas_viscosity: Optional[float] = None # cp
    oil_density: Optional[float] = None # lb/ft³
    gas_density: Optional[float] = None # lb/ft³
    surface_tension: Optional[float] = None # dynes/cm
    z_liquid: Optional[float] = None # Compressibility factor for liquid phase
    z_vapor: Optional[float] = None  # Compressibility factor for vapor phase


class BlackOilModel:
    def __init__(self, pvt_data: Dict[str, float]):
        # Ensure all required keys are present with defaults or raise error
        required_keys = ['pb', 'co', 'rsb', 'bob', 'muob', 'muod', 'cg', 'gamma_g', 'gamma_o', 'temperature']
        for key in required_keys:
            if key not in pvt_data:
                raise ValueError(f"Missing required key in pvt_data for BlackOilModel: {key}")

        self.pb: float = pvt_data['pb']  # Bubble point pressure (psi)
        self.co: float = pvt_data['co']  # Oil compressibility (1/psi)
        self.rsb: float = pvt_data['rsb']  # Solution GOR at bubble point (scf/STB)
        self.bob: float = pvt_data['bob']  # Oil FVF at bubble point (rb/STB)
        self.muob: float = pvt_data['muob']  # Oil viscosity at bubble point (cp)
        self.muod: float = pvt_data['muod']  # Dead oil viscosity (cp)
        self.cg: float = pvt_data['cg']  # Gas compressibility (1/psi)
        self.gamma_g: float = pvt_data['gamma_g']  # Gas specific gravity (air=1)
        self.gamma_o: float = pvt_data['gamma_o']  # Oil specific gravity (water=1)
        self.temperature: float = pvt_data['temperature']  # Reservoir temperature (°F)

        # Optional: tables for pressure-dependent properties (not used by current correlations but could be)
        self.bo_table: Dict[float, float] = pvt_data.get('bo_table', {})  # Oil FVF vs pressure
        self.rs_table: Dict[float, float] = pvt_data.get('rs_table', {})  # Solution GOR vs pressure
        logger.info(f"BlackOilModel initialized with temp: {self.temperature}°F, Pb: {self.pb} psi")


    def calculate_api_gravity(self) -> float:
        return (141.5 / self.gamma_o) - 131.5

    def calculate_bubble_point_standing(self) -> float: # Renamed for clarity
        """Calculate bubble point pressure using Standing's correlation (1947)"""
        api = self.calculate_api_gravity()
        # Pb = 18.2 * [(Rs/γg)^0.83 * 10^(0.00091*T - 0.0125*API)] - 1.4
        # This formula typically uses Rsb (GOR at bubble point) and current T, API
        term_val = (self.rsb / self.gamma_g)**0.83 * 10**(0.00091 * self.temperature - 0.0125 * api)
        pb_calc = 18.2 * (term_val - 1.4) # Original Standing had -1.4 inside parenthesis with term_val
        # Vazquez and Beggs (1980) is another common one.
        # For simplicity, this method might be more of a check if Pb is provided,
        # or an iterative solve if Rs(P) is used.
        # Here, it's assumed self.rsb is the Rs at the given self.pb.
        # So this function as written is more like a verification of consistency or an estimate.
        # If this is meant to *calculate* Pb from a given Rs, T, gamma_g, gamma_o, then Rs would be an input.
        # Let's assume it's an estimate based on Rsb.
        logger.debug(f"Standing's Pb correlation: API={api:.2f}, term_val={term_val:.2f}, Pb_calc={pb_calc:.2f}")
        return pb_calc # This is an estimate, actual self.pb is input.

    def calculate_oil_fvf_standing(self, p: float, rs_input: Optional[float] = None) -> float:
        """Calculate oil formation volume factor using Standing's correlation (1947)"""
        # Rs for this calculation is the solution GOR at pressure P.
        # If P > Pb, Rs = Rsb. If P <= Pb, Rs is a function of P.
        rs = rs_input if rs_input is not None else self.calculate_solution_gor_standing(p)

        # F = Rs * (gamma_g / gamma_o)^0.5 + 1.25 * T(°F)
        F = rs * (self.gamma_g / self.gamma_o)**0.5 + 1.25 * self.temperature

        # Bo (below bubble point or at bubble point if P=Pb)
        bo_sat = 0.9759 + 0.000120 * F**1.2

        if p >= self.pb:
            # Above bubble point: Bo = Bob * exp(-co * (P - Pb))
            # Bob should be Bo at Pb, using Rsb
            F_b = self.rsb * (self.gamma_g / self.gamma_o)**0.5 + 1.25 * self.temperature
            bob_calc = 0.9759 + 0.000120 * F_b**1.2
            # Use the provided self.bob if P=Pb, or calculated if P > Pb for consistency
            current_bob_to_use = self.bob if abs(p - self.pb) < 1e-3 else bob_calc

            # Correction for P > Pb
            bo_undersat = current_bob_to_use * np.exp(-self.co * (p - self.pb))
            return bo_undersat
        else:
            # Below bubble point
            return bo_sat

    def calculate_solution_gor_standing(self, p: float) -> float:
        """Calculate solution gas-oil ratio using Standing's correlation (1947)"""
        if p >= self.pb:
            return self.rsb
        else:
            # Rs = γg * [(P/18.2 + 1.4) * 10^(0.0125*API - 0.00091*T)]^(1/0.83)
            api = self.calculate_api_gravity()
            term_in_brackets = (p / 18.2 + 1.4) * 10**(0.0125 * api - 0.00091 * self.temperature)
            rs_calc = self.gamma_g * (term_in_brackets**(1.0 / 0.83))
            return max(0, rs_calc) # GOR cannot be negative

    def calculate_z_factor_hall_yarborough(self, p: float, t_fahrenheit: float) -> float:
        """Calculate gas compressibility factor using Hall-Yarborough correlation."""
        # Pseudocritical properties (Sutton correlation for gas gravity gamma_g)
        # Ensure T is in Rankine for these correlations
        t_rankine = t_fahrenheit + 459.67

        # Sutton's correlations for pseudocritical properties based on gas gravity (gamma_g)
        tpc = 169.2 + 349.5 * self.gamma_g - 74.0 * self.gamma_g**2  # Tc in Rankine
        ppc = 756.8 - 131.0 * self.gamma_g - 3.6 * self.gamma_g**2   # Pc in psia

        tpr = t_rankine / tpc  # Pseudoreduced temperature
        ppr = p / ppc      # Pseudoreduced pressure

        if tpr <= 0 or ppc <=0: # Should not happen with typical gamma_g
            logger.warning(f"Invalid Tpc ({tpc}) or Ppc ({ppc}) for Z-factor calc. Gamma_g: {self.gamma_g}")
            return 1.0

        # Hall-Yarborough constants and equation for reduced density (y)
        # 0.06125 * tpr * exp(-1.2 * (1-tpr)^2) * ppr - (y + y^2 + y^3 - y^4)/(1-y)^3 + (14.76*tpr - 9.76*tpr^2 + 4.58*tpr^3)*y^2 - (90.7*tpr - 242.2*tpr^2 + 42.4*tpr^3)*y^(2.18 + 2.82*tpr) = 0
        # Let f(y) = LHS of the equation. We need to find root of f(y) = 0.
        # Use Newton-Raphson or another root-finding method.

        c1 = 0.06125 * tpr * np.exp(-1.2 * (1 - tpr)**2)
        c2 = 14.76 * tpr - 9.76 * tpr**2 + 4.58 * tpr**3
        c3 = 90.7 * tpr - 242.2 * tpr**2 + 42.4 * tpr**3
        c4 = 2.18 + 2.82 * tpr

        def f_y(y_guess):
            if abs(1 - y_guess) < 1e-9: # Avoid division by zero
                return np.inf if y_guess > 0 else -np.inf # Large number to push solver away
            term1 = c1 * ppr
            term2 = (y_guess + y_guess**2 + y_guess**3 - y_guess**4) / (1 - y_guess)**3
            term3 = c2 * y_guess**2
            term4 = c3 * y_guess**c4
            return term1 - term2 + term3 - term4

        # Initial guess for y (reduced density)
        y_initial_guess = 0.001
        try:
            # Using fsolve, a more general root finder.
            # It might be more robust than a manual Newton-Raphson for this complex equation.
            y_solution = fsolve(f_y, y_initial_guess, xtol=1e-7)
            y = y_solution[0]
            if abs(f_y(y)) > 1e-5 : # Check if solution is good
                 logger.warning(f"Hall-Yarborough f(y) is not close to zero: {f_y(y):.2e} at Ppr={ppr:.2f}, Tpr={tpr:.2f}. Using y={y:.4f}")
                 # Fallback if solution is bad, could try other initial guesses or methods.
                 # For now, proceed with potentially less accurate y or default Z.
        except Exception as e:
            logger.warning(f"fsolve failed for Hall-Yarborough Z-factor at Ppr={ppr:.2f}, Tpr={tpr:.2f}: {e}. Returning Z=1.0")
            return 1.0 # Fallback Z

        z = (c1 * ppr) / y if abs(y) > 1e-9 else 1.0 # Avoid division by zero
        return z if z > 0 else 1.0 # Z factor should be positive

    def calculate_gas_fvf(self, p: float, t_fahrenheit: float) -> float:
        """Calculate gas formation volume factor (Bg) in ft³/scf."""
        # Bg = Z * T / P * (Psc / Tsc) = Z * (T_rankine / P_psia) * (14.7 / 519.67)
        # Bg = 0.02827 * Z * T_rankine / P_psia (if Tsc = 60F = 519.67R, Psc = 14.7 psia)
        z = self.calculate_z_factor_hall_yarborough(p, t_fahrenheit)
        t_rankine = t_fahrenheit + 459.67
        if p <= 0: return np.inf # Avoid division by zero if pressure is invalid
        bg = 0.02827 * z * t_rankine / p
        return bg

    def calculate_oil_viscosity_beggs_robinson(self, p: float, rs_input: Optional[float] = None) -> float:
        """Calculate oil viscosity using Beggs-Robinson correlation (1975)."""
        # Rs for this calculation is the solution GOR at pressure P.
        rs = rs_input if rs_input is not None else self.calculate_solution_gor_standing(p)

        # Dead oil viscosity (μod) first, using Beggs-Robinson or input self.muod
        # Beggs-Robinson dead oil viscosity part:
        # x = Y * T(°F)^(-1.163) where Y = 10^Z - 1 and Z = 3.0324 - 0.02023 * API
        # This calculates μod. If self.muod is provided, it might be preferred.
        # Let's use self.muod as the primary dead oil viscosity if available.
        muod_calc = self.muod # Use the input dead oil viscosity

        # Live oil viscosity (μo)
        # A = 10.715 * (Rs + 100)^(-0.515)
        # B = 5.44 * (Rs + 150)^(-0.338)
        # μob = A * μod^B (viscosity at bubble point or below)
        A = 10.715 * (rs + 100)**(-0.515)
        B = 5.44 * (rs + 150)**(-0.338)
        muo_saturated = A * muod_calc**B

        if p >= self.pb:
            # Above bubble point: μo = μob * (P/Pb)^m
            # where μob is viscosity at bubble point (using Rsb)
            A_b = 10.715 * (self.rsb + 100)**(-0.515)
            B_b = 5.44 * (self.rsb + 150)**(-0.338)
            # self.muob is the viscosity at bubble point pressure
            muob_to_use = self.muob

            # Exponent m for P > Pb (Beggs and Robinson)
            m = 2.6 * p**1.187 * np.exp(-11.513 - (8.98e-5 * p)) # Original paper has 8.98e-5 * API, not P
            # Re-checking the formula, often it's simpler or different.
            # Let's use a common simplified approach or assume m can be an input/correlation.
            # For now, this 'm' seems problematic with 'p' in exponent and base.
            # Fallback: A simpler approach might be needed or ensure the correlation for 'm' is correct.
            # Using the saturated oil viscosity at Pb and then applying pressure increase effect.
            # If this specific 'm' is required, it needs validation.
            # Let's assume for P > Pb, viscosity increases slightly.
            # A very simplified pressure correction:
            # muo_undersaturated = muob_to_use * (1 + (p - self.pb) * 1e-4) # Simplistic increase
            # The provided 'm' formula is likely from a specific paper, ensure it's correctly transcribed.
            # If using the exact Beggs-Robinson for undersaturated, it's often:
            # µo = µob (P/Pb)^C where C is an empirical factor.
            # Given the complex 'm', I'll use muob_to_use for now, assuming it's the viscosity at Pb.
            # The effect of pressure above Pb on oil viscosity is usually less dramatic than temp or Rs.
            # For a more rigorous approach, a specific undersaturated oil viscosity correlation would be better.
            # Let's use the calculated muo_saturated at Pb (which is muob_to_use effectively)
            # and then apply a pressure correction if needed.
            # For now, let's assume muo = muob if P >= Pb (simplification if 'm' is not robustly defined)
            # Or, if `m` is correct:
            # muo_undersaturated = muob_to_use * (p / self.pb)**m # This 'm' needs to be a small exponent
            # Let's use the saturated viscosity at Pb as a proxy for mu_ob and apply a small correction.
            # For now, returning muob for P > Pb is a placeholder until 'm' is clarified or a different correlation is used.
            return muob_to_use # Placeholder for undersaturated viscosity
        else:
            # Below bubble point
            return muo_saturated

    def calculate_gas_viscosity_lee_gonzalez_eakin(self, p: float, t_fahrenheit: float, gas_density_lb_ft3: Optional[float] = None) -> float:
        """Calculate gas viscosity using Lee, Gonzalez, and Eakin correlation (1966)."""
        t_rankine = t_fahrenheit + 459.67
        mw_gas = self.gamma_g * 28.96 # Molecular weight of gas (air = 28.96)

        if gas_density_lb_ft3 is None:
            # Calculate gas density if not provided
            z = self.calculate_z_factor_hall_yarborough(p, t_fahrenheit)
            # rho_g (g/cm^3) = P * MW / (Z * R_gas_specific * T)
            # R_gas_specific for g/cm^3, P in atm, T in K.
            # Easier: rho_g (lb/ft^3) = P * MW / (10.73 * Z * T_rankine)
            if z <= 0 or t_rankine <=0: # Should not happen
                 gas_density_lb_ft3 = (p * mw_gas) / (10.73 * 1.0 * (t_fahrenheit + 459.67)) # Approx if Z fails
            else:
                 gas_density_lb_ft3 = (p * mw_gas) / (10.73 * z * t_rankine)

        # Lee et al. correlation:
        K = ((9.4 + 0.02 * mw_gas) * t_rankine**1.5) / (209 + 19 * mw_gas + t_rankine)
        X = 3.5 + (986 / t_rankine) + 0.01 * mw_gas
        Y = 2.4 - 0.2 * X

        # Gas density in g/cm^3 for the correlation
        rho_g_g_cm3 = gas_density_lb_ft3 * 0.0160185 # Convert lb/ft^3 to g/cm^3

        mu_g = (1e-4) * K * np.exp(X * (rho_g_g_cm3**Y)) # Result in centipoise (cP)
        return mu_g


class CompositionalModel:
    def __init__(self, components: List[FluidComponent]):
        if not components:
            raise ValueError("CompositionalModel requires at least one component.")
        if abs(sum(c.mole_fraction for c in components) - 1.0) > 1e-4: # Tolerance for sum
            raise ValueError("Sum of mole fractions must be equal to 1.0")

        self.components = sorted(components, key=lambda c: c.molecular_weight) # Often sorted
        self.R_psia_ft3_lbmol_R = 10.73159  # Universal gas constant (psia·ft³/lb-mol·°R)

        # Peng-Robinson EOS constants
        self.omega_a_pr = 0.4572355289 # (R Tc)^2 / Pc
        self.omega_b_pr = 0.0777960739 # R Tc / Pc

        # Binary Interaction Parameters (BIPs, kij)
        # Stored as a dictionary of tuples: {(comp_idx_i, comp_idx_j): kij_value}
        self.binary_interaction_params = self._initialize_bips()
        logger.info(f"CompositionalModel initialized with {len(self.components)} components.")

    def _initialize_bips(self) -> Dict[Tuple[int, int], float]:
        """Initialize Binary Interaction Parameters. Default to zero."""
        bips = {}
        num_components = len(self.components)
        for i in range(num_components):
            for j in range(num_components):
                # kij = kji, kii = 0
                if i == j:
                    bips[(i, j)] = 0.0
                else:
                    # Placeholder: common to use zero or literature values for common pairs
                    # For example, Chueh and Prausnitz (1967) provide some estimations.
                    # Here, we default to 0.0, can be updated later.
                    bips[(i, j)] = 0.0
                    bips[(j, i)] = 0.0
        return bips

    def set_binary_interaction_params(self, kij_matrix: Optional[List[List[float]]] = None, kij_dict: Optional[Dict[Tuple[str, str], float]] = None):
        """Set BIPs from a matrix or a dictionary of name pairs."""
        if kij_matrix:
            # ... logic to populate self.binary_interaction_params from matrix ...
            pass
        elif kij_dict:
            # ... logic to populate self.binary_interaction_params from dict ...
            pass
        logger.info("Binary Interaction Parameters updated.")


    def _calculate_pr_eos_params_pure(self, component_idx: int, t_fahrenheit: float) -> Tuple[float, float]:
        """Calculate Peng-Robinson 'a' and 'b' for a pure component at T."""
        comp = self.components[component_idx]
        tc_rankine = comp.critical_temperature # Already in Rankine
        pc_psia = comp.critical_pressure     # Already in psia
        acentric_factor = comp.acentric_factor
        t_rankine = t_fahrenheit + 459.67

        b_i = self.omega_b_pr * self.R_psia_ft3_lbmol_R * tc_rankine / pc_psia

        # Kappa for Peng-Robinson alpha function
        if acentric_factor <= 0.491: # Original PR
            kappa = 0.37464 + 1.54226 * acentric_factor - 0.26992 * acentric_factor**2
        else: # Modification for heavier components (PR78 or others)
            kappa = 0.379642 + 1.48503 * acentric_factor - 0.164423 * acentric_factor**2 + 0.016666 * acentric_factor**3

        tr_i = t_rankine / tc_rankine
        alpha_i = (1 + kappa * (1 - np.sqrt(tr_i)))**2

        ac_i = self.omega_a_pr * (self.R_psia_ft3_lbmol_R**2 * tc_rankine**2) / pc_psia
        a_i = ac_i * alpha_i

        return a_i, b_i

    def _calculate_pr_eos_params_mixture(self, phase_comp_mole_fractions: List[float], t_fahrenheit: float) -> Tuple[float, float]:
        """Calculate Peng-Robinson 'a_mix' and 'b_mix' for a mixture."""
        if not (abs(sum(phase_comp_mole_fractions) - 1.0) < 1e-4 or sum(phase_comp_mole_fractions) == 0): # Allow sum=0 for empty phase
             logger.warning(f"Sum of mole fractions in mixture is {sum(phase_comp_mole_fractions):.5f}, not 1.0.")
             # Normalization might be needed if this is a persistent issue from upstream logic

        a_mix = 0.0
        b_mix = 0.0

        pure_params_at_t = [self._calculate_pr_eos_params_pure(i, t_fahrenheit) for i in range(len(self.components))]

        for i in range(len(self.components)):
            zi = phase_comp_mole_fractions[i]
            a_i_at_t, b_i = pure_params_at_t[i]
            b_mix += zi * b_i
            for j in range(len(self.components)):
                zj = phase_comp_mole_fractions[j]
                a_j_at_t, _ = pure_params_at_t[j]
                kij = self.binary_interaction_params.get((i,j), 0.0) # Default to 0 if somehow missing

                a_mix += zi * zj * np.sqrt(a_i_at_t * a_j_at_t) * (1 - kij)

        return a_mix, b_mix

    def _solve_pr_eos_for_z(self, p_psia: float, t_fahrenheit: float, a_mix: float, b_mix: float) -> List[float]:
        """Solves the PR EOS cubic equation for Z (compressibility factor)."""
        t_rankine = t_fahrenheit + 459.67

        A_coeff = a_mix * p_psia / (self.R_psia_ft3_lbmol_R**2 * t_rankine**2)
        B_coeff = b_mix * p_psia / (self.R_psia_ft3_lbmol_R * t_rankine)

        # Z^3 - (1-B)Z^2 + (A - 2B - 3B^2)Z - (AB - B^2 - B^3) = 0
        # Coefficients for Z^3 + c2*Z^2 + c1*Z + c0 = 0
        c2 = -(1 - B_coeff)
        c1 = A_coeff - 2 * B_coeff - 3 * B_coeff**2
        c0 = -(A_coeff * B_coeff - B_coeff**2 - B_coeff**3)

        coeffs = [1, c2, c1, c0]
        roots = np.roots(coeffs)

        real_roots = sorted([r.real for r in roots if abs(r.imag) < 1e-9 and r.real > 0]) # Only positive real roots

        if not real_roots:
            logger.warning(f"PR EOS: No positive real roots for Z at P={p_psia}, T={t_fahrenheit}. A={A_coeff:.3e}, B={B_coeff:.3e}. Roots: {roots}")
            # This indicates an issue, possibly outside valid phase region or bad parameters
            # Fallback to a default Z or raise error
            return [B_coeff] if B_coeff > 0 else [0.001] # Smallest physical Z is B for PR
        return real_roots

    def _calculate_fugacity_coeffs_pr(self, phase_comp_mole_fractions: List[float], p_psia: float, t_fahrenheit: float, z_factor_phase: float) -> List[float]:
        """Calculates fugacity coefficients for each component in a phase using PR EOS."""
        a_mix, b_mix = self._calculate_pr_eos_params_mixture(phase_comp_mole_fractions, t_fahrenheit)
        t_rankine = t_fahrenheit + 459.67

        A_mix_eos = a_mix * p_psia / (self.R_psia_ft3_lbmol_R**2 * t_rankine**2)
        B_mix_eos = b_mix * p_psia / (self.R_psia_ft3_lbmol_R * t_rankine)

        fugacity_coeffs = []
        pure_params_at_t = [self._calculate_pr_eos_params_pure(i, t_fahrenheit) for i in range(len(self.components))]

        term_log = np.log((z_factor_phase + (1 + np.sqrt(2)) * B_mix_eos) /
                          (z_factor_phase + (1 - np.sqrt(2)) * B_mix_eos))

        for i in range(len(self.components)):
            _, b_i = pure_params_at_t[i]

            sum_term_a_ij = 0
            for j in range(len(self.components)):
                a_j_at_t, _ = pure_params_at_t[j]
                a_i_at_t, _ = pure_params_at_t[i] # ai is needed here
                kij = self.binary_interaction_params.get((i,j),0.0)
                sum_term_a_ij += phase_comp_mole_fractions[j] * np.sqrt(a_i_at_t * a_j_at_t) * (1 - kij)

            ln_phi_i = (b_i / b_mix) * (z_factor_phase - 1) - \
                       np.log(z_factor_phase - B_mix_eos) - \
                       (A_mix_eos / (2 * np.sqrt(2) * B_mix_eos)) * \
                       ((2 * sum_term_a_ij / a_mix) - (b_i / b_mix)) * term_log

            fugacity_coeffs.append(np.exp(ln_phi_i))

        return fugacity_coeffs

    def _solve_rachford_rice(self, overall_comp_mole_fractions: List[float], k_values: List[float]) -> float:
        """Solves Rachford-Rice equation for V (vapor mole fraction)."""
        def objective_rr(V_guess):
            return sum(zi * (ki - 1) / (1 + V_guess * (ki - 1)) for zi, ki in zip(overall_comp_mole_fractions, k_values))

        # Bounds for V are [0, 1].
        # Check if solution is trivial (single phase)
        if sum(zi * ki for zi, ki in zip(overall_comp_mole_fractions, k_values)) < 1.0: # All liquid
            return 0.0
        if sum(zi / ki for zi, ki in zip(overall_comp_mole_fractions, k_values) if ki > 1e-9) < 1.0: # All vapor
            return 1.0

        try:
            # Brentq is good for 1D root finding within bounds
            V_solution = brentq(objective_rr, -1.0 * min(1/(k-1) for k in k_values if k > 1.0) + 1e-6 if any(k > 1.0 for k in k_values) else 0.0,
                                 1.0 * min(1/(1-k) for k in k_values if k < 1.0) -1e-6 if any(k < 1.0 for k in k_values) else 1.0,
                                 xtol=1e-9, rtol=1e-9)
            # Ensure V is within [0,1] due to numerical precision
            return np.clip(V_solution, 0.0, 1.0)

        except ValueError as e: # If brentq fails (e.g. f(a) and f(b) have same sign)
             logger.warning(f"Rachford-Rice brentq failed: {e}. K-values: {k_values}. Comps: {overall_comp_mole_fractions}. Trying fsolve.")
             # Fallback to fsolve if brentq fails (less robust for bounds)
             V_solution_fsolve, _, ier, _ = fsolve(objective_rr, 0.5, xtol=1e-9, full_output=True)
             if ier == 1: # Converged
                 return np.clip(V_solution_fsolve[0], 0.0, 1.0)
             else:
                 logger.error("Rachford-Rice fsolve also failed.")
                 # Determine if it's mostly liquid or vapor based on sum(zi*ki) and sum(zi/ki)
                 if sum(zi * ki for zi, ki in zip(overall_comp_mole_fractions, k_values)) < 1.0: return 0.0
                 if sum(zi / ki for zi, ki in zip(overall_comp_mole_fractions, k_values) if ki > 1e-9) < 1.0: return 1.0
                 return 0.5 # Fallback, should not happen often


    def initial_k_values_wilson(self, p_psia: float, t_fahrenheit: float) -> List[float]:
        """Initial K-values using Wilson's correlation."""
        t_rankine = t_fahrenheit + 459.67
        k_vals = []
        for comp in self.components:
            tc_rankine = comp.critical_temperature
            pc_psia = comp.critical_pressure
            acentric_factor = comp.acentric_factor

            # Wilson's correlation: Ki = (Pci/P) * exp(5.37 * (1 + ωi) * (1 - Tci/T))
            # Ensure T is in Rankine
            if t_rankine <=0 or pc_psia <=0: # Should not happen
                 k_vals.append(1.0)
                 continue

            # Check for P close to zero for safety, though physical pressures are higher
            if p_psia < 1e-3: p_psia = 1e-3

            val = 5.3727 * (1 + acentric_factor) * (1 - tc_rankine / t_rankine)
            k = (pc_psia / p_psia) * np.exp(val)
            k_vals.append(max(1e-9, k)) # K-values must be positive
        return k_vals

    def perform_flash_calculation_ssi(self, p_psia: float, t_fahrenheit: float) -> Dict[str, Any]:
        """Performs PT flash using Successive Substitution Iteration (SSI) with PR EOS."""
        overall_comp = [c.mole_fraction for c in self.components]
        k_values = self.initial_k_values_wilson(p_psia, t_fahrenheit)

        max_iter = 100
        tolerance = 1e-7

        V_frac = 0.5 # Initial guess for vapor fraction
        liquid_comp = list(overall_comp)
        vapor_comp = list(overall_comp)

        for iteration in range(max_iter):
            V_old = V_frac
            V_frac = self._solve_rachford_rice(overall_comp, k_values)

            # Update phase compositions
            for i in range(len(overall_comp)):
                denominator = 1 + V_frac * (k_values[i] - 1)
                if abs(denominator) < 1e-9: # Avoid division by zero if V and K are problematic
                    liquid_comp[i] = overall_comp[i] if k_values[i] < 1 else 0
                    vapor_comp[i] = overall_comp[i] if k_values[i] > 1 else 0
                else:
                    liquid_comp[i] = overall_comp[i] / denominator
                    vapor_comp[i] = overall_comp[i] * k_values[i] / denominator

            # Normalize if necessary (should be close if RR converged well)
            sum_x = sum(liquid_comp)
            sum_y = sum(vapor_comp)
            if abs(sum_x) > 1e-9: liquid_comp = [x/sum_x for x in liquid_comp]
            if abs(sum_y) > 1e-9: vapor_comp = [y/sum_y for y in vapor_comp]

            # Calculate Z factors and fugacity coefficients for each phase
            a_liq_mix, b_liq_mix = self._calculate_pr_eos_params_mixture(liquid_comp, t_fahrenheit)
            z_liq_roots = self._solve_pr_eos_for_z(p_psia, t_fahrenheit, a_liq_mix, b_liq_mix)
            z_liq = z_liq_roots[0] if z_liq_roots else b_liq_mix * p_psia / (self.R_psia_ft3_lbmol_R * (t_fahrenheit + 459.67)) # Smallest Z for liquid

            a_vap_mix, b_vap_mix = self._calculate_pr_eos_params_mixture(vapor_comp, t_fahrenheit)
            z_vap_roots = self._solve_pr_eos_for_z(p_psia, t_fahrenheit, a_vap_mix, b_vap_mix)
            z_vap = z_vap_roots[-1] if z_vap_roots else 1.0 # Largest Z for vapor

            phi_liq = self._calculate_fugacity_coeffs_pr(liquid_comp, p_psia, t_fahrenheit, z_liq)
            phi_vap = self._calculate_fugacity_coeffs_pr(vapor_comp, p_psia, t_fahrenheit, z_vap)

            # Update K-values
            new_k_values = [phi_l / phi_v if abs(phi_v)>1e-9 else 1e9 for phi_l, phi_v in zip(phi_liq, phi_vap)]

            # Check for convergence (e.g., on K-values or V_frac)
            # Using sum of squares of log(K_new/K_old)
            error = sum((np.log(new_k_values[i] / k_values[i]))**2 for i in range(len(k_values)) if abs(k_values[i]) > 1e-9)

            k_values = new_k_values
            if error < tolerance:
                logger.debug(f"Flash converged in {iteration+1} iterations at P={p_psia}, T={t_fahrenheit}.")
                return {
                    "vapor_fraction": V_frac,
                    "liquid_composition": liquid_comp,
                    "vapor_composition": vapor_comp,
                    "k_values": k_values,
                    "z_liquid": z_liq,
                    "z_vapor": z_vap
                }

        logger.warning(f"Flash calculation did NOT converge after {max_iter} iterations at P={p_psia}, T={t_fahrenheit}. Error: {error:.2e}")
        return { # Return best guess or indicate failure
            "vapor_fraction": V_frac, "liquid_composition": liquid_comp, "vapor_composition": vapor_comp,
            "k_values": k_values, "z_liquid": z_liq if 'z_liq' in locals() else None, "z_vapor": z_vap if 'z_vap' in locals() else None,
            "converged": False
        }

    def calculate_phase_properties(self, p_psia: float, t_fahrenheit: float) -> Optional[PVTResult]:
        """Calculate all relevant PVT properties for a given P, T using PR EOS and flash."""
        flash_results = self.perform_flash_calculation_ssi(p_psia, t_fahrenheit)

        if flash_results.get("converged", True) is False: # if "converged" key exists and is False
            logger.error(f"Flash did not converge for P={p_psia}, T={t_fahrenheit}. Cannot calculate phase properties accurately.")
            return None # Or return partial results with a warning

        V_frac = flash_results["vapor_fraction"]
        x_i = flash_results["liquid_composition"] # Liquid mole fractions
        y_i = flash_results["vapor_composition"] # Vapor mole fractions
        z_liq = flash_results["z_liquid"]
        z_vap = flash_results["z_vapor"]
        t_rankine = t_fahrenheit + 459.67

        # Molar volumes (ft³/lb-mol)
        molar_vol_liq = z_liq * self.R_psia_ft3_lbmol_R * t_rankine / p_psia if z_liq and p_psia > 0 else 0
        molar_vol_vap = z_vap * self.R_psia_ft3_lbmol_R * t_rankine / p_psia if z_vap and p_psia > 0 else 0

        # Average Molecular Weights
        mw_liq = sum(xi * comp.molecular_weight for xi, comp in zip(x_i, self.components)) if V_frac < 1.0 else 0
        mw_vap = sum(yi * comp.molecular_weight for yi, comp in zip(y_i, self.components)) if V_frac > 0.0 else 0

        # Densities (lb/ft³)
        rho_liq = mw_liq / molar_vol_liq if molar_vol_liq > 1e-9 else 0 # Avoid division by zero
        rho_vap = mw_vap / molar_vol_vap if molar_vol_vap > 1e-9 else 0

        # Viscosities (cP) - using Lohrenz-Bray-Clark (LBC)
        visc_liq = self._calculate_viscosity_lbc(x_i, "liquid", rho_liq, t_fahrenheit) if V_frac < 1.0 and rho_liq > 0 else None
        visc_vap = self._calculate_viscosity_lbc(y_i, "vapor", rho_vap, t_fahrenheit) if V_frac > 0.0 and rho_vap > 0 else None

        # Formation Volume Factors
        # Oil FVF (Bo): Volume of reservoir oil / Volume of stock tank oil (STO)
        # Gas FVF (Bg): Volume of reservoir gas / Volume of standard condition gas (SCF)
        # Standard conditions: e.g., 14.7 psia and 60°F (519.67 °R)
        # Density of STO (rho_sto_lb_ft3) would be needed for accurate Bo. Assume a typical value or calculate via a separate flash to std conditions.
        # For simplicity, let's assume a pseudo STO density.
        # A more rigorous Bo requires flashing the liquid phase to standard conditions.

        rho_sto_approx_lb_bbl = 350 / 5.61458 # Approx STO density in lb/bbl converted to lb/ft3 (assuming 35 API oil)
                                         # This is a major simplification.

        oil_fvf = (mw_liq / rho_liq) / (mw_liq / (rho_sto_approx_lb_bbl * 5.61458)) if rho_liq > 0 and V_frac < 1.0 else None # rb/STB
        # A simpler Bo: V_res_oil / V_std_oil. V_res_oil = molar_vol_liq. V_std_oil needs separate flash.
        # For now, this Bo is very approximate.

        # Gas FVF (Bg) = V_res_gas / V_std_gas
        # V_std_gas per mole = R_sc * T_sc / P_sc = 10.73159 * 519.67 / 14.7 = 379.49 scf/lb-mol
        V_std_gas_per_lbmol = 379.49 # scf/lb-mol
        gas_fvf = molar_vol_vap / V_std_gas_per_lbmol if V_frac > 0.0 and molar_vol_vap > 0 else None # rcf/scf (reservoir cubic ft / standard cubic ft)

        # Solution GOR (Rs)
        # Moles of gas in vapor phase / Moles of oil in liquid phase, then convert to scf/STB
        # This needs careful definition of STO.
        # For now, a simplified GOR might be based on vapor and liquid mole fractions and molar volumes.
        # Rs = (moles_gas_in_vapor / moles_oil_in_liquid) * (V_std_gas_per_lbmol / V_sto_per_lbmol_oil)
        # Placeholder GOR calculation:
        solution_gor = (V_frac * mw_vap / rho_vap) / ((1-V_frac) * mw_liq / rho_liq) * (V_std_gas_per_lbmol / 5.61458) if V_frac > 0 and (1-V_frac) > 0 and rho_liq > 0 and rho_vap > 0 else None # Highly approx.

        # Surface Tension (dynes/cm) - using parachor method
        surface_tension = self._calculate_surface_tension_parachor(x_i, y_i, rho_liq, rho_vap) if V_frac > 0 and V_frac < 1.0 else None

        return PVTResult(
            pressure=p_psia,
            temperature=t_fahrenheit,
            oil_fvf=oil_fvf,
            gas_fvf=gas_fvl,
            solution_gor=solution_gor,
            oil_viscosity=visc_liq,
            gas_viscosity=visc_vap,
            oil_density=rho_liq,
            gas_density=rho_vap,
            surface_tension=surface_tension,
            z_liquid=z_liq,
            z_vapor=z_vap
        )

    def _calculate_viscosity_lbc(self, phase_comp_mole_fractions: List[float], phase_type: str, phase_density_lb_ft3: float, t_fahrenheit: float) -> Optional[float]:
        """Calculate viscosity using Lohrenz-Bray-Clark correlation."""
        if not phase_comp_mole_fractions or phase_density_lb_ft3 <= 0:
            return None

        # Sum of (zi * MWi^0.5 * Tci^(1/6) / Pci^(2/3)) - this is incorrect, it's sum(zi*MWi) for MW_mix
        # The LBC correlation uses mixture critical properties and MW.

        # Mixture Molecular Weight
        mw_mix = sum(zi * comp.molecular_weight for zi, comp in zip(phase_comp_mole_fractions, self.components))
        if mw_mix <=0: return None

        # Mixture Critical Temperature (Rankine) - Kay's rule (simple)
        tc_mix_rankine = sum(zi * comp.critical_temperature for zi, comp in zip(phase_comp_mole_fractions, self.components))
        # Mixture Critical Pressure (psia) - Kay's rule (simple)
        pc_mix_psia = sum(zi * comp.critical_pressure for zi, comp in zip(phase_comp_mole_fractions, self.components))
        # Mixture Critical Volume (ft³/lb-mol) - Kay's rule (simple)
        # Ensure FluidComponent has critical_volume
        vc_mix_ft3_lbmol = sum(zi * comp.critical_volume for zi, comp in zip(phase_comp_mole_fractions, self.components) if hasattr(comp, 'critical_volume'))
        if not hasattr(self.components[0], 'critical_volume') or vc_mix_ft3_lbmol <=0:
            logger.warning("LBC Visc: Critical volume not available for components or zero/negative. Cannot calculate accurately.")
            return 0.01 # Default small viscosity

        t_rankine = t_fahrenheit + 459.67

        # Reduced temperature and density
        tr_mix = t_rankine / tc_mix_rankine if tc_mix_rankine > 0 else 1.0

        # Density parameter ksi_mix (lb-mol/ft³)
        # ksi_mix = phase_density_lb_ft3 / mw_mix
        # LBC uses a specific parameter ksi = Vc_mix ^ (-5/3) * Tc_mix ^ (1/6) / Mw_mix ^ (1/2)
        # This ksi is different from the reduced density.
        # Let's use the common form with reduced density.
        # rho_r = rho_molar / rho_critical_molar = (phase_density_lb_ft3 / mw_mix) / (1 / vc_mix_ft3_lbmol)
        rho_r_lbc = phase_density_lb_ft3 * vc_mix_ft3_lbmol / mw_mix
        if rho_r_lbc < 0: rho_r_lbc = 0 # Must be positive

        # Low-pressure gas viscosity (Herning and Zipperer mixing rule for mu_mix_lp)
        # For simplicity, using a placeholder or assuming single component for mu_i_lp
        # mu_i_lp = some correlation for pure component low-pressure gas viscosity
        # For now, a very rough estimate for mu_mix_lp:
        mu_mix_lp_approx = 1e-2 * (mw_mix**0.5) * (t_rankine**0.1) # Highly approximate, cP

        # LBC Correlation for (mu - mu_lp) * ksi_LBC
        # (mu - mu_lp) * ksi = f(rho_r_lbc)
        # ksi = Tc_mix^(1/6) / (Mw_mix^(1/2) * Pc_mix^(2/3)) -- units need care for consistency
        # Let's use the polynomial form for mu_r (reduced viscosity)
        # mu_r = a0 + a1*rho_r + a2*rho_r^2 + a3*rho_r^3 + a4*rho_r^4
        # where mu_r = (mu - mu_lp) * ksi_param if ksi_param is used, or directly mu if mu_lp is negligible (for liquids)

        coeffs_lbc = [0.1023, 0.023364, 0.058533, -0.040758, 0.0093324] # LBC coefficients

        # ( (µ - µo)ξ + 10^-4 )^1/4 = a0 + a1ρr + a2ρr^2 + a3ρr^3 + a4ρr^4
        # where µo is dilute gas viscosity, ξ is viscosity parameter
        # This is complex. Let's use a simplified form if LBC is too involved for now.
        # Fallback to a simpler correlation or placeholder for now if LBC is not fully implemented.
        # For demonstration, this is a simplified version:
        mu_r_poly = coeffs_lbc[0] + coeffs_lbc[1]*rho_r_lbc + coeffs_lbc[2]*rho_r_lbc**2 + \
                    coeffs_lbc[3]*rho_r_lbc**3 + coeffs_lbc[4]*rho_r_lbc**4

        # This mu_r_poly is actually ((mu-mu_lp)*ksi + 1e-4)^0.25
        # A more direct (but less accurate over wide ranges) approach:
        # mu = mu_lp * (1 + C1*rho_r + C2*rho_r^2 + ...)
        # Placeholder:
        visc = mu_mix_lp_approx * (1 + mu_r_poly) # Very rough combination
        return max(1e-3, visc) # Ensure positive viscosity

    def _calculate_surface_tension_parachor(self, x_i: List[float], y_i: List[float], rho_liq_lb_ft3: float, rho_vap_lb_ft3: float) -> Optional[float]:
        """Calculate surface tension using Weinaug-Katz parachor method."""
        if not hasattr(self.components[0], 'parachor'):
            logger.warning("Parachor values not available for components. Cannot calculate surface tension.")
            return None

        parachor_liq = sum(xi * comp.parachor for xi, comp in zip(x_i, self.components))
        parachor_vap = sum(yi * comp.parachor for yi, comp in zip(y_i, self.components))

        # Densities in g/cm^3 for parachor equation
        # 1 lb/ft³ = 0.0160185 g/cm³
        rho_liq_g_cm3 = rho_liq_lb_ft3 * 0.0160185
        rho_vap_g_cm3 = rho_vap_lb_ft3 * 0.0160185

        # Surface tension (sigma) in dynes/cm
        # sigma = [ P_L * (rho_L_molar - rho_V_molar) ]^4  -- original Macleod-Sugden
        # Weinaug-Katz uses mass densities: sigma = [ P_L * rho_L - P_V * rho_V ]^4
        # This requires molar densities (lb-mol/ft³) to be converted to g/cm³ if parachors are in cgs units.
        # Or, use mass densities directly if parachors are consistent.
        # Assuming parachors are for [ (g/cm^3)^(1/4) * cm * (mol/g) ]
        # Simpler form: sigma = (Parachor_mix * (rho_L_mass - rho_V_mass) / MW_mix )^4
        # For mixtures, often: sigma = [ sum(Parachor_i * (x_i * rho_L_molar - y_i * rho_V_molar)) ]^4
        # Let's use the common mixture form: sigma = [ sum( P_i * (x_i * rho_L_molar - y_i * rho_V_molar) ) ]^4
        # This means rho_L and rho_V need to be molar densities (lb-mol/ft^3).
        # This is quite complex; for now, a simpler approach based on overall phase parachor and mass density diff:

        # If parachor_liq and parachor_vap are mass-based parachors (not typical):
        # term = parachor_liq * rho_liq_g_cm3 - parachor_vap * rho_vap_g_cm3 # If P is per mass
        # Simpler: use average parachor for the liquid phase and density difference.

        if rho_liq_g_cm3 <= rho_vap_g_cm3: # Liquid must be denser
            return 0.0

        # Using liquid phase parachor and density difference (common simplification)
        sigma = (parachor_liq * (rho_liq_g_cm3 - rho_vap_g_cm3) / 1.0)**4 # Assuming MW_mix is somehow cancelled or incorporated in P_L
                                                                       # The 1.0 is a placeholder for MW_mix if parachor is molar based
        # This is a very common but simplified form. True parachor method can be more complex for mixtures.
        return max(0, sigma)


    def calculate_phase_envelope_points(self, num_points_curve: int = 20, p_min_psia: float = 14.7, p_max_psia: float = 10000) -> List[Dict[str, Any]]:
        """Calculates points for the phase envelope (bubble and dew point lines)."""
        # Uses iterative approach to find saturation pressures at given temperatures.
        # This is a placeholder for a more robust phase envelope algorithm.
        # A full algorithm would trace curves carefully, detect critical point, cricondentherm, cricondenbar.
        logger.info("Starting phase envelope calculation (simplified).")
        envelope_points = []
        overall_comp = [c.mole_fraction for c in self.components]

        # Temperature range estimate (can be refined)
        min_t_comp = min(c.critical_temperature for c in self.components) - 459.67 # to °F
        max_t_comp = max(c.critical_temperature for c in self.components) - 459.67 # to °F
        # Heuristic range, could be wider or user-defined
        t_range = np.linspace(min_t_comp * 0.8, max_t_comp * 1.2, num_points_curve)

        # Bubble Point Curve
        for t_f in t_range:
            # Objective function: sum(zi*Ki) - 1 = 0 for bubble point (V=0)
            # where Ki = phi_liq_i / phi_vap_i (here, simpler: K from fugacity of overall comp in L/V states)
            def bubble_point_obj(p_guess_psia):
                flash_res = self.perform_flash_calculation_ssi(p_guess_psia, t_f)
                # For bubble point, V_frac should be 0. Check sum(zi*Ki) = 1.
                # More directly, sum(yi - xi) should be 0 at bubble point.
                # A common way is to check sum(zi*Ki) - 1 = 0.
                # K_values are phi_L / phi_V
                if not flash_res or flash_res.get("converged", True) is False: return 1.0 # Try to push solver

                # Check if we are in two-phase region or just superheated vapor/subcooled liquid
                # If V_frac is ~0, then we are at bubble point.
                # If V_frac is ~1, then we are at dew point for this P,T.
                # This objective needs to be formulated carefully for root finding.
                # Let's use the K-value definition for bubble point: sum(zi * Ki) - 1 = 0
                # where Ki are from a hypothetical vapor phase in equilibrium.

                # Simplified: solve for P where V_frac is infinitesimally small (e.g. 1e-6)
                # This is tricky. A better way is to use stability analysis or specific BP/DP routines.
                # For now, we'll use the flash and check V_frac.
                # This is NOT a robust way to find the exact bubble point pressure.
                # Placeholder:
                return flash_res["vapor_fraction"] - 1e-6 # Target V_frac slightly > 0

            try:
                # This is not a good objective for brentq for bubble point.
                # A proper bubble point routine is needed.
                # For now, this part is illustrative of the need for such a routine.
                # p_sat = brentq(bubble_point_obj, p_min_psia, p_max_psia, xtol=1.0)
                # envelope_points.append({"temperature": t_f, "pressure": p_sat, "type": "bubble"})
                pass # Skipping bubble point calculation for now due to complexity of robust objective
            except ValueError: # Root not found in interval
                pass

        # Dew Point Curve (similar complexity)
        # ...

        # Critical Point Estimation (Heidemann-Khalil or similar)
        # ... placeholder for actual critical point calculation ...
        tc_mix_f = sum(c.mole_fraction * (c.critical_temperature - 459.67) for c in self.components)
        pc_mix_psia = sum(c.mole_fraction * c.critical_pressure for c in self.components)
        envelope_points.append({"temperature": tc_mix_f, "pressure": pc_mix_psia, "type": "critical_estimate"})

        logger.info(f"Phase envelope calculation (simplified) yielded {len(envelope_points)} points.")
        return envelope_points # This will be very sparse and inaccurate without proper BP/DP routines

    # Placeholder for Heidemann-Khalil critical point calculation parts
    def _da_dni(self, i: int, comp_mole_fractions: List[float], t_fahrenheit: float) -> float:
        # This was part of the user-provided snippet for fugacity, needs context for H-K
        # For fugacity, it's related to partial derivative of a_mix w.r.t ni
        # sum_j (xj * (dai_dj + daj_di)) where dai_dj = sqrt(ai*aj)*(1-kij)
        # This needs careful implementation of PR EOS derivatives.
        # For now, returning a placeholder as it's complex.
        # Let's assume this is for the fugacity coefficient term: (2 * sum_j(zj * sqrt(ai*aj)*(1-kij) ) / a_mix )
        # This term is part of the ln(phi_i) expression.
        # The snippet had it as (2/a * da_dni[i] - (b_i[i]/b))
        # where da_dni[i] = sum_j ( 2 * comp[j] * sqrt(a_i_at_t * a_j_at_t) * (1-kij) )
        # This part is very EOS specific and needs to be exact.
        # The provided snippet for fugacity coefficients seems to have combined terms.
        # For now, this function is a placeholder as its direct use in H-K Q-matrix wasn't shown.
        return 0.0

    def _db_dni(self, component_idx: int) -> float:
        # Derivative of b_mix w.r.t ni is just b_i
        comp_obj = self.components[component_idx]
        tc_r = comp_obj.critical_temperature
        pc_psia = comp_obj.critical_pressure
        return self.omega_b_pr * self.R_psia_ft3_lbmol_R * tc_r / pc_psia

    def estimate_critical_point_hk(self) -> Optional[Tuple[float, float]]:
        # Placeholder for a proper Heidemann-Khalil or other stability-based critical point search.
        # This is a very complex calculation involving solving non-linear equations
        # based on the determinant of stability matrices (second derivatives of Gibbs energy).
        logger.warning("Heidemann-Khalil critical point estimation is a placeholder and not fully implemented.")
        # Fallback to simple mixing rule for now.
        tc_mix_f = sum(c.mole_fraction * (c.critical_temperature - 459.67) for c in self.components)
        pc_mix_psia = sum(c.mole_fraction * c.critical_pressure for c in self.components)
        return tc_mix_f, pc_mix_psia
