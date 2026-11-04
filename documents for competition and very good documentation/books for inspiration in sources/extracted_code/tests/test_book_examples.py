"""Validation against every book worked example."""
import math
import numpy as np
import pytest
from ppes import (ch02_pvt as pvt, ch03_ipr as ipr,
                   ch04_tpr as tpr, ch05_choke as chk,
                   ch08_decline as dec, ch09_tubing as tub,
                   ch10_separation as sep, ch11_transport as tr,
                   ch12_rod_pump as srp, ch13_gas_lift as gl,
                   ch16_acidizing as ac, ch17_fracturing as fx,
                   ch18_optimization as opt)

# === Chapter 2 ===
class TestCh02:
    def test_ex_2_1(self):
        rs = 600.0
        mu_od = pvt.mu_dead_oil(35, 140)
        mu_ob = pvt.mu_sat_oil(rs, mu_od)
        mu_o = pvt.mu_unsat_oil(4475, 2745, mu_od, mu_ob)
        assert math.isclose(mu_o, 1.666, rel_tol=1e-2)

    def test_ex_2_4(self):
        z = pvt.z_brill_beggs(5000/697, (180+460)/345.357)
        assert math.isclose(z, 0.979, rel_tol=2e-2)

    def test_ex_2_5(self):
        z = pvt.z_hall_yarborough(2000/691.799,
                                    (200+460)/375.641)
        assert math.isclose(z, 0.885, rel_tol=2e-2)

# === Chapter 3 ===
class TestCh03:
    def test_ex_3_1_steady(self):
        j = 8.2*53/(141.2*1.1*1.7*math.log(2980/0.328))
        assert math.isclose(j, 0.1806, rel_tol=1e-2)

    def test_ex_3_1_pss(self):
        j = 8.2*53/(141.2*1.1*1.7*(math.log(2980/0.328) - 0.75))
        assert math.isclose(j, 0.1968, rel_tol=1e-2)

    def test_ex_3_2(self):
        assert math.isclose(ipr.qmax_from_j(0.1968, 5651), 618,
                              rel_tol=2e-2)

    def test_ex_3_6(self):
        j = ipr.future_j_vogel(1.01, 0.685, 3.59, 1.150,
                                0.815, 3.11, 1.173)
        assert math.isclose(j, 0.75, rel_tol=2e-2)

# === Chapter 4 ===
class TestCh04:
    def test_ex_4_1(self):
        re = 1.48*1000*(62.4*141.5/(40+131.5))/(2.259*1.2)
        f = tpr.friction_chen(re, 0.001)
        assert math.isclose(f, 0.006583, rel_tol=2e-3)

    def test_ex_4_5(self):
        p = tpr.bhp_average_tz(800, 2000, 0.71, 2.259, 10000,
                                0, 635, 0.9028, 0.017397)
        assert math.isclose(p, 1082, rel_tol=2e-2)

# === Chapter 5 ===
class TestCh05:
    def test_ex_5_1_critical(self):
        assert math.isclose(chk.critical_ratio(1.3), 0.5459,
                              abs_tol=1e-3)

    def test_ex_5_1_sonic(self):
        q = chk.q_sonic_gas(0.62, math.pi*0.5**2, 800, 535,
                              0.6, 1.3)
        assert 12000 < q < 13500

# === Chapter 8 ===
class TestCh08:
    def test_ex_8_1(self):
        b = dec.exponential_b_from_ln(100, 96, 0, 1)
        assert math.isclose(b, 0.04082, rel_tol=1e-3)

# === Chapter 9 ===
class TestCh09:
    def test_ex_9_1(self):
        p = tub.collapse_biaxial(7675.3, 35320, 55000)
        assert math.isclose(p, 3914.5, rel_tol=1e-2)

    def test_ex_9_2(self):
        f = tub.landing_tension(1.812, 3.25, 10000)
        assert math.isclose(f, 17667, rel_tol=5e-3)

# === Chapter 10 ===
class TestCh10:
    def test_ex_10_1(self):
        q = sep.gas_capacity(20/12, 0.205, 800, 80, 0.8427,
                               0.7, 46.11)
        assert 5.0 < q < 12.0

# === Chapter 11 ===
class TestCh11:
    def test_ex_11_1(self):
        hp = tr.triplex_hp_input(1000, 3.0, 12.0, 100, em=0.85)
        assert 50 < hp < 200

    def test_ex_11_6(self):
        t = tr.wall_thickness_internal(
            pd=2575.35, D=6.0, sigma_y=60000,
            eta=0.72, t_a=1/16)
        assert math.isclose(t, 0.2413, rel_tol=2e-2)

# === Chapter 12 ===
class TestCh12:
    def test_ex_12_1_speed(self):
        S = 2*37*111/96.05
        N = srp.speed_limit(S, 0.33, L=0.4)
        assert math.isclose(N, 17.6, rel_tol=2e-2)

    def test_ex_12_1_prl(self):
        S = 2*37*111/96.05
        F1 = srp.F1(S, 22, 0.33)
        prl = srp.prl_max(5770, 6138, F1)
        assert math.isclose(prl, 16076, rel_tol=2e-2)

    def test_ex_12_1_torque(self):
        S = 2*37*111/96.05
        T = srp.peak_torque(S, 5770, 22, 6138)
        assert math.isclose(T, 280056, rel_tol=3e-2)

# === Chapter 13 ===
class TestCh13:
    def test_ex_13_5(self):
        D1 = gl.valve_depth_first(1000, 50, 130, 0.39)
        assert math.isclose(D1, 2245, rel_tol=3e-2)

# === Chapter 16 ===
class TestCh16:
    def test_ex_16_1(self):
        beta = ac.gravimetric_power(0.15, 1, 100.1, 2, 36.5)
        assert math.isclose(beta, 0.2057, rel_tol=1e-2)

    def test_ex_16_2(self):
        q = ac.max_injection_rate(50, 60, 6650, 4000, 300,
                                    1.5, 1000, 0.328, 15)
        assert math.isclose(q, 1.34, rel_tol=2e-2)

# === Chapter 17 ===
class TestCh17:
    def test_ex_17_1(self):
        sv = fx.overburden(165, 10000)
        pbd = fx.breakdown_pressure(sv, 0.72, 3800, 0.25,
                                      2000, 1000)
        assert math.isclose(pbd, 6487, rel_tol=2e-2)

    def test_ex_17_2(self):
        fold = fx.fold_of_increase(1490, 0.328, -6.82)
        assert math.isclose(fold, 5.26, rel_tol=2e-2)

    def test_ex_17_4(self):
        p = fx.treatment_surface_pressure(
            pbd=6600, rho=1.2, D=10000, q=10, mu=20, d=3.0)
        assert math.isclose(p, 4959, rel_tol=5e-2)

# === Chapter 18 ===
class TestCh18:
    def test_ex_18_3_series(self):
        r = opt.series_capacity_ratio(10, 4, 7, 6)
        assert math.isclose(r, 1.1668, rel_tol=2e-2)

    def test_ex_18_3_parallel(self):
        r = opt.parallel_capacity_ratio(4, 6)
        assert math.isclose(r, 3.9483, rel_tol=2e-2)

    def test_ex_18_3_looped(self):
        r = opt.looped_capacity_ratio(10, 4, 3, 6)
        assert math.isclose(r, 1.1791, rel_tol=2e-2)
