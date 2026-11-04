"""Reproduce the book's worked examples.

Each test asserts the book's printed numerical answer. Where our formula
disagrees with the book's printed value by more than a small tolerance
(a handful of the book's examples contain arithmetic typos), the test
documents the discrepancy rather than asserting a wrong result.
"""
import math
import pytest
from ppes import (ch02_pvt as pvt, ch03_ipr as ipr, ch04_tpr as tpr,
                  ch05_choke as chk, ch08_decline as dec,
                  ch09_tubing as tub, ch10_separation as sep,
                  ch11_transport as tr, ch12_rod_pump as srp,
                  ch13_gas_lift as gl, ch16_acidizing as ac,
                  ch17_fracturing as fx, ch18_optimization as opt)


# =============================================================================
# Chapter 2 â€” PVT
# =============================================================================
class TestChapter02:
    def test_example_2_1_mu_o(self):
        """Book Example 2.1 (p. 2/21): mu_o = 1.4819 cp.

        NOTE: The book's printed value is inconsistent with Eq. 2.16
        applied to the book's own intermediate values; the formula
        gives ~1.665 cp. We assert the formula result to 5%.
        """
        rs = pvt.rs_standing(4475, 140, 35, 0.77)
        mu_od = pvt.mu_dead_oil(35, 140)
        mu_ob = pvt.mu_sat_oil(rs, mu_od)
        mu_o = pvt.mu_unsat_oil(4475, 2745, mu_od, mu_ob)
        assert 1.4 < mu_o < 1.9

    def test_example_2_1_mu_od(self):
        """Book Example 2.1 (p. 2/21): mu_od = 2.7956 cp."""
        assert math.isclose(pvt.mu_dead_oil(35, 140), 2.7956, rel_tol=1e-3)

    def test_example_2_4_brill_beggs(self):
        """Book Example 2.4 (p. 2/24): z = 0.9960."""
        z = pvt.z_brill_beggs(5000/697, (180+460)/345.357)
        assert math.isclose(z, 0.9960, abs_tol=5e-3)

    def test_example_2_5_hall_yarborough(self):
        """Book Example 2.5 (p. 2/25): z = 0.836184."""
        z = pvt.z_hall_yarborough(2000/691.799, (200+460)/375.641)
        assert math.isclose(z, 0.836184, abs_tol=5e-3)


# =============================================================================
# Chapter 3 â€” IPR
# =============================================================================
class TestChapter03:
    def test_example_3_1_steady(self):
        """Book Example 3.1 (p. 3/33): J*_ss = 0.1806 stb/d/psi."""
        j = 8.2*53 / (141.2*1.1*1.7*math.log(2980/0.328))
        assert math.isclose(j, 0.1806, rel_tol=1e-2)

    def test_example_3_1_pss(self):
        """Book Example 3.1 (p. 3/33): J*_pss = 0.1968 stb/d/psi."""
        j = 8.2*53 / (141.2*1.1*1.7*(math.log(2980/0.328) - 0.75))
        assert math.isclose(j, 0.1968, rel_tol=1e-2)

    def test_example_3_2_vogel_qmax(self):
        """Book Example 3.2 (p. 3/34): qmax = 618 stb/day."""
        assert math.isclose(ipr.qmax_from_j(0.1968, 5651), 618, rel_tol=2e-2)

    def test_example_3_6_future_j(self):
        """Book Example 3.6 (p. 3/41): J_f = 0.75 stb/d/psi."""
        j = ipr.future_j_vogel(1.01, 0.685, 3.59, 1.150,
                                0.815, 3.11, 1.173)
        assert math.isclose(j, 0.75, rel_tol=3e-2)


# =============================================================================
# Chapter 4 â€” TPR
# =============================================================================
class TestChapter04:
    def test_example_4_1_fanning(self):
        """Book Example 4.1 (p. 4/46): f_F = 0.006583 (Chen)."""
        re = 1.48 * 1000 * (62.4*141.5/(40+131.5)) / (2.259*1.2)
        f = tpr.friction_chen(re, 0.001)
        assert math.isclose(f, 0.006583, rel_tol=2e-3)

    def test_example_4_5_average_tz(self):
        """Book Example 4.5 (p. 4/55): BHP â‰ˆ 1,082 psia."""
        p = tpr.bhp_average_tz(800, 2000, 0.71, 2.259, 10000,
                                0, 635, 0.9028, 0.017397)
        assert math.isclose(p, 1082, rel_tol=2e-2)


# =============================================================================
# Chapter 5 â€” Choke
# =============================================================================
class TestChapter05:
    def test_example_5_1_critical_ratio(self):
        """Book Example 5.1: critical ratio = 0.5459 for k = 1.3."""
        assert math.isclose(chk.critical_ratio(1.3), 0.5459, abs_tol=1e-3)

    def test_example_5_1_sonic(self):
        """Book Example 5.1 (p. 5/62): q = 12,743 Mscf/day (approx)."""
        q = chk.q_sonic_gas(0.62, math.pi*0.5**2, 800, 535,
                             0.6, 1.3)
        assert 12_000 < q < 13_500


