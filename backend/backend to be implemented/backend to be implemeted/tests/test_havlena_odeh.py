"""Tests for backend/app/reservoir/havlena_odeh.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 2, Sec. 4, pp. 66-67, Eqs. (2.12)-(2.14);
Ch. 6, Sec. 3, pp. 191-193, Table 6.2 / Fig. 6.4.
"""

import pytest

from app.reservoir.havlena_odeh import (
    HavlenaOdehPoint,
    HavlenaOdehResult,
    havelna_odeh,
)


class TestSyntheticConsistent:
    """Construct 3 points on an exact F = N*Eo line with N=100 MM STB,
    Bti=1.20, no gas cap, no compressibility, Rp=Rsoi (no net gas)."""

    def _mk_point(self, Bt: float, Np: float) -> HavlenaOdehPoint:
        return HavlenaOdehPoint(
            Np=Np, Rp=500.0, Wp=0.0, We=0.0, Bw=1.0,
            Bt=Bt, Bg=0.001, delta_p=0.0,
        )

    def _run(self) -> HavlenaOdehResult:
        # N=100: Np_i = 100*(1 - Bti/Bt_i), Bti = 1.20
        points = [
            self._mk_point(Bt=1.50, Np=20.00),
            self._mk_point(Bt=1.40, Np=14.29),
            self._mk_point(Bt=1.30, Np=7.692),
        ]
        return havelna_odeh(
            points=points, Bti=1.20, Bgi=0.001, Rsoi=500.0,
            Swi=0.0, cw=0.0, cf=0.0, m=0.0,
        )

    def test_n_hat(self):
        r = self._run()
        assert r.n_hat / 1.0e6 == pytest.approx(100.0, rel=0.01)

    def test_intercept_near_zero(self):
        r = self._run()
        assert abs(r.intercept) < 1000.0

    def test_r_squared_high(self):
        r = self._run()
        assert r.r_squared > 0.999

    def test_per_point_n_equals_100(self):
        r = self._run()
        for n_i in r.per_point_n:
            assert n_i / 1.0e6 == pytest.approx(100.0, rel=0.02)

    def test_arrays_length(self):
        r = self._run()
        assert len(r.f_values) == 3
        assert len(r.x_values) == 3
        assert len(r.residuals) == 3


class TestGasCapExtension:
    """With m>0 and consistent synthetic data, slope should still equal N.
    Build points with Bg varying and m fixed."""

    def test_m_consistency(self):
        # Set up X_i = Eo_i + (m*Bti/Bgi)*Eg_i to be consistent with F=100*X
        Bti, Bgi, m = 1.20, 0.001, 0.10
        points = []
        for eo, eg, np_ in [
            (0.30, 0.0002, 30.0),
            (0.20, 0.00015, 20.0),
            (0.10, 0.00010, 10.0),
        ]:
            Bt = Bti + eo
            Bg = Bgi + eg
            x_i = eo + (m * Bti / Bgi) * eg
            f_i = 100.0e6 * x_i
            # F = Np*Bt + Bw*Wp - We (with Rp=Rsoi, Wp=0, We=0, Bw=1)
            # => Np = f_i / Bt
            np_exact = f_i / Bt
            points.append(HavlenaOdehPoint(
                Np=np_exact, Rp=500.0, Wp=0.0, We=0.0, Bw=1.0,
                Bt=Bt, Bg=Bg, delta_p=0.0,
            ))
        r = havelna_odeh(
            points=points, Bti=Bti, Bgi=Bgi, Rsoi=500.0,
            Swi=0.0, cw=0.0, cf=0.0, m=m,
        )
        assert r.n_hat / 1.0e6 == pytest.approx(100.0, rel=0.01)


