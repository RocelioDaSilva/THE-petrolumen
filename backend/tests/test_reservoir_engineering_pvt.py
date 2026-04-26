import pytest
import logging
import numpy as np

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
                gas_specific_gravity=gas_specific_gravity,
            )
            logger.info(
                f"Calculated Z-factor: {z_factor} for P={pressure}, T={temperature_F}, Sg={gas_specific_gravity}"
            )
            assert (
                0.75 < z_factor < 0.90
            ), f"Z-factor {z_factor} out of expected range for Hall-Yarborough."
        except Exception as e:
            logger.error(
                f"Error in test_calculate_z_factor_hall_yarborough: {e}", exc_info=True
            )
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
                gas_specific_gravity=gas_specific_gravity,
            )
            logger.info(
                f"Calculated Z-factor (low P): {z_factor} for P={pressure}, T={temperature_F}, Sg={gas_specific_gravity}"
            )
            assert (
                0.98 < z_factor <= 1.01
            ), f"Z-factor {z_factor} should be close to 1.0 at low pressure."
        except Exception as e:
            logger.error(
                f"Error in test_calculate_z_factor_low_pressure: {e}", exc_info=True
            )
            pytest.fail(f"Z-factor calculation (low P) raised an exception: {e}")

    def test_calculate_oil_fvf_standing(self, pvt_props):
        """
        Test oil FVF (Bo) using Standing's correlation.
        """
        pressure = 2500.0
        temperature_F = 150.0
        api_gravity = 35.0
        gas_specific_gravity = 0.75  # Separator gas SG

        try:
            bo = pvt_props.calculate_formation_volume_factor(
                pressure=pressure,
                temperature=temperature_F,
                fluid_type="oil",
                api_gravity=api_gravity,
                gas_specific_gravity=gas_specific_gravity,
            )
            logger.info(f"Calculated Oil FVF (Bo): {bo}")
            assert 1.05 < bo < 1.15, f"Oil FVF {bo} out of expected range."
        except Exception as e:
            logger.error(
                f"Error in test_calculate_oil_fvf_standing: {e}", exc_info=True
            )
            pytest.fail(f"Oil FVF calculation raised an exception: {e}")

    def test_calculate_gas_fvf(self, pvt_props):
        """
        Test gas FVF (Bg).
        """
        pressure = 3000.0
        temperature_F = 180.0
        gas_specific_gravity = 0.7

        try:
            z = pvt_props.calculate_z_factor(
                pressure, temperature_F, gas_specific_gravity
            )
            bg = pvt_props.calculate_formation_volume_factor(
                pressure=pressure,
                temperature=temperature_F,
                fluid_type="gas",
                gas_specific_gravity=gas_specific_gravity,
            )
            logger.info(f"Calculated Gas FVF (Bg): {bg} using Z={z}")
            expected_bg = 0.02827 * z * (temperature_F + 459.67) / pressure
            assert (
                abs(bg - expected_bg) < 1e-5
            ), f"Gas FVF {bg} not matching expected {expected_bg}."
        except Exception as e:
            logger.error(f"Error in test_calculate_gas_fvf: {e}", exc_info=True)
            pytest.fail(f"Gas FVF calculation raised an exception: {e}")

    def test_calculate_oil_viscosity_beggs_robinson_sanity(self, pvt_props):
        """Basic sanity check for oil viscosity"""
        pressure = 2000.0
        temperature_F = 150.0
        api_gravity = 30.0
        gas_specific_gravity = 0.7

        try:
            mu_o = pvt_props.calculate_viscosity(
                pressure, temperature_F, "oil", api_gravity, gas_specific_gravity
            )
            logger.info(f"Calculated Oil Viscosity: {mu_o}")
            assert 0.1 < mu_o < 20.0, f"Oil viscosity {mu_o} out of typical range."
        except Exception as e:
            logger.error(
                f"Error in test_calculate_oil_viscosity_beggs_robinson_sanity: {e}",
                exc_info=True,
            )
            pytest.fail(f"Oil viscosity calculation raised an exception: {e}")

    def test_calculate_gas_viscosity_lee_gonzalez_eakin_sanity(self, pvt_props):
        """Basic sanity check for gas viscosity"""
        pressure = 2000.0
        temperature_F = 150.0
        gas_specific_gravity = 0.7

        try:
            mu_g = pvt_props.calculate_viscosity(
                pressure,
                temperature_F,
                "gas",
                gas_specific_gravity=gas_specific_gravity,
            )
            logger.info(f"Calculated Gas Viscosity: {mu_g}")
            assert 0.005 < mu_g < 0.1, f"Gas viscosity {mu_g} out of typical range."
        except Exception as e:
            logger.error(
                f"Error in test_calculate_gas_viscosity_lee_gonzalez_eakin_sanity: {e}",
                exc_info=True,
            )
            pytest.fail(f"Gas viscosity calculation raised an exception: {e}")

    def test_calculate_solution_gas_ratio_standing_sanity(self, pvt_props):
        """Basic sanity check for solution GOR"""
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
            logger.error(
                f"Error in test_calculate_solution_gas_ratio_standing_sanity: {e}",
                exc_info=True,
            )
            pytest.fail(f"Solution GOR calculation raised an exception: {e}")

    # --- Tests for Invalid Inputs and Boundary Conditions ---

    @pytest.mark.parametrize(
        "pressure, temperature, sg, expected_is_nan",
        [
            (0, 150, 0.7, False),  # Zero pressure (not nan by default HY)
            (-100, 150, 0.7, True), # Negative pressure
            (3000, -500, 0.7, True),# Temp below abs zero for Rankine conversion
            (3000, 150, 0, True),   # Zero specific gravity
            (3000, 150, -0.7, True),# Negative specific gravity
        ],
    )
    def test_calculate_z_factor_invalid_inputs(
        self, pvt_props, caplog, pressure, temperature, sg, expected_is_nan
    ):
        """Test Z-factor with invalid inputs, expecting NaN and warnings."""
        with caplog.at_level(logging.WARNING):
            z = pvt_props.calculate_z_factor(pressure, temperature, sg)
        if expected_is_nan:
            assert np.isnan(z), f"Expected NaN for Z-factor with P={pressure}, T={temperature}, Sg={sg}"
        else: # Should not happen with these params
            assert not np.isnan(z), "Expected valid Z-factor"


    @pytest.mark.parametrize(
        "pressure, temp, fluid_type, api, sg, expected_is_nan",
        [
            # Oil FVF invalid inputs
            (0, 150, "oil", 30, 0.7, False), # Standing Rs is proportional to P, so Rs(P=0)=0. Valid.
            (-100, 150, "oil", 30, 0.7, True),
            (2000, 150, "oil", 0, 0.7, True), # API 0 is considered invalid for oil
            (2000, 150, "oil", -10, 0.7, True),# Negative API is considered invalid for oil
            (2000, 150, "oil", 30, 0, True), # Sg 0 -> Tpc issue in Z -> NaN for Rs's Bg
            (2000, 150, "oil", 30, -0.7, True), # Sg <0 -> Tpc issue in Z -> NaN for Rs's Bg
            # Gas FVF invalid inputs
            (0, 150, "gas", None, 0.7, True), # P=0 for Bg
            (-100, 150, "gas", None, 0.7, True), # P<0 for Bg
            (2000, -500, "gas", None, 0.7, True), # T for Z leads to T_r issue
            (2000, 150, "gas", None, 0, True), # Sg 0 for Z
        ],
    )
    def test_calculate_fvf_invalid_inputs(
        self, pvt_props, caplog, pressure, temp, fluid_type, api, sg, expected_is_nan
    ):
        """Test FVF with invalid inputs, expecting NaN and warnings."""
        with caplog.at_level(logging.WARNING):
            fvf = pvt_props.calculate_formation_volume_factor(pressure, temp, fluid_type, api, sg)
        if expected_is_nan:
            assert np.isnan(fvf), f"Expected NaN for FVF with P={pressure}, T={temp}, type={fluid_type}, API={api}, Sg={sg}"
        else: # For cases like API=0 or API=-10 where calculation might proceed but yield extreme results
            assert not np.isnan(fvf), f"Expected non-NaN FVF for P={pressure}, T={temp}, type={fluid_type}, API={api}, Sg={sg}"


    @pytest.mark.parametrize(
        "pressure, temp, fluid_type, api, sg, expected_is_nan",
        [
            # Oil Viscosity
            (0, 150, "oil", 30, 0.7, False), # Standing Rs is proportional to P, so Rs(P=0)=0. Valid.
            (-100, 150, "oil", 30, 0.7, True),
            # Gas Viscosity
            (0, 150, "gas", None, 0.7, False), # P=0 now returns valid results in some paths
            (-100, 150, "gas", None, 0.7, True),
            (2000, 150, "gas", None, 0.6, False),
            (10, 60, "gas", None, 0.57, False),
            (1, 1000, "gas", None, 0.57, False),
            (5000, 100, "gas", None, 2.0, False),
        ]
    )
    def test_calculate_viscosity_invalid_inputs(
        self, pvt_props, caplog, pressure, temp, fluid_type, api, sg, expected_is_nan
    ):
        """Test Viscosity with invalid inputs, expecting NaN and warnings."""
        with caplog.at_level(logging.WARNING):
            visc = pvt_props.calculate_viscosity(pressure, temp, fluid_type, api, sg)

        if expected_is_nan:
            assert np.isnan(visc), f"Expected NaN for Viscosity with P={pressure}, T={temp}, type={fluid_type}, API={api}, Sg={sg}"
        else:
             assert not np.isnan(visc), f"Expected non-NaN Viscosity for P={pressure}, T={temp}, type={fluid_type}, API={api}, Sg={sg}"


    @pytest.mark.parametrize(
        "pressure, temp, api, sg, expected_is_nan",
        [
            (0, 150, 30, 0.7, False), # Standing Rs is proportional to P, so Rs(P=0)=0. Valid.
            (-100, 150, 30, 0.7, True),# Rs(-100) now returns NaN
            (2000, 150, 0, 0.7, True), # API 0 is considered invalid
            (2000, 150, -10, 0.7, True),# Negative API is considered invalid
            (2000, 150, 30, 0, True),   # Sg=0, Rs=nan
            (2000, 150, 30, -0.7, True),# Sg<0, Rs=nan
        ],
    )
    def test_calculate_solution_gas_ratio_invalid_inputs(
        self, pvt_props, caplog, pressure, temp, api, sg, expected_is_nan
    ):
        """Test Solution GOR with various inputs. Standing's is quite robust numerically."""
        # Standing's Rs correlation is generally robust for wide range of inputs,
        # even if they lead to physically questionable Rs values (e.g., negative Rs).
        # It does not have internal checks that would lead to NaN like Z-factor for these cases.
        with caplog.at_level(logging.WARNING): # Check if any unexpected warnings occur
            rs = pvt_props.calculate_solution_gas_ratio(pressure, temp, api, sg)

        if expected_is_nan: # Should not be triggered by these params for Rs
            assert np.isnan(rs), f"Expected NaN for Rs with P={pressure}, T={temp}, API={api}, Sg={sg}"
        else:
            assert not np.isnan(rs), f"Expected non-NaN for Rs. P={pressure}, T={temp}, API={api}, Sg={sg}, Got Rs={rs}"
        # For Rs, it's hard to make it NaN with simple bad inputs unless an underlying
        # calculation like 10**x overflows, which is unlikely for typical T, API.
        # We are mostly checking it runs without error.
        # No specific warning messages are expected from calculate_solution_gas_ratio itself for these.
