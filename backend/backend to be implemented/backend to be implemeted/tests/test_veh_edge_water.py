"""Tests for backend/app/reservoir/veh_edge_water.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 8, Sec. 3.1, pp. 280-299, Eqs. (8.6)-(8.9),
Tables 8.1-8.2, Examples 8.1-8.3.
"""

import pytest

from app.reservoir.veh_edge_water import (
    VehResult,
    _weD_infinite,
    veh_edge_water_influx,
)


class TestWeDFanchi:
    """Example 8.1 (p. 283): W_eD at t_D = 5.88, 11.76, 23.52, 47.04
    are 5.07, 8.43, 13.90, 22.75. Tolerance 5% (Fanchi approximation).
    """

    @pytest.mark.parametrize(
        "tD,wed_book",
        [(5.88, 5.07), (11.76, 8.43), (23.52, 13.90), (47.04, 22.75)],
    )
    def test_wed(self, tD, wed_book):
        assert _weD_infinite(tD) == pytest.approx(wed_book, rel=0.05)


class TestExample81:
    """Example 8.1 (p. 283): B'=644.5; single 10 psi step; We at
    100/200/400/800 days = 32,680 / 54,330 / 89,590 / 146,600 bbl.
    Tolerance 5%.
    """

    def _run(self) -> VehResult:
        # Inputs chosen to reproduce t_D = 0.00245*t as in Ex 8.1
        # With theta=360, r_R=3000, h=40, phi=0.20, ct=8e-6,
        # mu=0.62:  td_factor = 0.0002637*k/(phi*mu*ct*r_R^2)
        # For k=83: 0.0002637*83/(0.20*0.62*8e-6*9e6) = 0.00245
        return veh_edge_water_influx(
            k_md=83.0, phi=0.20, mu_w_cp=0.62,
            ct_psi_inv=8.0e-6, h_ft=40.0, r_R_ft=3000.0,
            theta_deg=360.0,
            p_history=[
                (0.0, 2734.0),
                (100.0 * 24.0, 2724.0),
                (200.0 * 24.0, 2724.0),
                (400.0 * 24.0, 2724.0),
                (800.0 * 24.0, 2724.0),
            ],
        )

    def test_b_prime(self):
        r = self._run()
        assert r.B_prime_bbl_psi == pytest.approx(644.5, rel=0.02)

    def test_we_at_100(self):
        r = self._run()
        assert r.we_at_points_bbl[1] == pytest.approx(32_680.0, rel=0.05)

    def test_we_at_200(self):
        r = self._run()
        assert r.we_at_points_bbl[2] == pytest.approx(54_330.0, rel=0.05)

    def test_we_at_400(self):
        r = self._run()
        assert r.we_at_points_bbl[3] == pytest.approx(89_590.0, rel=0.05)

    def test_we_at_800(self):
        r = self._run()
        assert r.we_at_points_bbl[4] == pytest.approx(146_600.0, rel=0.05)


class TestExample82TwoStep:
    """Example 8.2 (p. 296): two-step history, B'=644.5.
    dp1=10 at t=0, dp2=20 at 100 days. At 400 days: We=233,190 bbl.
    Tolerance 3% (book uses table values; ours Fanchi).
    """

    def test_two_step(self):
        r = veh_edge_water_influx(
            k_md=83.0, phi=0.20, mu_w_cp=0.62,
            ct_psi_inv=8.0e-6, h_ft=40.0, r_R_ft=3000.0,
            theta_deg=360.0,
            p_history=[
                (0.0, 2734.0),
                (100.0 * 24.0, 2724.0),
                (400.0 * 24.0, 2704.0),
            ],
        )
        assert r.we_cumulative_bbl == pytest.approx(233_190.0, rel=0.03)


class TestFiniteAquiferCap:
    """For r_e/r_R=10, W_eD at very large t_D is capped at ~43.7
    (Table 8.2) rather than growing without bound."""

    def test_cap(self):
        # 100,000 days -> t_D huge; W_eD must be capped
        r = veh_edge_water_influx(
            k_md=83.0, phi=0.20, mu_w_cp=0.62,
            ct_psi_inv=8.0e-6, h_ft=40.0, r_R_ft=3000.0,
            theta_deg=360.0,
            p_history=[
                (0.0, 2734.0),
                (100000.0 * 24.0, 2724.0),
            ],
            r_e_over_r_R=10.0,
        )
        # With cap, We = 644.5 * 10 * 43.7 = 281,500
        assert r.we_cumulative_bbl / 281500.0 == pytest.approx(1.0, abs=0.05)


