import pytest
import logging
# Corrected import
from gaia_genesis.reservoir_engineering import PVTProperties

logger = logging.getLogger(__name__)

class TestPVTProperties:
    @pytest.fixture
    def pvt_props(self):
        """Fixture to create a PVTProperties instance."""
        return PVTProperties()

    def test_calculate_z_factor_hall_yarborough(self, pvt_props):
        """
        Test the Z-factor calculation using the Hall-Yarborough correlation.
        Test case: P = 3000 psia, T = 180 °F, Gas Specific Gravity = 0.7
        """
        pressure = 3000.0  # psia
        temperature_F = 180.0  # °F
        gas_specific_gravity = 0.7

        try:
            z_factor = pvt_props.calculate_z_factor(
                pressure=pressure,
                temperature=temperature_F,
                gas_specific_gravity=gas_specific_gravity
            )
            logger.info(f"Calculated Z-factor: {z_factor} for P={pressure}, T={temperature_F}, Sg={gas_specific_gravity}")
            assert 0.75 < z_factor < 0.90, f"Z-factor {z_factor} out of expected range for Hall-Yarborough."
        except Exception as e:
            logger.error(f"Error in test_calculate_z_factor_hall_yarborough: {e}", exc_info=True)
            pytest.fail(f"Z-factor calculation raised an exception: {e}")


    def test_calculate_z_factor_low_pressure(self, pvt_props):
        """
        Test Z-factor at low pressure, where it should approach 1.0.
        """
        pressure = 14.7  # psia (atmospheric pressure)
        temperature_F = 60.0  # °F
        gas_specific_gravity = 0.6

        try:
            z_factor = pvt_props.calculate_z_factor(
                pressure=pressure,
                temperature=temperature_F,
                gas_specific_gravity=gas_specific_gravity
            )
            logger.info(f"Calculated Z-factor (low P): {z_factor} for P={pressure}, T={temperature_F}, Sg={gas_specific_gravity}")
            assert 0.98 < z_factor <= 1.01, f"Z-factor {z_factor} should be close to 1.0 at low pressure."
        except Exception as e:
            logger.error(f"Error in test_calculate_z_factor_low_pressure: {e}", exc_info=True)
            pytest.fail(f"Z-factor calculation (low P) raised an exception: {e}")

    def test_calculate_oil_fvf_standing(self, pvt_props):
        """
        Test oil FVF (Bo) using Standing's correlation.
        """
        pressure = 2500.0
        temperature_F = 150.0
        api_gravity = 35.0
        gas_specific_gravity = 0.75 # Separator gas SG

        try:
            bo = pvt_props.calculate_formation_volume_factor(
                pressure=pressure,
                temperature=temperature_F,
                fluid_type='oil',
                api_gravity=api_gravity,
                gas_specific_gravity=gas_specific_gravity
            )
            logger.info(f"Calculated Oil FVF (Bo): {bo}")
            assert 1.05 < bo < 1.15, f"Oil FVF {bo} out of expected range."
        except Exception as e:
            logger.error(f"Error in test_calculate_oil_fvf_standing: {e}", exc_info=True)
            pytest.fail(f"Oil FVF calculation raised an exception: {e}")


    def test_calculate_gas_fvf(self, pvt_props):
        """
        Test gas FVF (Bg).
        """
        pressure = 3000.0
        temperature_F = 180.0
        gas_specific_gravity = 0.7

        try:
            z = pvt_props.calculate_z_factor(pressure, temperature_F, gas_specific_gravity)
            bg = pvt_props.calculate_formation_volume_factor(
                pressure=pressure,
                temperature=temperature_F,
                fluid_type='gas',
                gas_specific_gravity=gas_specific_gravity
            )
            logger.info(f"Calculated Gas FVF (Bg): {bg} using Z={z}")
            expected_bg = 0.02827 * z * (temperature_F + 459.67) / pressure
            assert abs(bg - expected_bg) < 1e-5, f"Gas FVF {bg} not matching expected {expected_bg}."
        except Exception as e:
            logger.error(f"Error in test_calculate_gas_fvf: {e}", exc_info=True)
            pytest.fail(f"Gas FVF calculation raised an exception: {e}")


    def test_calculate_oil_viscosity_beggs_robinson_sanity(self, pvt_props):
        """ Basic sanity check for oil viscosity """
        pressure = 2000.0
        temperature_F = 150.0
        api_gravity = 30.0
        gas_specific_gravity = 0.7

        try:
            mu_o = pvt_props.calculate_viscosity(
                pressure, temperature_F, 'oil', api_gravity, gas_specific_gravity
            )
            logger.info(f"Calculated Oil Viscosity: {mu_o}")
            assert 0.1 < mu_o < 20.0, f"Oil viscosity {mu_o} out of typical range."
        except Exception as e:
            logger.error(f"Error in test_calculate_oil_viscosity_beggs_robinson_sanity: {e}", exc_info=True)
            pytest.fail(f"Oil viscosity calculation raised an exception: {e}")


    def test_calculate_gas_viscosity_lee_gonzalez_eakin_sanity(self, pvt_props):
        """ Basic sanity check for gas viscosity """
        pressure = 2000.0
        temperature_F = 150.0
        gas_specific_gravity = 0.7

        try:
            mu_g = pvt_props.calculate_viscosity(
                pressure, temperature_F, 'gas', gas_specific_gravity=gas_specific_gravity
            )
            logger.info(f"Calculated Gas Viscosity: {mu_g}")
            assert 0.005 < mu_g < 0.1, f"Gas viscosity {mu_g} out of typical range."
        except Exception as e:
            logger.error(f"Error in test_calculate_gas_viscosity_lee_gonzalez_eakin_sanity: {e}", exc_info=True)
            pytest.fail(f"Gas viscosity calculation raised an exception: {e}")


    def test_calculate_solution_gas_ratio_standing_sanity(self, pvt_props):
        """ Basic sanity check for solution GOR """
        pressure = 2000.0
        temperature_F = 150.0
        api_gravity = 30.0
        gas_specific_gravity = 0.7

        try:
            rs = pvt_props.calculate_solution_gas_ratio(
                pressure, temperature_F, api_gravity, gas_specific_gravity
            )
            logger.info(f"Calculated Solution GOR (Rs): {rs}")
            assert 10 < rs < 5000, f"Solution GOR {rs} out of very broad typical range."
        except Exception as e:
            logger.error(f"Error in test_calculate_solution_gas_ratio_standing_sanity: {e}", exc_info=True)
            pytest.fail(f"Solution GOR calculation raised an exception: {e}")
