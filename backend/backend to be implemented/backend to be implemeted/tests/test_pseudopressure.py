"""Tests for pseudopressure (Craft Eq. 7.39)."""
import pytest
from app.reservoir.pseudopressure import pseudopressure


class TestAnalyticCheck:
    """If mu*z = const = C, then m(p) = 2(p^2 - pR^2)/(2*C) = (p^2 - pR^2)/C.
    Use mu=1, z=1 => C=1. p=1000, pR=14.7:
    m(p) = 1000^2 - 14.7^2 = 999,783.9."""
    def test_constant_mu_z(self):
        table = [(14.7, 1.0, 1.0), (500.0, 1.0, 1.0),
                 (2000.0, 1.0, 1.0)]
        r = pseudopressure(1000.0, table)
        expected = 1000.0**2 - 14.7**2
        assert r.m_p_psia2_cp == pytest.approx(expected, rel=1e-3)


class TestPositive:
    """m(p) is positive and monotone in p for physical (mu, z) tables."""
    def test_monotone(self):
        table = [
            (14.7, 0.011, 0.998), (500.0, 0.013, 0.940),
            (1000.0, 0.015, 0.900), (2000.0, 0.018, 0.870),
            (3000.0, 0.021, 0.900),
        ]
        m1 = pseudopressure(500.0, table).m_p_psia2_cp
        m2 = pseudopressure(2000.0, table).m_p_psia2_cp
        m3 = pseudopressure(3000.0, table).m_p_psia2_cp
        assert 0.0 < m1 < m2 < m3


class TestValidation:
    def test_p_zero(self):
        with pytest.raises(ValueError, match="p_psia must be > 0"):
            pseudopressure(0.0, [(14.7, 1.0, 1.0), (1000.0, 1.0, 1.0)])
    def test_mu_zero(self):
        with pytest.raises(ValueError, match="mu must be > 0"):
            pseudopressure(
                1000.0, [(14.7, 0.0, 1.0), (1000.0, 1.0, 1.0)],
            )
    def test_z_zero(self):
        with pytest.raises(ValueError, match="z must be > 0"):
            pseudopressure(
                1000.0, [(14.7, 1.0, 0.0), (1000.0, 1.0, 1.0)],
            )
    def test_table_not_sorted(self):
        with pytest.raises(ValueError, match="must be strictly increasing"):
            pseudopressure(
                1000.0, [(1000.0, 1.0, 1.0), (14.7, 1.0, 1.0)],
            )
    def test_n_grid_too_small(self):
        with pytest.raises(ValueError, match="n_grid must be"):
            pseudopressure(
                1000.0, [(14.7, 1.0, 1.0), (1000.0, 1.0, 1.0)],
                n_grid=5,
            )