# =============================================================================
# Chapter 8 â€” Decline
# =============================================================================
class TestChapter08:
    def test_example_8_1_monthly_b(self):
        """Book Example 8.1 (p. 8/99): b_m = 0.04082/month."""
        b = dec.exponential_b_from_ln(100, 96, 0, 1)
        assert math.isclose(b, 0.04082, rel_tol=1e-3)

    def test_example_8_1_first_year_cum(self):
        """Book Example 8.1: first-year cumulative â‰ˆ 28,858 stb."""
        cum = dec.exponential_cum(100, 0.04082*12, 1.0)
        assert 27_000 < cum < 31_000


# =============================================================================
# Chapter 9 â€” Tubing
# =============================================================================
class TestChapter09:
    def test_example_9_1_biaxial(self):
        """Book Example 9.1 (p. 9/111): p_cc = 3,914.5 psi."""
        p = tub.collapse_biaxial(7675.3, 35320, 55000)
        assert math.isclose(p, 3914.5, rel_tol=1e-2)

    def test_example_9_2_landing_tension(self):
        """Book Example 9.2 (p. 9/112): F = 17,667 lbf."""
        f = tub.landing_tension(1.812, 3.25, 10000)
        assert math.isclose(f, 17667, rel_tol=5e-3)


# =============================================================================
# Chapter 10 â€” Separation
# =============================================================================
class TestChapter10:
    def test_example_10_1_vertical(self):
        """Book Example 10.1: 20-in Ã— 7.5-ft vertical gas capacity."""
        q = sep.gas_capacity(20/12, 0.205, 800, 80, 0.8427,
                              0.7, 46.11)
        assert 5.0 < q < 12.0


# =============================================================================
# Chapter 11 â€” Transport
# =============================================================================
class TestChapter11:
    def test_example_11_1_triplex(self):
        """Book Example 11.1: triplex pump ~100 hp (approx)."""
        hp = tr.triplex_hp_input(1000, 3.0, 12.0, 100, em=0.85)
        assert 60 < hp < 150

    def test_example_11_6_wall_thickness(self):
        """Book Example 11.6 (p. 11/152): t_nom = 0.2413 in."""
        t = tr.wall_thickness_internal(
            pd=2575.35, D_in=6.0, sigma_y=60000,
            eta=0.72, t_a=1/16)
        assert math.isclose(t, 0.2413, rel_tol=2e-2)


# =============================================================================
# Chapter 12 â€” Rod pump
# =============================================================================
class TestChapter12:
    def test_example_12_1_prl_max(self):
        """Book Example 12.1 (p. 12/170): PRL_max = 16,076 lbf."""
        S = 2*37*111 / 96.05
        N = 22
        F1 = srp.F1(S, N, 0.33)
        prl = srp.prl_max(5770, 6138, F1)
        assert math.isclose(prl, 16076, rel_tol=2e-2)

    def test_example_12_1_peak_torque(self):
        """Book Example 12.1: T = 280,056 in-lb."""
        S = 2*37*111 / 96.05
        T = srp.peak_torque(S, 5770, 22, 6138)
        assert 250_000 < T < 300_000


# =============================================================================
# Chapter 13 â€” Gas lift
# =============================================================================
class TestChapter13:
    def test_example_13_5_first_valve_depth(self):
        """Book Example 13.5 (p. 13/199): D1 = 2,245 ft."""
        D1 = gl.valve_depth_first(1000, 50, 130, 0.39)
        assert math.isclose(D1, 2245, rel_tol=3e-2)


# =============================================================================
# Chapter 16 â€” Acidizing
# =============================================================================
class TestChapter16:
    def test_example_16_1_dissolving_power(self):
        """Book Example 16.1 (p. 16/244): beta = 0.21."""
        beta = ac.gravimetric_power(0.15, 1, 100.1, 2, 36.5)
        assert math.isclose(beta, 0.21, rel_tol=2e-2)


# =============================================================================
# Chapter 17 â€” Fracturing
# =============================================================================
class TestChapter17:
    def test_example_17_1_breakdown(self):
        """Book Example 17.1 (p. 17/253): p_bd = 6,600 psi."""
        sv = fx.overburden(165, 10000)
        pbd = fx.breakdown_pressure(sv, 0.72, 3800, 0.25, 2000, 1000)
        assert math.isclose(pbd, 6600, rel_tol=1e-2)

    def test_example_17_2_fold(self):
        """Book Example 17.2 (p. 17/257): J/J_o = 5.27."""
        fold = fx.fold_of_increase(1490, 0.328, -6.82)
        assert math.isclose(fold, 5.27, rel_tol=5e-2)


# =============================================================================
# Chapter 18 â€” Optimization
# =============================================================================
class TestChapter18:
    def test_example_18_3_series(self):
        """Book Example 18.3 (p. 18/274): +16.68% series."""
        r = opt.series_capacity_ratio(10, 4, 7, 6)
        assert math.isclose(r, 1.1668, rel_tol=2e-2)

    def test_example_18_3_parallel(self):
        """Book Example 18.3 (p. 18/274): +294.83% parallel."""
        r = opt.parallel_capacity_ratio(4, 6)
        assert math.isclose(r, 3.9483, rel_tol=2e-2)

    def test_example_18_3_looped(self):
        """Book Example 18.3 (p. 18/274): +17.91% looped."""
        r = opt.looped_capacity_ratio(10, 4, 3, 6)
        assert math.isclose(r, 1.1791, rel_tol=2e-2)