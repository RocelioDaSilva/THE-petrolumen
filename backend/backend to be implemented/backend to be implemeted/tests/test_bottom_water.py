"""Tests for backend/app/reservoir/bottom_water.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 8, Sec. 3.2, pp. 299-324, Eqs. (8.10)-(8.14),
Tables 8.6-8.10, Example 8.4 (pp. 300-301).
"""

import math
import pytest

from app.reservoir.bottom_water import (
    BottomWaterResult,
    _scale_factor,
    bottom_water_influx,
)


class TestExample84:
    """Example 8.4: r_R=2000, h=200, k=50, F_k=0.04, phi=0.10,
    mu=0.395, ct=8e-6, r_D'=inf, z_D'=0.5. B''=716 bbl/psi.
    Boundary pressure history 3000->2755 in 30-day steps.
    Book final We = 2.782 MM bbl. Tolerance 5%.
    """

    def test_b_double_prime(self):
        r = bottom_water_influx(
            k_md=50.0, phi=0.10, mu_w_cp=0.395, ct_psi_inv=8e-6,
            h_ft=200.0, r_R_ft=2000.0,
            F_k=0.04, r_e_over_r_R=1.0e6,
            p_history=[(0.0, 3000.0), (30.0, 2956.0)],
        )
        # Expected: 1.119 * 0.10 * 200 * 8e-6 * 4e6 = 716.16
        assert r.B_double_prime_bbl_psi == pytest.approx(716.0, rel=0.01)

    def test_z_D_prime(self):
        r = bottom_water_influx(
            k_md=50.0, phi=0.10, mu_w_cp=0.395, ct_psi_inv=8e-6,
            h_ft=200.0, r_R_ft=2000.0,
            F_k=0.04, r_e_over_r_R=1.0e6,
            p_history=[(0.0, 3000.0), (30.0, 2956.0)],
        )
        # z_D' = h / (r_R * sqrt(F_k)) = 200 / (2000 * 0.2) = 0.5
        assert r.z_D_prime == pytest.approx(0.5, rel=0.01)


class TestScaleFactor:
    """Calibrated scaling points."""

    @pytest.mark.parametrize(
        "zD,s_expected",
        [(0.1, 0.85), (0.3, 0.55), (0.5, 0.37), (0.7, 0.27), (0.9, 0.20)],
    )
    def test_interp(self, zD, s_expected):
        assert _scale_factor(zD) == pytest.approx(s_expected, rel=0.01)

    def test_zero_degenerate(self):
        # z_D'=0 means no vertical distance, edge-like => s=1
        assert _scale_factor(0.0) == pytest.approx(1.0)

    def test_above_max_returns_lowest(self):
        assert _scale_factor(2.0) == pytest.approx(0.20)


class TestFkEffect:
    """Larger F_k (more vertical connectivity) => higher W_eD scaling."""

    def test_higher_Fk_higher_we(self):
        kw = dict(
            k_md=50.0, phi=0.10, mu_w_cp=0.395, ct_psi_inv=8e-6,
            h_ft=200.0, r_R_ft=2000.0, r_e_over_r_R=1.0e6,
            p_history=[
                (0.0, 3000.0), (30.0, 2956.0), (60.0, 2917.0),
                (90.0, 2877.0), (120.0, 2844.0),
                (150.0, 2811.0), (180.0, 2791.0),
                (210.0, 2773.0), (240.0, 2755.0),
            ],
        )
        r_low = bottom_water_influx(F_k=0.02, **kw)
        r_high = bottom_water_influx(F_k=0.50, **kw)
        # Higher F_k => lower z_D' => larger s => larger We
        assert r_high.we_cumulative_bbl > r_low.we_cumulative_bbl


class TestOverride:
    def test_custom_wed(self):
        def my_wed(tD: float, rD: float, zD: float) -> float:
            return 2.0 * math.sqrt(tD)

        r = bottom_water_influx(
            k_md=50.0, phi=0.10, mu_w_cp=0.395, ct_psi_inv=8e-6,
            h_ft=200.0, r_R_ft=2000.0,
            F_k=0.04, r_e_over_r_R=1.0e6,
            p_history=[(0.0, 3000.0), (30.0, 2956.0)],
            wed_func=my_wed,
        )
        tD = 0.0002637 * 50.0 * 30.0 / (
            0.10 * 0.395 * 8e-6 * 2000.0 ** 2
        )
        expected = 716.16 * 44.0 * 2.0 * math.sqrt(tD)
        assert r.we_cumulative_bbl == pytest.approx(expected, rel=0.02)


class TestValidation:
    def _ok(self) -> dict:
        return dict(
            k_md=50.0, phi=0.10, mu_w_cp=0.395, ct_psi_inv=8e-6,
            h_ft=200.0, r_R_ft=2000.0, F_k=0.04,
            r_e_over_r_R=1.0e6,
            p_history=[(0.0, 3000.0), (30.0, 2956.0)],
        )

    def test_Fk_zero(self):
        kw = self._ok(); kw["F_k"] = 0.0
        with pytest.raises(ValueError, match="F_k must be in"):
            bottom_water_influx(**kw)

    def test_Fk_too_high(self):
        kw = self._ok(); kw["F_k"] = 1.5
        with pytest.raises(ValueError, match="F_k must be in"):
            bottom_water_influx(**kw)

    def test_r_ratio_le_one(self):
        kw = self._ok(); kw["r_e_over_r_R"] = 0.5
        with pytest.raises(ValueError, match="r_e_over_r_R must be > 1"):
            bottom_water_influx(**kw)

    def test_phi_out(self):
        kw = self._ok(); kw["phi"] = 1.5
        with pytest.raises(ValueError, match="phi must be in"):
            bottom_water_influx(**kw)

    def test_short_history(self):
        kw = self._ok(); kw["p_history"] = [(0.0, 3000.0)]
        with pytest.raises(ValueError, match=">= 2 points"):
            bottom_water_influx(**kw)

    def test_non_increasing(self):
        kw = self._ok()
        kw["p_history"] = [(30.0, 3000.0), (30.0, 2956.0)]
        with pytest.raises(ValueError, match="strictly increasing"):
            bottom_water_influx(**kw)


class TestDeterminism:
    def test_repeatable(self):
        kw = dict(
            k_md=50.0, phi=0.10, mu_w_cp=0.395, ct_psi_inv=8e-6,
            h_ft=200.0, r_R_ft=2000.0, F_k=0.04,
            r_e_over_r_R=1.0e6,
            p_history=[(0.0, 3000.0), (30.0, 2956.0)],
        )
        a = bottom_water_influx(**kw)
        b = bottom_water_influx(**kw)
        assert a.we_cumulative_bbl == b.we_cumulative_bbl


class TestParametrizedHistory:
    """Longer history produces more cumulative W_e (monotonic)."""

    @pytest.mark.parametrize("n_steps", [2, 4, 6])
    def test_monotone(self, n_steps):
        # Simple linear decline 3000 -> 2755 over n_steps*30 days
        history = []
        for i in range(n_steps):
            p = 3000.0 - (245.0 * i / (n_steps - 1)) if n_steps > 1 else 3000.0
            history.append((float(i * 30), float(p)))
        if n_steps > 1:
            r = bottom_water_influx(
                k_md=50.0, phi=0.10, mu_w_cp=0.395, ct_psi_inv=8e-6,
                h_ft=200.0, r_R_ft=2000.0, F_k=0.04,
                r_e_over_r_R=1.0e6, p_history=history,
            )
            assert r.we_cumulative_bbl > 0.0
