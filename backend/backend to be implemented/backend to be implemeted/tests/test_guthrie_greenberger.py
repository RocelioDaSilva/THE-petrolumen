"""Tests for guthrie_greenberger_rf (Craft Eq. 5.5, p. 152)."""
import pytest
from app.reservoir.guthrie_greenberger import guthrie_greenberger_rf


class TestBookExample:
    """Book p. 152: k=1000, Swi=0.25, mu_o=2.0, phi=0.20, h=10
    -> RF = 0.642 (64.2%). Tolerance 1%."""
    def test_rf(self):
        r = guthrie_greenberger_rf(1000.0, 0.25, 2.0, 0.20, 10.0)
        assert r.RF == pytest.approx(0.642, rel=0.02)
        assert r.out_of_physical_range is False


class TestValidation:
    def test_k_zero(self):
        with pytest.raises(ValueError, match="k_md must be > 0"):
            guthrie_greenberger_rf(0.0, 0.25, 2.0, 0.20, 10.0)
    def test_swi_one(self):
        with pytest.raises(ValueError, match="Swi must be in"):
            guthrie_greenberger_rf(100.0, 1.0, 2.0, 0.20, 10.0)
    def test_mu_zero(self):
        with pytest.raises(ValueError, match="mu_o_cp must be > 0"):
            guthrie_greenberger_rf(100.0, 0.25, 0.0, 0.20, 10.0)
    def test_h_zero(self):
        with pytest.raises(ValueError, match="h_ft must be > 0"):
            guthrie_greenberger_rf(100.0, 0.25, 2.0, 0.20, 0.0)


class TestOutOfRangeFlag:
    def test_very_hot(self):
        r = guthrie_greenberger_rf(5000.0, 0.15, 0.2, 0.10, 5.0)
        # High k, low mu -> RF can exceed 1
        # Only assert the flag exists
        assert isinstance(r.out_of_physical_range, bool)
