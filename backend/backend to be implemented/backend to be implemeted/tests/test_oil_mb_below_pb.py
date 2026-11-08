"""Tests for backend/app/reservoir/oil_mb_below_pb.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 5, Sec. 3, pp. 153-157, Eqs. (5.6)-(5.11);
Sec. 6, p. 173, Eq. (5.29); Example 5.1 (pp. 156-157).
"""

import pytest

from app.reservoir.oil_mb_below_pb import (
    OilMBBelowPbResult,
    oil_mb_below_pb_general,
    oil_mb_below_pb_volumetric,
)


class TestExample51:
    """Example 5.1 (pp. 156-157): 3-A-2 reservoir at 2800 psia.
    Np=1.486 MM STB, Rp=3300, Rsoi=1100, Bt=1.724, Bti=1.572, Bg=0.00102.
    Book: N=38.8 MM STB, RF=3.83%. Tolerance 1% (N), 0.005 (RF).
    """

    def test_n(self):
        r = oil_mb_below_pb_volumetric(
            Np_stb=1.486e6, Rp=3300.0, Rsoi=1100.0,
            Bt=1.724, Bti=1.572, Bg=0.00102,
        )
        assert isinstance(r, OilMBBelowPbResult)
        assert r.n_stb / 1.0e6 == pytest.approx(38.8, rel=0.01)

    def test_rf(self):
        r = oil_mb_below_pb_volumetric(
            Np_stb=1.486e6, Rp=3300.0, Rsoi=1100.0,
            Bt=1.724, Bti=1.572, Bg=0.00102,
        )
        assert r.rf_fraction == pytest.approx(0.0383, abs=0.005)


class TestExample51AllReturned:
    """If two-thirds of produced gas is returned (Rp=1100), RF=8.8%.
    Book p. 157.
    """

    def test_rf(self):
        r = oil_mb_below_pb_volumetric(
            Np_stb=1.486e6, Rp=1100.0, Rsoi=1100.0,
            Bt=1.724, Bti=1.572, Bg=0.00102,
        )
        assert r.rf_fraction == pytest.approx(0.0882, rel=0.02)


class TestGeneralReducesToVolumetric:
    """With cw=cf=0, We=0, Wp=0, Bw=1, Eq. 5.29 should match Eq. 5.10."""

    def test_identical(self):
        r_vol = oil_mb_below_pb_volumetric(
            Np_stb=1.486e6, Rp=3300.0, Rsoi=1100.0,
            Bt=1.724, Bti=1.572, Bg=0.00102,
        )
        r_gen = oil_mb_below_pb_general(
            Np_stb=1.486e6, Rp=3300.0, Rsoi=1100.0,
            Bt=1.724, Bti=1.572, Bg=0.00102,
            Swi=0.20, cw=0.0, cf=0.0, delta_p=0.0,
            We=0.0, Wp=0.0, Bw=1.0,
        )
        assert r_gen.n_stb == pytest.approx(r_vol.n_stb, rel=1e-12)


class TestGeneralWithComp:
    """Adding compressibilities slightly lowers N (denominator grows)."""

    def test_comp_lowers_n(self):
        r1 = oil_mb_below_pb_general(
            1.486e6, 3300.0, 1100.0, 1.724, 1.572, 0.00102,
            Swi=0.20, cw=0.0, cf=0.0, delta_p=1400.0,
        )
        r2 = oil_mb_below_pb_general(
            1.486e6, 3300.0, 1100.0, 1.724, 1.572, 0.00102,
            Swi=0.20, cw=3.6e-6, cf=5.0e-6, delta_p=1400.0,
        )
        assert r2.n_stb < r1.n_stb


class TestValidation:
    def _ok(self) -> dict:
        return dict(
            Np_stb=1.486e6, Rp=3300.0, Rsoi=1100.0,
            Bt=1.724, Bti=1.572, Bg=0.00102,
        )

    def test_Np_negative(self):
        kw = self._ok(); kw["Np_stb"] = -1.0
        with pytest.raises(ValueError, match="Np_stb must be >= 0"):
            oil_mb_below_pb_volumetric(**kw)

    def test_Rp_negative(self):
        kw = self._ok(); kw["Rp"] = -1.0
        with pytest.raises(ValueError, match="Rp must be >= 0"):
            oil_mb_below_pb_volumetric(**kw)

    def test_Bt_less_than_Bti(self):
        kw = self._ok(); kw["Bt"] = 1.50
        with pytest.raises(ValueError, match="oil FVF cannot shrink"):
            oil_mb_below_pb_volumetric(**kw)

    def test_Bg_zero(self):
        kw = self._ok(); kw["Bg"] = 0.0
        with pytest.raises(ValueError, match="Bg must be > 0"):
            oil_mb_below_pb_volumetric(**kw)

    def test_Swi_one_general(self):
        with pytest.raises(ValueError, match="Swi must be in"):
            oil_mb_below_pb_general(
                1.486e6, 3300.0, 1100.0, 1.724, 1.572, 0.00102,
                Swi=1.0, cw=3.6e-6, cf=5.0e-6, delta_p=1400.0,
            )

    def test_We_negative_general(self):
        with pytest.raises(ValueError, match="We must be >= 0"):
            oil_mb_below_pb_general(
                1.486e6, 3300.0, 1100.0, 1.724, 1.572, 0.00102,
                Swi=0.20, cw=0.0, cf=0.0, delta_p=0.0, We=-1.0,
            )


class TestDegenerate:
    def test_tp_zero(self):
        # Bt + (Rp-Rsoi)*Bg = 0 by construction
        # e.g. Bt=0.5, Rp-Rsoi=-500, Bg=0.001 -> 0.5-0.5=0
        with pytest.raises(ValueError, match="tp"):
            oil_mb_below_pb_volumetric(
                Np_stb=1.0e6, Rp=600.0, Rsoi=1100.0,
                Bt=0.5, Bti=0.4, Bg=0.001,
            )


class TestDeterminism:
    def test_repeatable(self):
        a = oil_mb_below_pb_volumetric(
            1.486e6, 3300.0, 1100.0, 1.724, 1.572, 0.00102,
        )
        b = oil_mb_below_pb_volumetric(
            1.486e6, 3300.0, 1100.0, 1.724, 1.572, 0.00102,
        )
        assert a.n_stb == b.n_stb


class TestParametrizedRp:
    """Higher Rp produces higher RF."""

    @pytest.mark.parametrize(
        "rp_pair", [(1100.0, 2200.0), (2200.0, 3300.0)]
    )
    def test_rf_increases_with_rp(self, rp_pair):
        rp1, rp2 = rp_pair
        r1 = oil_mb_below_pb_volumetric(
            1.486e6, rp1, 1100.0, 1.724, 1.572, 0.00102,
        )
        r2 = oil_mb_below_pb_volumetric(
            1.486e6, rp2, 1100.0, 1.724, 1.572, 0.00102,
        )
        assert r2.rf_fraction > r1.rf_fraction
