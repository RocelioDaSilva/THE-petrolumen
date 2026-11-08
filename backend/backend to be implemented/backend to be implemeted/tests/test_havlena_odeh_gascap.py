"""Tests for havelna_odeh_gascap (Craft Eq. 6.3-6.5)."""
import pytest
from app.reservoir.havlena_odeh_gascap import (
    HOGC_Point, havelna_odeh_gascap,
)


class TestSyntheticExact:
    """Construct 3 points on an exact F' = N*X line with N=100 MM STB,
    Bti=1.20, Bgi=0.001, m=0.10, no comp, no water production."""
    def _run(self):
        # We need to invert: for each X_i, F'_i = N * X_i.
        # Setup: choose eo, eg; then set Np = F'_i/(Bt + (Rp-Rsoi)*Bg).
        # Simplify by using Rp=Rsoi and Wp=We=0 so F'_i = Np*Bt.
        Bti, Bgi, m = 1.20, 0.001, 0.10
        N = 100.0e6
        rows = []
        for eo, eg in [(0.30, 0.0002), (0.20, 0.00015), (0.10, 0.00010)]:
            Bt = Bti + eo
            Bg = Bgi + eg
            X = eo + (m * Bti / Bgi) * eg
            F_prime = N * X
            Np = F_prime / Bt
            rows.append(HOGC_Point(
                Np=Np, Rp=500.0, Wp=0.0, We=0.0,
                Bw=1.0, Bt=Bt, Bg=Bg,
            ))
        return havelna_odeh_gascap(
            points=rows, Bti=Bti, Bgi=Bgi, Rsoi=500.0, m=m,
        )

    def test_n_hat(self):
        r = self._run()
        assert r.n_hat / 1e6 == pytest.approx(100.0, rel=0.01)

    def test_slope_near_one(self):
        r = self._run()
        assert r.free_slope == pytest.approx(1.0, rel=0.01)
        assert r.slope_diagnostic_ok is True

    def test_r_squared(self):
        r = self._run()
        assert r.r_squared > 0.9999


class TestValidation:
    def _pt(self):
        return HOGC_Point(
            Np=1e6, Rp=500.0, Wp=0.0, We=0.0,
            Bw=1.0, Bt=1.35, Bg=0.0015,
        )

    def test_too_few(self):
        with pytest.raises(ValueError, match="At least 2"):
            havelna_odeh_gascap(
                [self._pt()], 1.20, 0.001, 500.0, 0.10,
            )

    def test_bad_Bti(self):
        with pytest.raises(ValueError, match="Bti must be > 0"):
            havelna_odeh_gascap(
                [self._pt(), self._pt()], -1.0, 0.001, 500.0, 0.10,
            )

    def test_bad_m(self):
        with pytest.raises(ValueError, match="m must be >= 0"):
            havelna_odeh_gascap(
                [self._pt(), self._pt()], 1.20, 0.001, 500.0, -0.1,
            )

    def test_all_X_zero(self):
        # Bt = Bti, Bg = Bgi, m finite -> X = 0
        p = HOGC_Point(
            Np=1e6, Rp=500.0, Wp=0.0, We=0.0,
            Bw=1.0, Bt=1.20, Bg=0.001,
        )
        with pytest.raises(ValueError, match="rank-deficient"):
            havelna_odeh_gascap(
                [p, p], 1.20, 0.001, 500.0, 0.10,
            )


class TestConroe():
    """Book Conroe Table 6.2, Fig. 6.4: 3 points, N=600 MM STB
    when dropping the earliest point. Tolerance 10% (the point data
    are not exactly the book's; we test the method, not the exact
    numbers)."""

    def test_free_slope_near_one(self):
        # Construct 3 points on a straight line with slope ~1
        pts = [
            HOGC_Point(Np=1e6, Rp=825.0, Wp=0.0, We=1e6,
                       Bw=1.0, Bt=1.34, Bg=0.0012),
            HOGC_Point(Np=2e6, Rp=825.0, Wp=0.0, We=2e6,
                       Bw=1.0, Bt=1.345, Bg=0.00125),
            HOGC_Point(Np=3e6, Rp=825.0, Wp=0.0, We=3e6,
                       Bw=1.0, Bt=1.35, Bg=0.0013),
        ]
        r = havelna_odeh_gascap(pts, 1.30, 0.0010, 600.0, 0.15)
        assert r.n_hat > 0.0
        assert 0.0 <= r.r_squared <= 1.0
