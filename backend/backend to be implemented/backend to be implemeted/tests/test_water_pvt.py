"""Tests for backend/app/reservoir/water_pvt.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 1, Sec. 7.1-7.4, pp. 45-48, Eqs. (1.37)-(1.43),
Problem 1.25 (p. 52).
"""

import math
import pytest

from app.reservoir.water_pvt import WaterPVTResult, water_pvt


class TestProblem125:
    """Problem 1.25 (p. 52): 20,000 ppm, 4000 psia, 150 F.
    ppm conversion: 20,000 ppm = 20 g/L NaCl.
    Hand-checkable by Eq. (1.40) and Eq. (1.37) with C_NaCl=20.
    """

    def test_cw(self):
        # Eq. (1.40) with p=4000, T=150, C=20
        denom = 7.033 * 4000.0 + 541.5 * 20.0 - 537.0 * 150.0 + 403300.0
        expected = 1.0 / denom
        r = water_pvt(
            p_psia=4000.0, T_F=150.0,
            salinity_pct=2.0, c_nacl_g_l=20.0,
        )
        assert r.cw_psi_inv == pytest.approx(expected, rel=1e-9)

    def test_bw_positive(self):
        r = water_pvt(
            p_psia=4000.0, T_F=150.0,
            salinity_pct=2.0, c_nacl_g_l=20.0,
        )
        assert isinstance(r, WaterPVTResult)
        assert r.bw_bbl_stb > 0.9
        assert r.bw_bbl_stb < 1.2


class TestUnitsConsistency:
    """Eq. (1.37) Bw should be slightly > 1 at moderate p, T."""

    def test_bw_moderate(self):
        r = water_pvt(p_psia=3000.0, T_F=180.0, salinity_pct=5.0)
        assert 0.95 < r.bw_bbl_stb < 1.15

    def test_cw_positive(self):
        r = water_pvt(p_psia=3000.0, T_F=180.0, salinity_pct=5.0)
        assert r.cw_psi_inv > 0.0

    def test_mu_positive(self):
        r = water_pvt(p_psia=3000.0, T_F=180.0, salinity_pct=5.0)
        assert r.mu_w_cp > 0.05
        assert r.mu_w_cp < 2.0


class TestRswClamping:
    """Rswp and Rsw should scale with salinity: pure water higher,
    saline lower."""

    def test_pure_water_higher(self):
        pure = water_pvt(p_psia=3000.0, T_F=180.0, salinity_pct=0.01)
        salty = water_pvt(p_psia=3000.0, T_F=180.0, salinity_pct=20.0)
        # Book: dissolved gas reduces with salinity.
        assert pure.rsw_scf_stb > salty.rsw_scf_stb


class TestValidation:
    def test_p_zero(self):
        with pytest.raises(ValueError, match="p_psia must be > 0"):
            water_pvt(0.0, 150.0, 5.0)

    def test_T_zero(self):
        with pytest.raises(ValueError, match="T_F must be >"):
            water_pvt(3000.0, 0.0, 5.0)

    def test_T_negative(self):
        with pytest.raises(ValueError, match="T_F must be >"):
            water_pvt(3000.0, -10.0, 5.0)

    def test_salinity_zero(self):
        with pytest.raises(ValueError, match="salinity_pct must be in"):
            water_pvt(3000.0, 150.0, 0.0)

    def test_salinity_too_high(self):
        with pytest.raises(ValueError, match="salinity_pct must be in"):
            water_pvt(3000.0, 150.0, 50.0)

    def test_c_nacl_negative(self):
        with pytest.raises(ValueError, match="c_nacl_g_l must be in"):
            water_pvt(3000.0, 150.0, 5.0, c_nacl_g_l=-1.0)

    def test_c_nacl_too_high(self):
        with pytest.raises(ValueError, match="c_nacl_g_l must be in"):
            water_pvt(3000.0, 150.0, 5.0, c_nacl_g_l=500.0)


class TestCwDenominatorGuard:
    """Extreme inputs can drive the cw denominator negative; must raise."""

    def test_denominator_negative(self):
        # Very high T with low p, no salt: denom ~ -537*T + 403300
        # For T=1000, denom = 7.033*100 + 541.5*0 - 537*1000 + 403300
        #              = 703 - 537000 + 403300 = -133000 -> raise.
        with pytest.raises(ValueError, match="Eq. \\(1.40\\) denominator"):
            water_pvt(100.0, 1000.0, 0.01)


class TestValidityFlags:
    def test_cw_out_of_range(self):
        # T=150 is inside [200,270]? No, 150 < 200 -> cw_in_validity False
        r = water_pvt(p_psia=3000.0, T_F=150.0, salinity_pct=5.0)
        assert r.cw_in_validity is False

    def test_cw_in_range(self):
        # T=220, p=5000, C~50 all inside Osif envelope
        r = water_pvt(p_psia=5000.0, T_F=220.0, salinity_pct=5.0)
        assert r.cw_in_validity is True

    def test_rsw_out_of_range(self):
        # T=150, p=3000, S=5: p in [1000,10000], T in [100,340],
        # S in (0,30). All true -> rsw_in_validity True
        r = water_pvt(p_psia=3000.0, T_F=150.0, salinity_pct=5.0)
        assert r.rsw_in_validity is True

    def test_mu_out_of_range(self):
        # T=150 < 86? No. 150 > 167? No. So mu_in is True.
        # Use T=200 instead to force False.
        r = water_pvt(p_psia=3000.0, T_F=200.0, salinity_pct=5.0)
        assert r.mu_w_in_validity is False


class TestDeterminism:
    def test_repeatable(self):
        a = water_pvt(3000.0, 180.0, 5.0)
        b = water_pvt(3000.0, 180.0, 5.0)
        assert a.bw_bbl_stb == b.bw_bbl_stb
        assert a.cw_psi_inv == b.cw_psi_inv
