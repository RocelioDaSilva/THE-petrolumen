"""Tests for backend/app/reservoir/waterflood_efficiency.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 9, Sec. 2, pp. 335-347, Sec. 4.3, pp. 378-380,
Eq. (9.1); Eq. (5.4), p. 150.
"""

import pytest

from app.reservoir.waterflood_efficiency import (
    WaterfloodEfficiencyResult,
    waterflood_ed_from_saturations,
    waterflood_efficiency_from_components,
    waterflood_efficiency_from_saturations,
)


class TestFromComponents:
    """Ea=0.7, Ei=0.8, Ed=0.6 -> Ev=0.56, E=0.336."""

    def test_book_equation(self):
        r = waterflood_efficiency_from_components(
            E_a=0.7, E_i=0.8, E_d=0.6,
        )
        assert isinstance(r, WaterfloodEfficiencyResult)
        assert r.E_v == pytest.approx(0.56, rel=1e-12)
        assert r.E == pytest.approx(0.336, rel=1e-12)


class TestEdFromSaturations:
    """Ed = (1 - Swr - Sor)/(1 - Swr). Swr=0.3, Sor=0.25 -> 0.45/0.7."""

    def test_value(self):
        Ed = waterflood_ed_from_saturations(0.30, 0.25)
        assert Ed == pytest.approx(0.45 / 0.70, rel=1e-12)

    def test_no_residual(self):
        Ed = waterflood_ed_from_saturations(0.30, 0.0)
        assert Ed == pytest.approx(1.0, rel=1e-12)

    def test_all_residual(self):
        # Swr + Sor = 1 -> Ed = 0
        Ed = waterflood_ed_from_saturations(0.40, 0.60)
        assert Ed == pytest.approx(0.0, abs=1e-12)


class TestFromSaturations:
    """Ea=0.7, Ei=0.8, Swr=0.3, Sor=0.25 -> Ed=0.643, E=0.36."""

    def test_value(self):
        r = waterflood_efficiency_from_saturations(
            Swr=0.30, Sor=0.25, E_a=0.7, E_i=0.8,
        )
        assert r.E_d == pytest.approx(0.45 / 0.70, rel=1e-12)
        assert r.E == pytest.approx(0.7 * 0.8 * (0.45 / 0.70), rel=1e-12)


class TestValidation:
    def test_Ea_out_of_range(self):
        with pytest.raises(ValueError, match="E_a must be in \\[0, 1\\]"):
            waterflood_efficiency_from_components(1.2, 0.8, 0.6)

    def test_Ei_out_of_range(self):
        with pytest.raises(ValueError, match="E_i must be in \\[0, 1\\]"):
            waterflood_efficiency_from_components(0.7, -0.1, 0.6)

    def test_Ed_out_of_range(self):
        with pytest.raises(ValueError, match="E_d must be in \\[0, 1\\]"):
            waterflood_efficiency_from_components(0.7, 0.8, 1.5)

    def test_Swr_zero(self):
        with pytest.raises(ValueError, match="Swr must be in"):
            waterflood_ed_from_saturations(0.0, 0.25)

    def test_Swr_one(self):
        with pytest.raises(ValueError, match="Swr must be in"):
            waterflood_ed_from_saturations(1.0, 0.25)

    def test_Sor_negative(self):
        with pytest.raises(ValueError, match="Sor must be >= 0"):
            waterflood_ed_from_saturations(0.3, -0.05)

    def test_Swr_plus_Sor_ge_one(self):
        with pytest.raises(ValueError, match="must be < 1"):
            waterflood_ed_from_saturations(0.7, 0.4)


class TestDeterminism:
    def test_repeatable(self):
        a = waterflood_efficiency_from_components(0.7, 0.8, 0.6)
        b = waterflood_efficiency_from_components(0.7, 0.8, 0.6)
        assert a.E == b.E


class TestParametrizedEd:
    """Higher Sor -> lower Ed (more oil left behind)."""

    @pytest.mark.parametrize("sor_pair", [(0.20, 0.30), (0.30, 0.40)])
    def test_ed_decreases(self, sor_pair):
        s1, s2 = sor_pair
        e1 = waterflood_ed_from_saturations(0.25, s1)
        e2 = waterflood_ed_from_saturations(0.25, s2)
        assert e2 < e1
