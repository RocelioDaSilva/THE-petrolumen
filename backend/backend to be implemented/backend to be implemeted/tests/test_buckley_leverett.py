"""Tests for backend/app/reservoir/buckley_leverett.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 9, Sec. 2.2 pp. 337-347, Sec. 3.1 pp. 347-354,
Eqs. (9.3), (9.6), (9.15), (9.17), Table 9.1 (p. 351).
"""

import math
import pytest

from app.reservoir.buckley_leverett import (
    BuckleyLeverettResult,
    buckley_leverett_advance,
    buckley_leverett_single,
)


class TestTable91:
    """Table 9.1 (p. 351) with mu_w/mu_o=0.50, a=540, b=11.5.
    Book: at Sw=0.40, ko/kw=5.50, fw=0.267, dfw/dSw=2.25.
    Tolerance: 2% on ko/kw and fw, 5% on dfw/dSw.
    """

    def test_at_040(self):
        r = buckley_leverett_single(
            Sw=0.40, mu_w=0.50, mu_o=1.00, a=540.0, b=11.5,
        )
        pt = r.points[0]
        assert pt.ko_over_kw == pytest.approx(5.50, rel=0.02)
        assert pt.fw == pytest.approx(0.267, abs=0.005)
        assert pt.dfw_dSw == pytest.approx(2.25, rel=0.05)

    def test_at_060(self):
        r = buckley_leverett_single(
            Sw=0.60, mu_w=0.50, mu_o=1.00, a=540.0, b=11.5,
        )
        pt = r.points[0]
        # Book: ko/kw=0.55, fw=0.784, dfw/dSw=1.95
        assert pt.ko_over_kw == pytest.approx(0.55, rel=0.02)
        assert pt.fw == pytest.approx(0.784, abs=0.005)
        assert pt.dfw_dSw == pytest.approx(1.95, rel=0.05)


class TestFrontalAdvanceBookExample:
    """pp. 349-355: q_i'=900 bbl/day, phi=0.25, Ac=26,400 ft^2,
    coefficient per day = 5.615*900/(0.25*26400) = 0.7657.
    Book at Sw=0.40, t=60d: x = 46*2.25 = 103.5 ft (book prints 104).
    Tolerance 2%.
    """

    def test_at_040_t60(self):
        r = buckley_leverett_advance(
            Sw_list=[0.40], mu_w=0.50, mu_o=1.00,
            a=540.0, b=11.5,
            qi_bbl_d=900.0, phi=0.25, Ac_ft2=26400.0,
            times_days=[60.0],
        )
        x = r.x_by_Sw_by_time[0][0]
        assert x == pytest.approx(103.5, rel=0.02)

    def test_at_040_t240(self):
        r = buckley_leverett_advance(
            Sw_list=[0.40], mu_w=0.50, mu_o=1.00,
            a=540.0, b=11.5,
            qi_bbl_d=900.0, phi=0.25, Ac_ft2=26400.0,
            times_days=[240.0],
        )
        x = r.x_by_Sw_by_time[0][0]
        assert x == pytest.approx(414.0, rel=0.02)


class TestMultipleSwMultipleTimes:
    def test_shape(self):
        r = buckley_leverett_advance(
            Sw_list=[0.30, 0.40, 0.50, 0.60],
            mu_w=0.50, mu_o=1.00, a=540.0, b=11.5,
            qi_bbl_d=900.0, phi=0.25, Ac_ft2=26400.0,
            times_days=[60.0, 120.0, 240.0],
        )
        assert isinstance(r, BuckleyLeverettResult)
        assert len(r.points) == 4
        assert len(r.x_by_Sw_by_time) == 4
        assert len(r.x_by_Sw_by_time[0]) == 3

    def test_x_scales_with_t(self):
        r = buckley_leverett_advance(
            Sw_list=[0.40], mu_w=0.50, mu_o=1.00,
            a=540.0, b=11.5,
            qi_bbl_d=900.0, phi=0.25, Ac_ft2=26400.0,
            times_days=[60.0, 120.0],
        )
        x60 = r.x_by_Sw_by_time[0][0]
        x120 = r.x_by_Sw_by_time[0][1]
        assert x120 == pytest.approx(2.0 * x60, rel=1e-9)


