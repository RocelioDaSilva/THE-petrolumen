import pytest
from app.reservoir.muskat_igd import MuskatPVT, muskat_igd


class TestExample91:
    """Example 9.1 (pp. 370-373): Muskat Np = 939,500 STB at 2300 psia.
    Tolerance 5% (finite-diff slope differs slightly from book's
    graphical slope)."""
    def _run(self):
        pvt = [
            MuskatPVT(2500.0, 1.498, 0.001048, 721.0, 0.488, 0.0170),
            MuskatPVT(2300.0, 1.463, 0.001155, 669.0, 0.539, 0.0166),
        ]
        rp = [(0.20, 1.0e9), (0.50, 1.0), (0.80, 0.005),
              (0.95, 3.0e-5), (0.99, 1.0e-6)]
        return muskat_igd(56e6, 0.20, pvt, rp)

    def test_Np(self):
        r = self._run()
        assert r.rows[0].Np_stb == pytest.approx(939_500.0, rel=0.05)


class TestValidation:
    def test_N_zero(self):
        with pytest.raises(ValueError, match="N_stb must be > 0"):
            muskat_igd(0.0, 0.20,
                       [MuskatPVT(2500.0, 1.5, 0.001, 700.0, 0.5, 0.017),
                        MuskatPVT(2300.0, 1.46, 0.0011, 670.0, 0.54, 0.017)],
                       [(0.20, 1.0), (0.50, 1.0), (0.90, 1e-4)])
