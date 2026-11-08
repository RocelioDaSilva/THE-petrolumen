"""Tests for backend/app/reservoir/horner.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 7, Sec. 10.2, pp. 259-262, Eqs. (7.68)-(7.71),
Example 7.3 (pp. 261-262).

Golden test uses synthetic Horner points on the book's m=-170 psi/cycle
line; recovered k and S then match the book's 17.5 md and 3.71.
"""

import math
import pytest

from app.reservoir.horner import HornerResult, horner_buildup


class TestExample73:
    """Example 7.3 (pp. 261-262). Book: m=-170, p1hr=2435, k=17.5,
    S=3.71, tp=230 hr, pwf at shut-in=1123 psia.
    Tolerance: 1% on m, 1% on k, 0.05 on S.
    """

    def _horner_points(self) -> list[tuple[float, float]]:
        # Synthetic points on the book's line:
        # pws(dt) = 2435 - 170 * log10((tp + dt)/dt) at dt=1 is 2435.
        # Pick dt in {2, 5, 10, 25, 50} (all in the transient region)
        tp = 230.0
        return [(dt, 2435.0 - 170.0 * math.log10((tp + dt) / dt))
                for dt in (2.0, 5.0, 10.0, 25.0, 50.0)]

    def _run(self) -> HornerResult:
        return horner_buildup(
            q_stb_d=280.0, mu_cp=2.0, B_bbl_stb=1.31, h_ft=40.0,
            phi=0.10, ct_psi_inv=15e-6, rw_ft=0.333,
            tp_hr=230.0, pwf_at_shutin_psia=1123.0,
            horner_points=self._horner_points(),
        )

    def test_m(self):
        r = self._run()
        assert r.m_psi_per_cycle == pytest.approx(-170.0, rel=0.01)

    def test_p1hr(self):
        r = self._run()
        assert r.p1hr_psia == pytest.approx(2435.0, abs=1.0)

    def test_k(self):
        r = self._run()
        assert r.k_md == pytest.approx(17.5, rel=0.01)

    def test_skin(self):
        r = self._run()
        assert r.skin == pytest.approx(3.71, abs=0.05)

    def test_p_star(self):
        r = self._run()
        # p* = extrapolation at dt -> infinity (Horner x -> 0)
        # For the book's line, p* = 2435 + 170*log10(tp+1) is wrong;
        # actually p* = 2435 + 170*log10(tp/1) by construction since
        # we set pws(dt=1) = 2435 means b + m*log10(tp+1) = 2435.
        # At x = 0 (dt = infinity), p* = b, and b = 2435 - m*log10(tp+1).
        expected = 2435.0 - (-170.0) * math.log10(230.0 + 1.0)
        assert r.p_star_psia == pytest.approx(expected, rel=0.01)

    def test_r_squared_near_one(self):
        r = self._run()
        assert r.r_squared > 0.9999


class TestValidation:
    def _ok(self) -> dict:
        return dict(
            q_stb_d=280.0, mu_cp=2.0, B_bbl_stb=1.31, h_ft=40.0,
            phi=0.10, ct_psi_inv=15e-6, rw_ft=0.333,
            tp_hr=230.0, pwf_at_shutin_psia=1123.0,
            horner_points=[(2.0, 2300.0), (50.0, 2450.0)],
        )

    def test_q_zero(self):
        kw = self._ok(); kw["q_stb_d"] = 0.0
        with pytest.raises(ValueError, match="q_stb_d must be > 0"):
            horner_buildup(**kw)

    def test_tp_zero(self):
        kw = self._ok(); kw["tp_hr"] = 0.0
        with pytest.raises(ValueError, match="tp_hr must be > 0"):
            horner_buildup(**kw)

    def test_pwf_shutin_zero(self):
        kw = self._ok(); kw["pwf_at_shutin_psia"] = 0.0
        with pytest.raises(ValueError, match="pwf_at_shutin_psia must be > 0"):
            horner_buildup(**kw)

    def test_too_few(self):
        kw = self._ok(); kw["horner_points"] = [(2.0, 2300.0)]
        with pytest.raises(ValueError, match="At least 2"):
            horner_buildup(**kw)

    def test_dt_zero(self):
        kw = self._ok()
        kw["horner_points"] = [(0.0, 2300.0), (50.0, 2450.0)]
        with pytest.raises(ValueError, match="dt must be > 0"):
            horner_buildup(**kw)

    def test_pws_zero(self):
        kw = self._ok()
        kw["horner_points"] = [(2.0, 0.0), (50.0, 2450.0)]
        with pytest.raises(ValueError, match="pws must be > 0"):
            horner_buildup(**kw)

    def test_short_span(self):
        kw = self._ok()
        kw["horner_points"] = [(2.0, 2400.0), (3.0, 2405.0)]
        with pytest.raises(ValueError, match="Horner time span"):
            horner_buildup(**kw)

    def test_increasing_pws_with_horner_x(self):
        # pws must DECREASE with increasing x (Horner time)
        kw = self._ok()
        kw["horner_points"] = [(50.0, 2300.0), (2.0, 2450.0)]
        with pytest.raises(ValueError, match="Horner slope m .* >= 0"):
            horner_buildup(**kw)


class TestDeterminism:
    def test_repeatable(self):
        pts = [(dt, 2435.0 - 170.0 * math.log10((230.0 + dt) / dt))
               for dt in (2.0, 5.0, 10.0, 25.0, 50.0)]
        kw = dict(
            q_stb_d=280.0, mu_cp=2.0, B_bbl_stb=1.31, h_ft=40.0,
            phi=0.10, ct_psi_inv=15e-6, rw_ft=0.333,
            tp_hr=230.0, pwf_at_shutin_psia=1123.0,
            horner_points=pts,
        )
        a = horner_buildup(**kw)
        b = horner_buildup(**kw)
        assert a.k_md == b.k_md
        assert a.skin == b.skin


class TestParametrizedQ:
    """Larger q (same slope) -> larger k."""

    @pytest.mark.parametrize("q_pair", [(140.0, 280.0), (280.0, 560.0)])
    def test_k_scales_with_q(self, q_pair):
        q1, q2 = q_pair
        pts = [(dt, 2435.0 - 170.0 * math.log10((230.0 + dt) / dt))
               for dt in (2.0, 5.0, 10.0)]
        r1 = horner_buildup(
            q1, 2.0, 1.31, 40.0, 0.10, 15e-6, 0.333,
            230.0, 1123.0, horner_points=pts,
        )
        r2 = horner_buildup(
            q2, 2.0, 1.31, 40.0, 0.10, 15e-6, 0.333,
            230.0, 1123.0, horner_points=pts,
        )
        assert r2.k_md > r1.k_md
