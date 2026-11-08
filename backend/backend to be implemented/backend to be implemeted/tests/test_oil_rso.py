"""Tests for backend/app/reservoir/oil_rso.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 1, Sec. 6.1, pp. 32-34, Eq. (1.26) and Ex. 1.7.
"""

import pytest

from app.reservoir.oil_rso import RsoResult, oil_rso


class TestExample17:
    """Book Example 1.7 (p. 42): T=180 F, pb=2500 psia, gas_sg=0.80,
    API=40. Book answers (to nearest SCF/STB): 772 at pb, 590 at 2000 psia.
    Tolerance: 2 SCF/STB absolute (book rounds to integer).
    """

    def test_at_pb(self):
        r = oil_rso(
            p_psia=2500.0, T_F=180.0, gas_sg=0.80,
            oil_api=40.0, pb_psia=2500.0,
        )
        assert isinstance(r, RsoResult)
        assert r.rso_scf_stb == pytest.approx(772.0, abs=2.0)
        assert r.clamped is False
        assert r.in_validity_range is True

    def test_above_pb_clamps(self):
        r = oil_rso(
            p_psia=4000.0, T_F=180.0, gas_sg=0.80,
            oil_api=40.0, pb_psia=2500.0,
        )
        # Book: above pb, Rso = Rsob = 772
        assert r.rso_scf_stb == pytest.approx(772.0, abs=2.0)
        assert r.clamped is True

    def test_below_pb(self):
        r = oil_rso(
            p_psia=2000.0, T_F=180.0, gas_sg=0.80,
            oil_api=40.0, pb_psia=2500.0,
        )
        # Book: Rso at 2000 psia = 590 SCF/STB
        assert r.rso_scf_stb == pytest.approx(590.0, abs=2.0)
        assert r.clamped is False


class TestYgIntermediate:
    """Yg = 0.00091*T - 0.0125*API. At T=180, API=40 -> -0.336."""

    def test_yg_value(self):
        r = oil_rso(
            p_psia=2000.0, T_F=180.0, gas_sg=0.80,
            oil_api=40.0, pb_psia=2500.0,
        )
        assert r.y_g == pytest.approx(-0.336, abs=1e-6)


class TestMonotonicity:
    """Rso(p) is monotonically increasing for p < pb."""

    @pytest.mark.parametrize(
        "p1,p2",
        [(500.0, 1000.0), (1000.0, 1500.0), (1500.0, 2000.0)],
    )
    def test_increasing(self, p1, p2):
        a = oil_rso(p1, 180.0, 0.80, 40.0, 2500.0)
        b = oil_rso(p2, 180.0, 0.80, 40.0, 2500.0)
        assert b.rso_scf_stb > a.rso_scf_stb


class TestValidation:
    def test_p_zero(self):
        with pytest.raises(ValueError, match="p_psia must be > 0"):
            oil_rso(0.0, 180.0, 0.80, 40.0, 2500.0)

    def test_p_negative(self):
        with pytest.raises(ValueError, match="p_psia must be > 0"):
            oil_rso(-1.0, 180.0, 0.80, 40.0, 2500.0)

    def test_pb_zero(self):
        with pytest.raises(ValueError, match="pb_psia must be > 0"):
            oil_rso(1000.0, 180.0, 0.80, 40.0, 0.0)

    def test_T_below_abs(self):
        with pytest.raises(ValueError, match="T_F must be above"):
            oil_rso(1000.0, -500.0, 0.80, 40.0, 2500.0)

    def test_gas_sg_zero(self):
        with pytest.raises(ValueError, match="gas_sg must be in"):
            oil_rso(1000.0, 180.0, 0.0, 40.0, 2500.0)

    def test_gas_sg_too_high(self):
        with pytest.raises(ValueError, match="gas_sg must be in"):
            oil_rso(1000.0, 180.0, 2.5, 40.0, 2500.0)

    def test_api_too_low(self):
        with pytest.raises(ValueError, match="oil_api must be in"):
            oil_rso(1000.0, 180.0, 0.80, -15.0, 2500.0)

    def test_api_too_high(self):
        with pytest.raises(ValueError, match="oil_api must be in"):
            oil_rso(1000.0, 180.0, 0.80, 120.0, 2500.0)


class TestValidityFlag:
    def test_in_range(self):
        r = oil_rso(2000.0, 180.0, 0.80, 40.0, 2500.0)
        assert r.in_validity_range is True

    def test_pb_below_range(self):
        # pb=100 psia < 130 (book minimum)
        r = oil_rso(80.0, 180.0, 0.80, 40.0, 100.0)
        assert r.in_validity_range is False

    def test_API_out_of_range(self):
        # API=10 < 16.5 (book minimum) but physically valid
        r = oil_rso(2000.0, 180.0, 0.80, 10.0, 2500.0)
        assert r.in_validity_range is False


class TestDeterminism:
    def test_repeatable(self):
        a = oil_rso(2000.0, 180.0, 0.80, 40.0, 2500.0)
        b = oil_rso(2000.0, 180.0, 0.80, 40.0, 2500.0)
        assert a.rso_scf_stb == b.rso_scf_stb
