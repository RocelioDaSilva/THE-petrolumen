"""Tests for backend/app/reservoir/oil_viscosity.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 1, Sec. 6.4, pp. 40-44, Eqs. (1.34)-(1.36),
Example 1.7 (pp. 42-44).
"""

import pytest

from app.reservoir.oil_viscosity import (
    OilViscosityResult,
    oil_viscosity,
)


class TestExample17AbovePB:
    """Example 1.7 (p. 43): at 4000 psia (>pb=2500), mu_o = 0.470 cp.
    Tolerance: 0.01 cp absolute (book rounds to 3 decimals).
    """

    def test_4000_psia(self):
        r = oil_viscosity(
            p_psia=4000.0, T_F=180.0, gas_sg=0.80,
            oil_api=40.0, pb_psia=2500.0,
        )
        assert isinstance(r, OilViscosityResult)
        assert r.formulation == "vasquez_beggs"
        assert r.mu_cp == pytest.approx(0.470, abs=0.01)
        assert r.m is not None


class TestExample17BelowPB:
    """Example 1.7 (p. 44): at 2000 psia (<pb=2500), mu_o = 0.458 cp.
    Tolerance: 0.01 cp absolute.
    """

    def test_2000_psia(self):
        r = oil_viscosity(
            p_psia=2000.0, T_F=180.0, gas_sg=0.80,
            oil_api=40.0, pb_psia=2500.0,
        )
        assert r.formulation == "beggs_robinson"
        assert r.mu_cp == pytest.approx(0.458, abs=0.01)
        assert r.m is None


class TestExample17Intermediates:
    """Example 1.7 intermediates: mu_od=1.444 cp; mu_ob=0.400 cp.
    Tolerance: 0.01 cp on mu_ob; 0.01 cp on mu_od.
    """

    def test_mu_od(self):
        r = oil_viscosity(
            p_psia=2500.0, T_F=180.0, gas_sg=0.80,
            oil_api=40.0, pb_psia=2500.0,
        )
        assert r.mu_od_cp == pytest.approx(1.444, abs=0.01)

    def test_mu_ob(self):
        r = oil_viscosity(
            p_psia=2500.0, T_F=180.0, gas_sg=0.80,
            oil_api=40.0, pb_psia=2500.0,
        )
        assert r.mu_ob_cp == pytest.approx(0.400, abs=0.01)


class TestFormulationSwitch:
    """Below pb uses B-R; above pb uses V-B."""

    def test_at_pb_uses_br(self):
        r = oil_viscosity(
            p_psia=2500.0, T_F=180.0, gas_sg=0.80,
            oil_api=40.0, pb_psia=2500.0,
        )
        assert r.formulation == "beggs_robinson"

    def test_above_pb_uses_vb(self):
        r = oil_viscosity(
            p_psia=3000.0, T_F=180.0, gas_sg=0.80,
            oil_api=40.0, pb_psia=2500.0,
        )
        assert r.formulation == "vasquez_beggs"


class TestValidation:
    def test_p_zero(self):
        with pytest.raises(ValueError, match="p_psia must be > 0"):
            oil_viscosity(0.0, 180.0, 0.80, 40.0, 2500.0)

    def test_pb_zero(self):
        with pytest.raises(ValueError, match="pb_psia must be > 0"):
            oil_viscosity(2000.0, 180.0, 0.80, 40.0, 0.0)

    def test_T_negative(self):
        with pytest.raises(ValueError, match="T_F must be above"):
            oil_viscosity(2000.0, -500.0, 0.80, 40.0, 2500.0)

    def test_T_zero_or_below_for_log(self):
        # T in (-459.67, 0] is physically valid but log10(T) fails.
        with pytest.raises(ValueError, match="log10\\(T\\) in Eq\\. 1.34"):
            oil_viscosity(2000.0, 0.0, 0.80, 40.0, 2500.0)

    def test_gas_sg_invalid(self):
        with pytest.raises(ValueError, match="gas_sg must be in"):
            oil_viscosity(2000.0, 180.0, 2.5, 40.0, 2500.0)

    def test_api_invalid(self):
        with pytest.raises(ValueError, match="oil_api must be in"):
            oil_viscosity(2000.0, 180.0, 0.80, 150.0, 2500.0)


class TestValidityFlag:
    def test_in_range_below_pb(self):
        r = oil_viscosity(2000.0, 180.0, 0.80, 40.0, 2500.0)
        assert r.in_validity_range is True

    def test_api_out_of_br_range(self):
        # API=10 below BR_API_MIN=16
        r = oil_viscosity(2000.0, 180.0, 0.80, 10.0, 2500.0)
        assert r.in_validity_range is False


class TestDeterminism:
    def test_repeatable(self):
        a = oil_viscosity(2000.0, 180.0, 0.80, 40.0, 2500.0)
        b = oil_viscosity(2000.0, 180.0, 0.80, 40.0, 2500.0)
        assert a.mu_cp == b.mu_cp
