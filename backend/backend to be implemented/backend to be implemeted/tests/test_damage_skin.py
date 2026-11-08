import pytest
from app.reservoir.damage_skin import damage_skin


class TestDamage:
    """k_e=100, k_a=10 (10x damage) out to r_a=10*r_w."""
    def test_S(self):
        r = damage_skin(100.0, 10.0, 10.0, 1.0)
        # S = (100/10 - 1) * ln(10) = 9 * 2.303 = 20.7
        assert r.S == pytest.approx(20.72, rel=0.01)
        assert r.kind == "damage"


class TestStimulation:
    def test_negative(self):
        r = damage_skin(100.0, 500.0, 10.0, 1.0)
        # S = (0.2 - 1)*ln(10) = -1.84
        assert r.S < 0.0
        assert r.kind == "stimulation"


class TestUndamaged:
    def test_zero(self):
        r = damage_skin(100.0, 100.0, 10.0, 1.0)
        assert r.S == pytest.approx(0.0, abs=1e-12)
        assert r.kind == "undamaged"


class TestValidation:
    def test_ra_le_rw(self):
        with pytest.raises(ValueError, match="r_a_ft"):
            damage_skin(100.0, 10.0, 1.0, 1.0)
