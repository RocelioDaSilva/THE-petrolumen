import pytest
from backend.gaia_genesis.reservoir_engineering import PVTProperties

class TestPVTProperties:
    @pytest.fixture
    def pvt_props(self):
        """Fixture to create a PVTProperties instance."""
        return PVTProperties()

    def test_calculate_z_factor_hall_yarborough(self, pvt_props):
        """
        Test the Z-factor calculation using the Hall-Yarborough correlation.
        Test case: P = 3000 psia, T = 180 °F, Gas Specific Gravity = 0.7
        Expected Tr ~ 1.643, Pr ~ 4.483.
        Expected Z-factor from charts is around 0.80-0.85.
        The Hall-Yarborough correlation should be in this range.
        """
        pressure = 3000.0  # psia
        temperature_F = 180.0  # °F
        gas_specific_gravity = 0.7

        z_factor = pvt_props.calculate_z_factor(
            pressure=pressure,
            temperature=temperature_F,
            gas_specific_gravity=gas_specific_gravity
        )

        # Assert that the Z-factor is within a plausible range for these conditions
        # Using a slightly wider range for initial automated test.
        # A more precise value would require manual calculation or a trusted source
        # for Hall-Yarborough with these exact inputs.
        assert 0.75 < z_factor < 0.90, f"Z-factor {z_factor} out of expected range for Hall-Yarborough."

    def test_calculate_z_factor_low_pressure(self, pvt_props):
        """
        Test Z-factor at low pressure, where it should approach 1.0.
        """
        pressure = 14.7  # psia (atmospheric pressure)
        temperature_F = 60.0  # °F
        gas_specific_gravity = 0.6

        z_factor = pvt_props.calculate_z_factor(
            pressure=pressure,
            temperature=temperature_F,
            gas_specific_gravity=gas_specific_gravity
        )
        # At very low pressures, Z should be close to 1.0
        assert 0.98 < z_factor <= 1.01, f"Z-factor {z_factor} should be close to 1.0 at low pressure."

    # It would be good to add tests for other PVT methods here as well,
    # e.g., calculate_formation_volume_factor, calculate_viscosity, calculate_solution_gas_ratio
    # with known inputs and expected outputs if available.

    def test_calculate_oil_fvf_standing(self, pvt_props):
        """
        Test oil FVF (Bo) using Standing's correlation.
        P = 2500 psia, T = 150 °F, API = 35, Sg = 0.75
        Rs (Standing) for these params:
        x = 0.0125 * 35 - 0.00091 * 150 = 0.4375 - 0.1365 = 0.301
        Rs = 0.75 * (2500/18.2 + 1.4) * 10**0.301
           = 0.75 * (137.36 + 1.4) * 1.9998
           = 0.75 * 138.76 * 1.9998 ~ 208.1 scf/STB

        F = Rs * (Sg/gamma_o_sg_equiv)^0.5 + 1.25 * T  -- (gamma_o_sg_equiv is not used in this version of Standing for Bo)
          Standing's Bo uses Sg of separator gas.
        F = 208.1 * (0.75/0.7)**0.5 + 1.25 * 150
          = 208.1 * (1.071)**0.5 + 187.5
          = 208.1 * 1.035 + 187.5
          = 215.38 + 187.5 = 402.88

        Bo = 0.972 + 0.000147 * F^1.175
           = 0.972 + 0.000147 * (402.88)^1.175
           = 0.972 + 0.000147 * (402.88 * 402.88**0.175)
           = 0.972 + 0.000147 * (402.88 * 1.84)
           = 0.972 + 0.000147 * 741.3
           = 0.972 + 0.1089
           ~ 1.0809 rb/STB
        """
        pressure = 2500.0
        temperature_F = 150.0
        api_gravity = 35.0
        gas_specific_gravity = 0.75 # Separator gas SG

        bo = pvt_props.calculate_formation_volume_factor(
            pressure=pressure,
            temperature=temperature_F,
            fluid_type='oil',
            api_gravity=api_gravity,
            gas_specific_gravity=gas_specific_gravity
        )
        # Based on manual calculation above, expecting ~1.08
        assert 1.05 < bo < 1.15, f"Oil FVF {bo} out of expected range."

    def test_calculate_gas_fvf(self, pvt_props):
        """
        Test gas FVF (Bg).
        P = 3000 psia, T = 180 °F, Sg = 0.7
        Z-factor from previous test for these conditions was ~0.82 (using the test's actual result for consistency)
        """
        pressure = 3000.0
        temperature_F = 180.0
        gas_specific_gravity = 0.7

        # Get Z from the z-factor method
        z = pvt_props.calculate_z_factor(pressure, temperature_F, gas_specific_gravity)

        bg = pvt_props.calculate_formation_volume_factor(
            pressure=pressure,
            temperature=temperature_F,
            fluid_type='gas',
            gas_specific_gravity=gas_specific_gravity
        )
        # Expected Bg = 0.02827 * Z * T_rankine / P
        # T_rankine = 180 + 459.67 = 639.67 °R
        expected_bg = 0.02827 * z * (temperature_F + 459.67) / pressure
        assert abs(bg - expected_bg) < 1e-5, f"Gas FVF {bg} not matching expected {expected_bg}."

    # TODO: Add tests for calculate_viscosity and calculate_solution_gas_ratio
    # with known reference values if possible.
    # For now, just basic sanity checks or placeholder tests.

    def test_calculate_oil_viscosity_beggs_robinson_sanity(self, pvt_props):
        """ Basic sanity check for oil viscosity """
        pressure = 2000.0
        temperature_F = 150.0
        api_gravity = 30.0
        gas_specific_gravity = 0.7

        mu_o = pvt_props.calculate_viscosity(
            pressure, temperature_F, 'oil', api_gravity, gas_specific_gravity
        )
        # Expected oil viscosity is typically in 0.1 - 10 cP range for conventional oils
        assert 0.1 < mu_o < 20.0, f"Oil viscosity {mu_o} out of typical range."

    def test_calculate_gas_viscosity_lee_gonzalez_eakin_sanity(self, pvt_props):
        """ Basic sanity check for gas viscosity """
        pressure = 2000.0
        temperature_F = 150.0
        gas_specific_gravity = 0.7

        mu_g = pvt_props.calculate_viscosity(
            pressure, temperature_F, 'gas', gas_specific_gravity=gas_specific_gravity
        )
        # Expected gas viscosity is typically in 0.01 - 0.05 cP range
        assert 0.005 < mu_g < 0.1, f"Gas viscosity {mu_g} out of typical range."

    def test_calculate_solution_gas_ratio_standing_sanity(self, pvt_props):
        """ Basic sanity check for solution GOR """
        pressure = 2000.0
        temperature_F = 150.0
        api_gravity = 30.0
        gas_specific_gravity = 0.7

        rs = pvt_props.calculate_solution_gas_ratio(
            pressure, temperature_F, api_gravity, gas_specific_gravity
        )
        # Rs can vary widely, but for typical oil, it might be in 50 - 2000 scf/STB
        assert 10 < rs < 5000, f"Solution GOR {rs} out of very broad typical range."
