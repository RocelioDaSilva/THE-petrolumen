"""Tests for anisotropy_weighted_permeability (Chin Ch 2 p. 46)."""
import pytest
from app.reservoir.anisotropy_weighted_perm import (
    anisotropy_weighted_permeability,
)


class TestBookExample84:
    """Example 8.4 (Chin): k=50, F_k=0.04, h=200. Single layer:
    kh_eff=50, kv_eff=50*0.04=2, kappa=0.04."""

    def test_single_layer(self):
        r = anisotropy_weighted_permeability([(50.0, 2.0, 200.0)])
        assert r.kh_eff_md == pytest.approx(50.0)
        assert r.kv_eff_md == pytest.approx(2.0)
        assert r.kappa == pytest.approx(0.04)


class TestTwoLayers:
    """Two equal-thickness layers: kh1=100, kv1=10; kh2=200, kv2=20.
    kh_eff = (100+200)/2 = 150; kv_eff = 2/(1/10 + 1/20) = 13.33;
    kappa = 13.33/150 = 0.0889."""

    def test_values(self):
        r = anisotropy_weighted_permeability(
            [(100.0, 10.0, 10.0), (200.0, 20.0, 10.0)]
        )
        assert r.kh_eff_md == pytest.approx(150.0, rel=1e-9)
        assert r.kv_eff_md == pytest.approx(200.0/15.0, rel=1e-9)
        assert r.kappa == pytest.approx((200.0/15.0)/150.0, rel=1e-9)


class TestIsotropic:
    """All layers isotropic with same k: kh_eff = kv_eff = k; kappa = 1."""

    def test_kappa_one(self):
        r = anisotropy_weighted_permeability(
            [(100.0, 100.0, 10.0), (100.0, 100.0, 20.0)]
        )
        assert r.kh_eff_md == pytest.approx(100.0)
        assert r.kv_eff_md == pytest.approx(100.0)
        assert r.kappa == pytest.approx(1.0)


class TestValidation:
    def test_empty(self):
        with pytest.raises(ValueError, match="non-empty"):
            anisotropy_weighted_permeability([])

    def test_kh_zero(self):
        with pytest.raises(ValueError, match="kh_md must be > 0"):
            anisotropy_weighted_permeability([(0.0, 10.0, 10.0)])

    def test_kv_zero(self):
        with pytest.raises(ValueError, match="kv_md must be > 0"):
            anisotropy_weighted_permeability([(100.0, 0.0, 10.0)])

    def test_h_zero(self):
        with pytest.raises(ValueError, match="h_ft must be > 0"):
            anisotropy_weighted_permeability([(100.0, 10.0, 0.0)])


class TestDeterminism:
    def test_repeatable(self):
        a = anisotropy_weighted_permeability(
            [(100.0, 10.0, 10.0), (200.0, 20.0, 10.0)]
        )
        b = anisotropy_weighted_permeability(
            [(100.0, 10.0, 10.0), (200.0, 20.0, 10.0)]
        )
        assert a.kh_eff_md == b.kh_eff_md
        assert a.kv_eff_md == b.kv_eff_md


class TestThicknessWeighting:
    """Thicker high-kh layer dominates arithmetic mean; thicker
    low-kv layer dominates harmonic mean."""

    def test_kh_dominated_by_thick_layer(self):
        r = anisotropy_weighted_permeability(
            [(100.0, 10.0, 90.0), (1000.0, 10.0, 10.0)]
        )
        # kh_eff = (100*90 + 1000*10)/100 = 190
        assert r.kh_eff_md == pytest.approx(190.0, rel=1e-9)

    def test_kv_dominated_by_thin_layer(self):
        r = anisotropy_weighted_permeability(
            [(100.0, 10.0, 10.0), (100.0, 1.0, 90.0)]
        )
        # kv_eff = 100 / (10/10 + 90/1) = 100/91 = 1.099
        assert r.kv_eff_md == pytest.approx(100.0/91.0, rel=1e-9)
