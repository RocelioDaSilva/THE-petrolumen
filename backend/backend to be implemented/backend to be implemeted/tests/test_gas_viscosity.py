"""Tests for backend/app/reservoir/gas_viscosity.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 1, Sec. 5.6, pp. 27-31, Eq. (1.25).
"""

import math
import pytest

from app.reservoir.gas_viscosity import (
    GasViscosityResult,
    gas_viscosity,
)


class TestLowDensityLimit:
    """At rho -> 0, Eq. (1.25) reduces to mu = 1e-4 * K exactly."""

    def test_K_only(self):
        # Mw=21.7, T=660 degR (200 F), z=1, p extremely small -> rho ~ 0
        T_R = 660.0
        Mw = 21.7
        expected_K = (
            (9.4 + 0.02 * Mw) * math.pow(T_R, 1.5)
            / (209.0 + 19.0 * Mw + T_R)
        )
        expected_mu = 1.0e-4 * expected_K
        r = gas_viscosity(
            p_psia=1.0e-8, T_F=200.0, z=1.0, Mw_g_mol=Mw,
        )
        assert isinstance(r, GasViscosityResult)
        assert r.mu_cp == pytest.approx(expected_mu, rel=1e-6)


class TestExample16Comparison:
    """Compare against book Example 1.6 (p. 29-30): p=2680 psia, T=212 F,
    gas_sg=0.90. Book chart answer: mu = 0.0192 cp.

    Tolerance 30%: (a) chart vs correlation is ~12% here, (b) Example 1.6
    also corrects for 5 mol% CO2 which LGE does not directly handle.
    """

    def test_2680_psia_212F(self):
        # Use z ~ 0.83 (Standing-Katz at ppr=4.0, Tpr=1.6 per Ex. 1.6)
        r = gas_viscosity(
            p_psia=2680.0, T_F=212.0, z=0.83, gas_sg=0.90,
        )
        assert r.mu_cp == pytest.approx(0.0192, rel=0.30)


class TestValidityFlag:
    def test_in_range(self):
        r = gas_viscosity(
            p_psia=3000.0, T_F=200.0, z=0.85, gas_sg=0.70,
        )
        assert r.in_validity_range is True

    def test_out_of_range_low_p(self):
        r = gas_viscosity(
            p_psia=50.0, T_F=200.0, z=0.98, gas_sg=0.70,
        )
        assert r.in_validity_range is False

    def test_out_of_range_high_T(self):
        r = gas_viscosity(
            p_psia=3000.0, T_F=400.0, z=0.90, gas_sg=0.70,
        )
        assert r.in_validity_range is False


class TestValidation:
    def test_p_zero(self):
        with pytest.raises(ValueError, match="p_psia must be > 0"):
            gas_viscosity(0.0, 200.0, 0.9, gas_sg=0.7)

    def test_p_negative(self):
        with pytest.raises(ValueError, match="p_psia must be > 0"):
            gas_viscosity(-1.0, 200.0, 0.9, gas_sg=0.7)

    def test_T_below_abs(self):
        with pytest.raises(ValueError, match="T_F must be above"):
            gas_viscosity(1000.0, -500.0, 0.9, gas_sg=0.7)

    def test_z_zero(self):
        with pytest.raises(ValueError, match="z must be > 0"):
            gas_viscosity(1000.0, 200.0, 0.0, gas_sg=0.7)

    def test_both_Mw_and_sg(self):
        with pytest.raises(ValueError, match="exactly one"):
            gas_viscosity(1000.0, 200.0, 0.9, Mw_g_mol=20.0, gas_sg=0.7)

    def test_neither_Mw_nor_sg(self):
        with pytest.raises(ValueError, match="exactly one"):
            gas_viscosity(1000.0, 200.0, 0.9)

    def test_gas_sg_zero(self):
        with pytest.raises(ValueError, match="gas_sg must be in"):
            gas_viscosity(1000.0, 200.0, 0.9, gas_sg=0.0)

    def test_gas_sg_too_high(self):
        with pytest.raises(ValueError, match="gas_sg must be in"):
            gas_viscosity(1000.0, 200.0, 0.9, gas_sg=2.5)

    def test_Mw_zero(self):
        with pytest.raises(ValueError, match="Mw_g_mol must be > 0"):
            gas_viscosity(1000.0, 200.0, 0.9, Mw_g_mol=0.0)


class TestDeterminism:
    def test_repeatable(self):
        a = gas_viscosity(2000.0, 180.0, 0.85, gas_sg=0.75)
        b = gas_viscosity(2000.0, 180.0, 0.85, gas_sg=0.75)
        assert a.mu_cp == b.mu_cp