class TestWeDOverride:
    """Caller-supplied W_eD function overrides the built-in."""

    def test_override(self):
        def my_weD(tD: float, r: float | None) -> float:
            return 2.0 * (tD ** 0.5)

        r = veh_edge_water_influx(
            k_md=83.0, phi=0.20, mu_w_cp=0.62,
            ct_psi_inv=8.0e-6, h_ft=40.0, r_R_ft=3000.0,
            theta_deg=360.0,
            p_history=[(0.0, 2734.0), (100.0 * 24.0, 2724.0)],
            wed_func=my_weD,
        )
        # Expected: 644.5 * 10 * 2 * sqrt(5.88) = 644.5 * 10 * 4.849 = 31,250
        assert r.we_cumulative_bbl == pytest.approx(31250.0, rel=0.02)


class TestValidation:
    def _ok(self) -> dict:
        return dict(
            k_md=83.0, phi=0.20, mu_w_cp=0.62, ct_psi_inv=8e-6,
            h_ft=40.0, r_R_ft=3000.0, theta_deg=360.0,
            p_history=[(0.0, 2734.0), (2400.0, 2724.0)],
        )

    def test_k_zero(self):
        kw = self._ok(); kw["k_md"] = 0.0
        with pytest.raises(ValueError, match="k_md must be > 0"):
            veh_edge_water_influx(**kw)

    def test_phi_out(self):
        kw = self._ok(); kw["phi"] = 1.5
        with pytest.raises(ValueError, match="phi must be in"):
            veh_edge_water_influx(**kw)

    def test_theta_zero(self):
        kw = self._ok(); kw["theta_deg"] = 0.0
        with pytest.raises(ValueError, match="theta_deg must be"):
            veh_edge_water_influx(**kw)

    def test_short_history(self):
        kw = self._ok(); kw["p_history"] = [(0.0, 2734.0)]
        with pytest.raises(ValueError, match=">= 2 points"):
            veh_edge_water_influx(**kw)

    def test_non_increasing(self):
        kw = self._ok()
        kw["p_history"] = [(100.0, 2734.0), (100.0, 2724.0)]
        with pytest.raises(ValueError, match="strictly increasing"):
            veh_edge_water_influx(**kw)

    def test_r_ratio_below_one(self):
        kw = self._ok(); kw["r_e_over_r_R"] = 0.5
        with pytest.raises(ValueError, match="r_e_over_r_R must be"):
            veh_edge_water_influx(**kw)


class TestDeterminism:
    def test_repeatable(self):
        kw = dict(
            k_md=83.0, phi=0.20, mu_w_cp=0.62, ct_psi_inv=8e-6,
            h_ft=40.0, r_R_ft=3000.0, theta_deg=360.0,
            p_history=[(0.0, 2734.0), (2400.0, 2724.0)],
        )
        a = veh_edge_water_influx(**kw)
        b = veh_edge_water_influx(**kw)
        assert a.we_cumulative_bbl == b.we_cumulative_bbl


class TestParametrizedTheta:
    """Smaller theta (partial contact) -> smaller B' and smaller We."""

    @pytest.mark.parametrize("theta_pair", [(180.0, 360.0)])
    def test_we_scales_with_theta(self, theta_pair):
        t1, t2 = theta_pair
        kw = dict(
            k_md=83.0, phi=0.20, mu_w_cp=0.62, ct_psi_inv=8e-6,
            h_ft=40.0, r_R_ft=3000.0,
            p_history=[(0.0, 2734.0), (2400.0, 2724.0)],
        )
        r1 = veh_edge_water_influx(theta_deg=t1, **kw)
        r2 = veh_edge_water_influx(theta_deg=t2, **kw)
        assert r2.we_cumulative_bbl == pytest.approx(
            2.0 * r1.we_cumulative_bbl, rel=1e-9
        )