class TestDerivativePeaks:
    """dfw/dSw has a maximum somewhere in (0, 1); monotone either side."""

    def test_peak(self):
        Sws = [i / 100.0 for i in range(20, 81, 5)]
        r = buckley_leverett_advance(
            Sw_list=Sws, mu_w=0.50, mu_o=1.00, a=540.0, b=11.5,
            qi_bbl_d=900.0, phi=0.25, Ac_ft2=26400.0,
            times_days=[1.0],
        )
        dfws = [p.dfw_dSw for p in r.points]
        # Peak should be interior (not at endpoints)
        peak_idx = dfws.index(max(dfws))
        assert 0 < peak_idx < len(dfws) - 1


class TestValidation:
    def test_Sw_out_of_range(self):
        with pytest.raises(ValueError, match="Sw must be in"):
            buckley_leverett_single(1.2, 0.5, 1.0, 540.0, 11.5)

    def test_mu_w_zero(self):
        with pytest.raises(ValueError, match="mu_w must be > 0"):
            buckley_leverett_single(0.40, 0.0, 1.0, 540.0, 11.5)

    def test_mu_o_zero(self):
        with pytest.raises(ValueError, match="mu_o must be > 0"):
            buckley_leverett_single(0.40, 0.5, 0.0, 540.0, 11.5)

    def test_a_zero(self):
        with pytest.raises(ValueError, match="a must be > 0"):
            buckley_leverett_single(0.40, 0.5, 1.0, 0.0, 11.5)

    def test_b_zero(self):
        with pytest.raises(ValueError, match="b must be > 0"):
            buckley_leverett_single(0.40, 0.5, 1.0, 540.0, 0.0)

    def test_empty_Sw_list(self):
        with pytest.raises(ValueError, match="Sw_list must be non-empty"):
            buckley_leverett_advance(
                [], 0.5, 1.0, 540.0, 11.5, 900.0, 0.25, 26400.0, [60.0],
            )

    def test_empty_times(self):
        with pytest.raises(ValueError, match="times_days must be non-empty"):
            buckley_leverett_advance(
                [0.40], 0.5, 1.0, 540.0, 11.5, 900.0, 0.25, 26400.0, [],
            )

    def test_negative_time(self):
        with pytest.raises(ValueError, match="times_days\\[0\\]"):
            buckley_leverett_advance(
                [0.40], 0.5, 1.0, 540.0, 11.5, 900.0, 0.25, 26400.0, [-1.0],
            )

    def test_qi_zero(self):
        with pytest.raises(ValueError, match="qi_bbl_d must be > 0"):
            buckley_leverett_advance(
                [0.40], 0.5, 1.0, 540.0, 11.5, 0.0, 0.25, 26400.0, [60.0],
            )

    def test_phi_out(self):
        with pytest.raises(ValueError, match="phi must be in"):
            buckley_leverett_advance(
                [0.40], 0.5, 1.0, 540.0, 11.5, 900.0, 1.5, 26400.0, [60.0],
            )


class TestDeterminism:
    def test_repeatable(self):
        a = buckley_leverett_single(0.40, 0.5, 1.0, 540.0, 11.5)
        b = buckley_leverett_single(0.40, 0.5, 1.0, 540.0, 11.5)
        assert a.points[0].fw == b.points[0].fw
        assert a.points[0].dfw_dSw == b.points[0].dfw_dSw


class TestParametrizedMuRatio:
    """Higher mu_w/mu_o (more adverse) -> higher fw at same Sw."""

    @pytest.mark.parametrize("ratio_pair", [(0.25, 0.50), (0.50, 1.00)])
    def test_fw_increases(self, ratio_pair):
        r1, r2 = ratio_pair
        # mu_o fixed at 1.0 cp
        p1 = buckley_leverett_single(0.40, r1, 1.0, 540.0, 11.5).points[0]
        p2 = buckley_leverett_single(0.40, r2, 1.0, 540.0, 11.5).points[0]
        assert p2.fw > p1.fw
