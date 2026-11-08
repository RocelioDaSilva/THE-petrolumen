import pytest
from app.reservoir.kelly_snyder import KSPoint, kelly_snyder


class TestKellySnyderRange:
    """Book pp. 159-161: Pb=1725, Sg first hits ~0.10 at ~1400 psig."""
    def _pvt(self):
        return [
            KSPoint(1725.0, 1.4509, 1.4509, 0.00151, 885.0),
            KSPoint(1600.0, 1.4303, 1.4952, 0.00159, 842.0),
            KSPoint(1400.0, 1.3978, 1.5944, 0.00184, 772.0),
        ]

    def test_runs(self):
        r = kelly_snyder(2.25e9, 0.20, 0.10, self._pvt())
        assert len(r.rows) >= 1
        assert r.rows[0].Np_stb > 0.0

    def test_Np_increases(self):
        r = kelly_snyder(2.25e9, 0.20, 0.10, self._pvt())
        for i in range(1, len(r.rows)):
            assert r.rows[i].Np_stb >= r.rows[i-1].Np_stb


class TestValidation:
    def test_Np_zero(self):
        with pytest.raises(ValueError, match="N_stb must be > 0"):
            kelly_snyder(0.0, 0.20, 0.10,
                         [KSPoint(2000.0, 1.4, 1.4, 0.001, 800.0),
                          KSPoint(1900.0, 1.39, 1.42, 0.0011, 780.0)])
    def test_nonincreasing_p(self):
        pts = [KSPoint(1900.0, 1.4, 1.4, 0.001, 800.0),
               KSPoint(2000.0, 1.39, 1.42, 0.0011, 780.0)]
        with pytest.raises(ValueError, match="strictly decrease"):
            kelly_snyder(1e8, 0.20, 0.10, pts)
