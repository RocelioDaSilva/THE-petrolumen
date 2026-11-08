"""Tests for craze_buckley_sor (Craft Table 5.2, p. 151)."""
import pytest
from app.reservoir.craze_buckley_sor import craze_buckley_sor


class TestBookExample:
    """Book p. 151: mu_o=2.0 cp, k=500 md -> Sor = 39% (0.39)."""
    def test_sor(self):
        r = craze_buckley_sor(2.0, 500.0)
        assert r.Sor_pct == pytest.approx(39.0, abs=0.5)
        assert r.Sor == pytest.approx(0.39, abs=0.005)


class TestTablePoints:
    """Exact reproduction at tabulated points."""
    @pytest.mark.parametrize("mu,sor_pct",
        [(0.2, 30.0), (1.0, 34.5), (2.0, 37.0), (10.0, 43.5)])
    def test_base(self, mu, sor_pct):
        # Use k such that adj ~ 0 (k=1000 => adj=-1)
        r = craze_buckley_sor(mu, 1000.0)
        assert r.base_pct == pytest.approx(sor_pct, abs=0.01)


class TestValidation:
    def test_mu_zero(self):
        with pytest.raises(ValueError, match="mu_o_cp must be > 0"):
            craze_buckley_sor(0.0, 100.0)
    def test_k_zero(self):
        with pytest.raises(ValueError, match="k_md must be > 0"):
            craze_buckley_sor(2.0, 0.0)


class TestMonotonic:
    """Higher mu_o -> higher Sor; higher k -> lower Sor."""
    def test_mu_increases_sor(self):
        a = craze_buckley_sor(1.0, 500.0)
        b = craze_buckley_sor(5.0, 500.0)
        assert b.Sor_pct > a.Sor_pct
    def test_k_decreases_sor(self):
        a = craze_buckley_sor(2.0, 100.0)
        b = craze_buckley_sor(2.0, 2000.0)
        assert b.Sor_pct < a.Sor_pct
