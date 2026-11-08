"""Tests for backend/app/reservoir/drawdown.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 7, Sec. 6.1 and 10.1, pp. 234-258,
Eqs. (7.37), (7.58)-(7.67), Example 7.2 (pp. 256-258).

Golden test uses synthetic points that reproduce the book's stated
m=-86 psi/cycle and p1hr=3526 psia exactly; the recovered k and S
then match the book's 85.1 md and 1.04.
"""

import math
import pytest

from app.reservoir.drawdown import (
    DrawdownResult,
    drawdown_analysis,
)


class TestExample72:
    """Example 7.2 (pp. 256-258). Book: m=-86, p1hr=3526, k=85.1,
    S=1.04. Tolerance: 1% on m, 1% on k, 0.05 on S.
    """

    def _semilog_points(self) -> list[tuple[float, float]]:
        # Synthetic points on the book's line:
        # pwf(t) = 3526 - 86 * log10(t) for t in {1,2,3,4,5,10}
        return [(t, 3526.0 - 86.0 * math.log10(t))
                for t in (1.0, 2.0, 3.0, 4.0, 5.0, 10.0)]

    def _run(self) -> DrawdownResult:
        return drawdown_analysis(
            q_stb_d=500.0, mu_cp=1.5, B_bbl_stb=1.2, h_ft=20.0,
            phi=0.25, ct_psi_inv=30e-6, rw_ft=0.333, pi_psia=4000.0,
            semilog_points=self._semilog_points(),
        )

    def test_m(self):
        r = self._run()
        assert r.m_psi_per_cycle == pytest.approx(-86.0, rel=0.01)

    def test_p1hr(self):
        r = self._run()
        assert r.p1hr_psia == pytest.approx(3526.0, rel=0.001)

    def test_k(self):
        r = self._run()
        assert r.k_md == pytest.approx(85.1, rel=0.01)

    def test_skin(self):
        r = self._run()
        assert r.skin == pytest.approx(1.04, abs=0.05)

    def test_r_squared_near_one(self):
        r = self._run()
        assert r.r_squared_semilog > 0.9999


class TestPseudosteadyArea:
    """Example 7.2 p. 257: m'=-0.373 psi/hr, book A=57.6 ac = 2509,
    000 ft^2. Synthetic cartesian line gives the same A.
    """

    def _pss_points(self) -> list[tuple[float, float]]:
        # pwf = 3315 - 0.373*t (t in {100, 200, 300} -- book's last 3)
        return [(t, 3315.0 - 0.373 * t) for t in (100.0, 200.0, 300.0)]

    def test_area(self):
        r = drawdown_analysis(
            q_stb_d=500.0, mu_cp=1.5, B_bbl_stb=1.2, h_ft=20.0,
            phi=0.25, ct_psi_inv=30e-6, rw_ft=0.333, pi_psia=4000.0,
            semilog_points=[
                (t, 3526.0 - 86.0 * math.log10(t))
                for t in (1.0, 2.0, 3.0, 4.0, 5.0, 10.0)
            ],
            pseudosteady_points=self._pss_points(),
        )
        assert r.drainage_area_ft2 is not None
        # 57.6 ac * 43560 = 2,509,056 ft^2; tolerance 2%
        assert r.drainage_area_ft2 == pytest.approx(2509056.0, rel=0.02)

    def test_m_prime(self):
        r = drawdown_analysis(
            q_stb_d=500.0, mu_cp=1.5, B_bbl_stb=1.2, h_ft=20.0,
            phi=0.25, ct_psi_inv=30e-6, rw_ft=0.333, pi_psia=4000.0,
            semilog_points=[(t, 3526.0 - 86.0 * math.log10(t))
                            for t in (1.0, 10.0)],
            pseudosteady_points=self._pss_points(),
        )
        assert r.m_prime_psi_per_hr == pytest.approx(-0.373, rel=0.01)


class TestValidation:
    def _ok(self) -> dict:
        return dict(
            q_stb_d=500.0, mu_cp=1.5, B_bbl_stb=1.2, h_ft=20.0,
            phi=0.25, ct_psi_inv=30e-6, rw_ft=0.333, pi_psia=4000.0,
            semilog_points=[(1.0, 3400.0), (10.0, 3314.0)],
        )

    def test_q_zero(self):
        kw = self._ok(); kw["q_stb_d"] = 0.0
        with pytest.raises(ValueError, match="q_stb_d must be > 0"):
            drawdown_analysis(**kw)

    def test_phi_out(self):
        kw = self._ok(); kw["phi"] = 1.5
        with pytest.raises(ValueError, match="phi must be in"):
            drawdown_analysis(**kw)

    def test_too_few_points(self):
        kw = self._ok(); kw["semilog_points"] = [(1.0, 3400.0)]
        with pytest.raises(ValueError, match="At least 2"):
            drawdown_analysis(**kw)

    def test_time_zero(self):
        kw = self._ok()
        kw["semilog_points"] = [(0.0, 3400.0), (10.0, 3314.0)]
        with pytest.raises(ValueError, match="time must be > 0"):
            drawdown_analysis(**kw)

    def test_pwf_zero(self):
        kw = self._ok()
        kw["semilog_points"] = [(1.0, 0.0), (10.0, 3314.0)]
        with pytest.raises(ValueError, match="pwf must be > 0"):
            drawdown_analysis(**kw)

    def test_short_log_span(self):
        kw = self._ok()
        kw["semilog_points"] = [(1.0, 3400.0), (1.5, 3390.0)]
        with pytest.raises(ValueError, match="Semilog time span"):
            drawdown_analysis(**kw)

    def test_increasing_pwf(self):
        kw = self._ok()
        kw["semilog_points"] = [(1.0, 3314.0), (10.0, 3400.0)]
        with pytest.raises(ValueError, match="slope m .* >= 0"):
            drawdown_analysis(**kw)

    def test_pss_too_few(self):
        kw = self._ok()
        kw["pseudosteady_points"] = [(100.0, 3278.0)]
        with pytest.raises(ValueError, match="At least 2 pseudosteady"):
            drawdown_analysis(**kw)


class TestDeterminism:
    def test_repeatable(self):
        pts = [(t, 3526.0 - 86.0 * math.log10(t))
               for t in (1.0, 2.0, 3.0, 4.0, 5.0, 10.0)]
        kw = dict(
            q_stb_d=500.0, mu_cp=1.5, B_bbl_stb=1.2, h_ft=20.0,
            phi=0.25, ct_psi_inv=30e-6, rw_ft=0.333, pi_psia=4000.0,
            semilog_points=pts,
        )
        a = drawdown_analysis(**kw)
        b = drawdown_analysis(**kw)
        assert a.k_md == b.k_md
        assert a.skin == b.skin


class TestParametrizedQ:
    """Larger q (same m) -> larger k."""

    @pytest.mark.parametrize("q_pair", [(250.0, 500.0), (500.0, 1000.0)])
    def test_k_scales_with_q(self, q_pair):
        q1, q2 = q_pair
        pts = [(t, 3526.0 - 86.0 * math.log10(t))
               for t in (1.0, 10.0)]
        r1 = drawdown_analysis(
            250.0 if q1 == 250.0 else 500.0, 1.5, 1.2, 20.0, 0.25,
            30e-6, 0.333, 4000.0, semilog_points=pts,
        )
        r2 = drawdown_analysis(
            500.0 if q2 == 500.0 else 1000.0, 1.5, 1.2, 20.0, 0.25,
            30e-6, 0.333, 4000.0, semilog_points=pts,
        )
        assert r2.k_md > r1.k_md