class TestValidation:
    def _pt(self) -> HavlenaOdehPoint:
        return HavlenaOdehPoint(
            Np=10.0e6, Rp=500.0, Wp=0.0, We=0.0, Bw=1.0,
            Bt=1.35, Bg=0.0015, delta_p=0.0,
        )

    def test_fewer_than_two_points(self):
        with pytest.raises(ValueError, match="At least 2 points"):
            havelna_odeh(
                points=[self._pt()],
                Bti=1.20, Bgi=0.001, Rsoi=500.0,
                Swi=0.0, cw=0.0, cf=0.0, m=0.0,
            )

    def test_bad_Bti(self):
        with pytest.raises(ValueError, match="Bti must be > 0"):
            havelna_odeh(
                points=[self._pt(), self._pt()],
                Bti=-1.0, Bgi=0.001, Rsoi=500.0,
                Swi=0.0, cw=0.0, cf=0.0,
            )

    def test_bad_Bgi(self):
        with pytest.raises(ValueError, match="Bgi must be > 0"):
            havelna_odeh(
                points=[self._pt(), self._pt()],
                Bti=1.20, Bgi=0.0, Rsoi=500.0,
                Swi=0.0, cw=0.0, cf=0.0,
            )

    def test_bad_Swi(self):
        with pytest.raises(ValueError, match="Swi must be in"):
            havelna_odeh(
                points=[self._pt(), self._pt()],
                Bti=1.20, Bgi=0.001, Rsoi=500.0,
                Swi=1.5, cw=0.0, cf=0.0,
            )

    def test_bad_Np_in_point(self):
        pts = [
            self._pt(),
            HavlenaOdehPoint(
                Np=-1.0, Rp=500.0, Wp=0.0, We=0.0, Bw=1.0,
                Bt=1.35, Bg=0.0015, delta_p=0.0,
            ),
        ]
        with pytest.raises(ValueError, match="Np must be >= 0"):
            havelna_odeh(
                points=pts, Bti=1.20, Bgi=0.001, Rsoi=500.0,
                Swi=0.0, cw=0.0, cf=0.0,
            )


class TestDegenerate:
    def test_all_X_zero(self):
        """If Bt = Bti for every point (and no comp, no gas cap), then
        all X_i = 0 and the design matrix is rank-deficient."""
        p = HavlenaOdehPoint(
            Np=1.0e6, Rp=500.0, Wp=0.0, We=0.0, Bw=1.0,
            Bt=1.20, Bg=0.001, delta_p=0.0,
        )
        with pytest.raises(ValueError, match="rank-deficient"):
            havelna_odeh(
                points=[p, p], Bti=1.20, Bgi=0.001, Rsoi=500.0,
                Swi=0.0, cw=0.0, cf=0.0, m=0.0,
            )


class TestNumericRegression:
    def test_fixed_value(self):
        # 2 points with eo = 0.10 and 0.20, no comp, no gas cap
        # X = [0.10, 0.20]; F = Np*Bt with Np chosen to make F = 50*X
        pts = [
            HavlenaOdehPoint(
                Np=2.5e6, Rp=500.0, Wp=0.0, We=0.0, Bw=1.0,
                Bt=1.30, Bg=0.0015, delta_p=0.0,
            ),
            HavlenaOdehPoint(
                Np=5.0e6, Rp=500.0, Wp=0.0, We=0.0, Bw=1.0,
                Bt=1.40, Bg=0.0015, delta_p=0.0,
            ),
        ]
        r = havelna_odeh(
            points=pts, Bti=1.20, Bgi=0.001, Rsoi=500.0,
            Swi=0.0, cw=0.0, cf=0.0, m=0.0,
        )
        # F = [2.5e6*1.30, 5.0e6*1.40] = [3.25e6, 7.0e6]
        # X = [0.10, 0.20]
        # slope = (0.10*3.25e6 + 0.20*7.0e6) / (0.10^2 + 0.20^2)
        #       = (0.325 + 1.4)e6 / 0.05 = 1.725e6 / 0.05 = 34.5e6
        assert r.n_hat == pytest.approx(34.5e6, rel=1e-6)


class TestParametrizedR2:
    """R^2 should be 1 for exact synthetic data across different m values."""

    @pytest.mark.parametrize("m_val", [0.0, 0.05, 0.20])
    def test_exact_fit(self, m_val):
        Bti, Bgi = 1.20, 0.001
        # Consistent points: pick eo, eg, then np such that F = 100*X
        pts = []
        for eo, eg in [(0.30, 0.0002), (0.20, 0.00015), (0.10, 0.00010)]:
            Bt = Bti + eo
            Bg = Bgi + eg
            x_i = eo + (m_val * Bti / Bgi) * eg
            f_i = 100.0e6 * x_i
            np_exact = f_i / Bt
            pts.append(HavlenaOdehPoint(
                Np=np_exact, Rp=500.0, Wp=0.0, We=0.0, Bw=1.0,
                Bt=Bt, Bg=Bg, delta_p=0.0,
            ))
        r = havelna_odeh(
            points=pts, Bti=Bti, Bgi=Bgi, Rsoi=500.0,
            Swi=0.0, cw=0.0, cf=0.0, m=m_val,
        )
        assert r.r_squared > 0.9999
