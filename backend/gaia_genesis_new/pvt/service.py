from typing import Dict, List, Tuple, Optional, Any

# Assuming core.py contains BlackOilModel, CompositionalModel, PVTResult, FluidComponent
from .core import BlackOilModel, CompositionalModel, PVTResult
# FluidComponent will be used via schemas for API input, then passed to CompositionalModel
from backend.gaia_genesis_new.api_v1.schemas import FluidComponent as FluidComponentSchema
from backend.gaia_genesis_new.logger import logger

class PVTService:
    def __init__(self):
        # Store models in memory for this service instance.
        # For persistence, these would need to be saved/loaded from a database
        # via the DataManager.
        self.black_oil_models: Dict[str, BlackOilModel] = {}
        self.compositional_models: Dict[str, CompositionalModel] = {}
        logger.info("PVTService initialized.")

    def create_black_oil_model(self, name: str, pvt_data_dict: Dict[str, float]) -> bool:
        if name in self.black_oil_models or name in self.compositional_models:
            logger.warning(f"PVT Model with name '{name}' already exists.")
            return False
        try:
            self.black_oil_models[name] = BlackOilModel(pvt_data_dict)
            logger.info(f"Black oil model '{name}' created successfully.")
            return True
        except Exception as e:
            logger.error(f"Error creating black oil model '{name}': {e}", exc_info=True)
            return False

    def create_compositional_model(self, name: str, components_schema: List[FluidComponentSchema]) -> bool:
        if name in self.black_oil_models or name in self.compositional_models:
            logger.warning(f"PVT Model with name '{name}' already exists.")
            return False
        try:
            # Convert Pydantic schema components to core.FluidComponent if they are different
            # Assuming they are compatible for now, or core.FluidComponent is the Pydantic one.
            # If FluidComponent in core.py is NOT a Pydantic model, conversion is needed.
            # Based on previous core.py, FluidComponent IS a Pydantic model.
            core_components = [comp for comp in components_schema] # Direct use if Pydantic model
            self.compositional_models[name] = CompositionalModel(core_components)
            logger.info(f"Compositional model '{name}' created successfully.")
            return True
        except Exception as e:
            logger.error(f"Error creating compositional model '{name}': {e}", exc_info=True)
            return False

    def get_black_oil_model(self, name: str) -> Optional[BlackOilModel]:
        return self.black_oil_models.get(name)

    def get_compositional_model(self, name: str) -> Optional[CompositionalModel]:
        return self.compositional_models.get(name)

    def calculate_pvt_properties(self, model_name: str, p_psia: float, t_fahrenheit: float) -> Optional[PVTResult]:
        logger.debug(f"Calculating PVT properties for model '{model_name}' at P={p_psia} psi, T={t_fahrenheit}°F.")
        if model_name in self.black_oil_models:
            model = self.black_oil_models[model_name]
            try:
                # Black Oil calculations
                rs = model.calculate_solution_gor_standing(p_psia)
                bo = model.calculate_oil_fvf_standing(p_psia, rs_input=rs)
                bg = model.calculate_gas_fvf(p_psia, t_fahrenheit)
                mu_o = model.calculate_oil_viscosity_beggs_robinson(p_psia, rs_input=rs)

                # Gas viscosity and densities need Z-factor, which is part of Bg calc
                z_gas = model.calculate_z_factor_hall_yarborough(p_psia, t_fahrenheit) # Recalculate or get from Bg

                # Gas density (lb/ft³) = P * MW_gas / (Z * R_gas * T_abs)
                # MW_gas = gamma_g * 28.96
                mw_gas = model.gamma_g * 28.96
                t_rankine = t_fahrenheit + 459.67
                rho_g = (p_psia * mw_gas) / (z_gas * 10.73159 * t_rankine) if z_gas > 0 and t_rankine > 0 else 0.0

                mu_g = model.calculate_gas_viscosity_lee_gonzalez_eakin(p_psia, t_fahrenheit, gas_density_lb_ft3=rho_g)

                # Oil density (lb/ft³) - approximated from specific gravity and Bo
                # rho_o = (gamma_o * 62.4 + Rs * gamma_g * 0.0764) / Bo  (approximate formula)
                # This is complex; using a simpler placeholder for now.
                # rho_o_sto = model.gamma_o * 62.4 # STO density in lb/ft^3
                # rho_o = rho_o_sto / bo # This is not quite right, as Bo includes dissolved gas.
                # For black oil, often density is correlated directly or derived from Bo and Rs.
                # Placeholder:
                rho_o_approx = model.gamma_o * 62.4 / bo if bo > 0 else model.gamma_o * 62.4

                return PVTResult(
                    pressure=p_psia,
                    temperature=t_fahrenheit,
                    oil_fvf=bo,
                    gas_fvf=bg,
                    solution_gor=rs,
                    oil_viscosity=mu_o,
                    gas_viscosity=mu_g,
                    oil_density=rho_o_approx,
                    gas_density=rho_g,
                    z_vapor=z_gas # Storing gas Z-factor
                )
            except Exception as e:
                logger.error(f"Error calculating black oil properties for '{model_name}': {e}", exc_info=True)
                return None

        elif model_name in self.compositional_models:
            model = self.compositional_models[model_name]
            try:
                # Compositional calculations
                # The calculate_phase_properties method in CompositionalModel should return a PVTResult
                pvt_result_comp = model.calculate_phase_properties(p_psia, t_fahrenheit)
                return pvt_result_comp # This should be an instance of PVTResult or None
            except Exception as e:
                logger.error(f"Error calculating compositional properties for '{model_name}': {e}", exc_info=True)
                return None
        else:
            logger.warning(f"PVT model '{model_name}' not found.")
            raise ValueError(f"Unknown PVT model: {model_name}")

    def generate_pvt_table(self, model_name: str,
                          pressure_points_psia: List[float], # Changed to list of specific pressures
                          t_fahrenheit: float) -> List[PVTResult]:
        """Generate PVT table for a list of pressures at a given temperature."""
        results = []
        logger.info(f"Generating PVT table for model '{model_name}' at T={t_fahrenheit}°F for {len(pressure_points_psia)} pressures.")
        for p_psia in sorted(list(set(pressure_points_psia))): # Ensure unique sorted pressures
            if p_psia <=0: continue # Skip invalid pressures
            props = self.calculate_pvt_properties(model_name, p_psia, t_fahrenheit)
            if props:
                results.append(props)
            else:
                # Add a placeholder or error entry if calculation fails for a point
                results.append(PVTResult(pressure=p_psia, temperature=t_fahrenheit)) # Minimal entry
        return results

    def generate_phase_envelope(self, model_name: str,
                                num_points_curve: int = 20,
                                p_min_psia: float = 14.7,
                                p_max_psia: float = 10000) -> List[Dict[str, Any]]:
        """Generate phase envelope data points for a compositional model."""
        if model_name not in self.compositional_models:
            logger.warning(f"Model '{model_name}' not found or is not a compositional model for phase envelope.")
            raise ValueError("Model not found or not compositional type.")

        model = self.compositional_models[model_name]
        try:
            # This method in core.CompositionalModel needs to be robust.
            envelope_points = model.calculate_phase_envelope_points(
                num_points_curve=num_points_curve,
                p_min_psia=p_min_psia,
                p_max_psia=p_max_psia
            )
            return envelope_points
        except Exception as e:
            logger.error(f"Error generating phase envelope for model '{model_name}': {e}", exc_info=True)
            return [] # Return empty list on error

    def list_available_models(self) -> Dict[str, List[str]]:
        return {
            "black_oil_models": list(self.black_oil_models.keys()),
            "compositional_models": list(self.compositional_models.keys())
        }

    def get_model_type(self, model_name: str) -> Optional[str]:
        if model_name in self.black_oil_models:
            return "black_oil"
        if model_name in self.compositional_models:
            return "compositional"
        return None

# Global instance (singleton-like for simple in-memory storage for now)
# In a more complex app, this might be managed by FastAPI's dependency injection
# or a more sophisticated service locator pattern if PVTService had dependencies.
pvt_service_global_instance = PVTService()
