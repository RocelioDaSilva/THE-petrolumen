"""Tests for backend/app/reservoir/oil_compressibility.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 1, Sec. 6.3, pp. 38-40, Eqs. (1.32)-(1.33),
Example 1.7 (pp. 42-43).
"""

import pytest

from app.reservoir.oil_compressibility import (
    OilCompressibilityResult,
    oil_compressibility,
)


class TestExample17AbovePB:
    """Example 1.7 p. 42: at p=4000 (>pb=2500), co=12.7e-6 psi^-1 (V-B).
    Tolerance: 5% relative.
    """

    def test_4000_psia(self):
        r = oil_compressibility(
            p_psia=4000.0, T_F=180.0, gas_sg=0.80,
            oil_api=40.0, pb_psia=2500.0,
        )
        assert isinstance(r, OilCompressibilityResult)
        assert r.formulation == "vasquez_beggs"
        assert r.co_psi_inv == pytest.approx(12.7e-6, rel=0.05)


class TestExample17BelowPB:
    """Example 1.7 p. 43: at p=2000 (<pb=2500), co=183e-6 psi^-1 (V-L).
    Tolerance: 5% relative.
    """

    def test_2000_psia(self):
        r = oil_compressibility(
            p_psia=2000.0, T_F=180.0, gas_sg=0.80,
            oil_api=40.0, pb_psia=2500.0,
        )
        assert r.formulation == "villena_lanzi"
        assert r.co_psi_inv == pytest.approx(183e-6, rel=0.05)


class TestFormulationSwitch:
    """p <= pb uses V-L; p > pb uses V-B."""

    def test_at_pb_uses_vl(self):
        r = oil_compressibility(
            p_psia=2500.0, T_F=180.0, gas_sg=0.80,
            oil_api=40.0, pb_psia=2500.0,
        )
        assert r.formulation == "villena_lanzi"

    def test_above_pb_uses_vb(self):
        r = oil_compressibility(
            p_psia=3000.0, T_F=180.0, gas_sg=0.80,
            oil_api=40.0, pb_psia=2500.0,
        )
        assert r.formulation == "vasquez_beggs"


class TestRsobEchoed:
    def test_rsob_matches_feature4(self):
        # Feature 4 Example 1.7 value: Rsob = 772 SCF/STB
        r = oil_compressibility(
            p_psia=2000.0, T_F=180.0, gas_sg=0.80,
            oil_api=40.0, pb_psia=2500.0,
        )
        assert r.rsob_scf_stb == pytest.approx(772.0, abs=2.0)


class TestValidation:
    def test_p_zero(self):
        with pytest.raises(ValueError, match="p_psia must be > 0"):
            oil_compressibility(0.0, 180.0, 0.80, 40.0, 2500.0)

    def test_pb_zero(self):
        with pytest.raises(ValueError, match="pb_psia must be > 0"):
            oil_compressibility(2000.0, 180.0, 0.80, 40.0, 0.0)

    def test_T_below_abs(self):
        with pytest.raises(ValueError, match="T_F must be above"):
            oil_compressibility(2000.0, -500.0, 0.80, 40.0, 2500.0)

    def test_gas_sg_invalid(self):
        with pytest.raises(ValueError, match="gas_sg must be in"):
            oil_compressibility(2000.0, 180.0, 2.5, 40.0, 2500.0)

    def test_api_invalid(self):
        with pytest.raises(ValueError, match="oil_api must be in"):
            oil_compressibility(2000.0, 180.0, 0.80, 150.0, 2500.0)

    def test_api_nonpositive_below_pb(self):
        # oil_api=0 breaks ln(API); API must be > 0 for V-L.
        with pytest.raises(ValueError, match="ln\\(API\\) requires"):
            oil_compressibility(2000.0, 180.0, 0.80, 0.0, 2500.0)


class TestNumeratorGuard:
    """V-B numerator <= 0 must raise, not return negative co."""

    def test_negative_numerator(self):
        # Very low API pushes 12.61*API down; low Rsob; high sg.
        # pb small so Rsob is small.
        with pytest.raises(ValueError, match="numerator"):
            oil_compressibility(
                p_psia=3000.0, T_F=100.0, gas_sg=1.90,
                oil_api=17.0, pb_psia=200.0,
            )


class TestValidityFlag:
    def test_in_range_below_pb(self):
        r = oil_compressibility(2000.0, 180.0, 0.80, 40.0, 2500.0)
        # p=2000 < 500? No, it's > 500. pb=2500 in [763, 5300].
        # T=180 in [78, 330]. Rsob~772 in [1.5, 1947].
        # API=40 in [6, 52]. sg=0.80 in [0.58, 1.20].
        # Actually V-L requires p >= 500, and p=2000 qualifies.
        assert r.in_validity_range is True

    def test_api_out_of_range_below_pb(self):
        # API=8 < VL_API_MIN=6? No, 8 > 6. Use 4:
        r = oil_compressibility(2000.0, 180.0, 0.80, 4.0, 2500.0)
        assert r.in_validity_range is False


class TestDeterminism:
    def test_repeatable(self):
        a = oil_compressibility(2000.0, 180.0, 0.80, 40.0, 2500.0)
        b = oil_compressibility(2000.0, 180.0, 0.80, 40.0, 2500.0)
        assert a.co_psi_inv == b.co_psi_inv
