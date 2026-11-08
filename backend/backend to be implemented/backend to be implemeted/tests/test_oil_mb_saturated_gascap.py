"""Tests for backend/app/reservoir/oil_mb_saturated_gascap.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 6, Sec. 2, pp. 186-191, Example 6.1.
"""

import pytest

from app.reservoir.oil_mb_saturated_gascap import (
    SaturatedOilMBResult,
    oil_mb_saturated_gascap,
)


class TestExample61:
    """Example 6.1 (p. 187). Book answer: N = 98.97 MM STB.
    Tolerance 1% (book's internal rounding of 5.615 conversion).
    """

    def _run(self) -> SaturatedOilMBResult:
        return oil_mb_saturated_gascap(
            Np_stb=20e6, Rp=700.0,
            Bt=1.4954, Bti=1.3400,
            Bg=0.001510, Bgi=0.001110,
            Rsoi=562.0, m=0.175,
            We=11.58e6, Wp=1.05e6, Bw=1.028,
        )

    def test_n(self):
        r = self._run()
        assert isinstance(r, SaturatedOilMBResult)
        assert r.n_stb / 1.0e6 == pytest.approx(98.97, rel=0.01)

    def test_denominator(self):
        r = self._run()
        # Bt-Bti=0.1554, gas=0.0845, comp=0 -> denom ~ 0.2399
        assert r.denom_bbl_stb == pytest.approx(0.2399, rel=0.01)

    def test_no_compression_term(self):
        r = self._run()
        assert r.expansion_comp == 0.0


class TestVolumetricDepletionCase:
    """m=0, We=0, Wp=0 reduces to undersaturated saturated-oil MB."""

    def test_reduces(self):
        r = oil_mb_saturated_gascap(
            Np_stb=1.0e6, Rp=600.0, Bt=1.28, Bti=1.25,
            Bg=0.0015, Rsoi=600.0, m=0.0,
        )
        # exp_oil = 0.03, rhs_hc = 1e6 * 1.28 = 1.28e6
        # N = 1.28e6 / 0.03 = 42.67e6
        assert r.n_stb == pytest.approx(1.28e6 / 0.03, rel=1e-9)
        assert r.expansion_gas == 0.0


class TestGasCapOnly:
    """We=0, Wp=0, comp=0, m>0."""

    def test_gas_term_positive(self):
        r = oil_mb_saturated_gascap(
            Np_stb=5.0e6, Rp=700.0, Bt=1.40, Bti=1.30,
            Bg=0.0020, Bgi=0.0012, Rsoi=600.0, m=0.20,
        )
        # gas term: 0.20*1.30/0.0012 * (0.0020-0.0012) = 0.1733
        assert r.expansion_gas == pytest.approx(0.1733, rel=0.01)


class TestWaterDriveOnly:
    """m=0, Wp=0, We>0, comp=0."""

    def test_water_only(self):
        r = oil_mb_saturated_gascap(
            Np_stb=2.0e6, Rp=600.0, Bt=1.26, Bti=1.25,
            Bg=0.0015, Rsoi=600.0, m=0.0, We=1.0e6,
        )
        assert r.net_water_bbl == pytest.approx(1.0e6, rel=1e-9)


class TestValidation:
    def _ok(self) -> dict:
        return dict(
            Np_stb=20e6, Rp=700.0, Bt=1.4954, Bti=1.3400,
            Bg=0.001510, Bgi=0.001110, Rsoi=562.0, m=0.175,
            We=11.58e6, Wp=1.05e6, Bw=1.028,
        )

    def test_Np_negative(self):
        kw = self._ok(); kw["Np_stb"] = -1.0
        with pytest.raises(ValueError, match="Np_stb must be >= 0"):
            oil_mb_saturated_gascap(**kw)

    def test_Bt_zero(self):
        kw = self._ok(); kw["Bt"] = 0.0
        with pytest.raises(ValueError, match="Bt must be > 0"):
            oil_mb_saturated_gascap(**kw)

    def test_m_positive_without_Bgi(self):
        with pytest.raises(ValueError, match="Bgi is required"):
            oil_mb_saturated_gascap(
                Np_stb=1.0e6, Rp=600.0, Bt=1.30, Bti=1.25,
                Bg=0.0015, Rsoi=600.0, m=0.10,
            )

    def test_We_negative(self):
        kw = self._ok(); kw["We"] = -1.0
        with pytest.raises(ValueError, match="We must be >= 0"):
            oil_mb_saturated_gascap(**kw)

    def test_Swi_out_of_range(self):
        kw = self._ok(); kw["Swi"] = 1.5
        with pytest.raises(ValueError, match="Swi must be in"):
            oil_mb_saturated_gascap(**kw)


class TestCompressionContribution:
    """With Swi, cw, cf, delta_p provided, exp_comp is positive."""

    def test_comp_added(self):
        r = oil_mb_saturated_gascap(
            Np_stb=20e6, Rp=700.0, Bt=1.4954, Bti=1.3400,
            Bg=0.001510, Bgi=0.001110, Rsoi=562.0, m=0.175,
            We=11.58e6, Wp=1.05e6, Bw=1.028,
            Swi=0.25, cw=3e-6, cf=5e-6, delta_p=710.0,
        )
        assert r.expansion_comp > 0.0
        # Adding compression increases denominator -> lowers N
        r_no_comp = oil_mb_saturated_gascap(
            Np_stb=20e6, Rp=700.0, Bt=1.4954, Bti=1.3400,
            Bg=0.001510, Bgi=0.001110, Rsoi=562.0, m=0.175,
            We=11.58e6, Wp=1.05e6, Bw=1.028,
        )
        assert r.n_stb < r_no_comp.n_stb


class TestDegenerate:
    def test_denominator_zero(self):
        with pytest.raises(ValueError, match="denominator"):
            oil_mb_saturated_gascap(
                Np_stb=1.0e6, Rp=600.0, Bt=1.25, Bti=1.25,
                Bg=0.0015, Rsoi=600.0,
            )


class TestDeterminism:
    def test_repeatable(self):
        a = oil_mb_saturated_gascap(
            20e6, 700.0, 1.4954, 1.3400, 0.001510, 562.0,
            m=0.175, Bgi=0.001110, We=11.58e6, Wp=1.05e6, Bw=1.028,
        )
        b = oil_mb_saturated_gascap(
            20e6, 700.0, 1.4954, 1.3400, 0.001510, 562.0,
            m=0.175, Bgi=0.001110, We=11.58e6, Wp=1.05e6, Bw=1.028,
        )
        assert a.n_stb == b.n_stb


class TestParametrizedM:
    """Increasing m increases expansion_gas."""

    @pytest.mark.parametrize("m_pair", [(0.1, 0.3), (0.3, 0.5)])
    def test_gas_increases(self, m_pair):
        m1, m2 = m_pair
        r1 = oil_mb_saturated_gascap(
            Np_stb=5e6, Rp=700.0, Bt=1.40, Bti=1.30, Bg=0.0020,
            Rsoi=600.0, m=m1, Bgi=0.0012,
        )
        r2 = oil_mb_saturated_gascap(
            Np_stb=5e6, Rp=700.0, Bt=1.40, Bti=1.30, Bg=0.0020,
            Rsoi=600.0, m=m2, Bgi=0.0012,
        )
        assert r2.expansion_gas > r1.expansion_gas
