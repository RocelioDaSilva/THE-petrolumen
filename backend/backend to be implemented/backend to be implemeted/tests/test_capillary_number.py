"""Tests for backend/app/reservoir/capillary_number.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 9, Sec. 5.1, pp. 380-381, Eq. (9.58), Fig. 9.19.
"""

import pytest

from app.reservoir.capillary_number import (
    CapillaryNumberResult,
    capillary_number,
)


class TestTypicalWaterflood:
    """k_o=100 md, dp=1000, phi=0.20, sigma=30, L=1000:
    N_w = 1e-3 * 100 * 1000 / (0.20 * 30 * 1000) = 1e-3 / 6 ~ 1.67e-5.
    Right at the capillary-number transition knee; category 'transition'.
    """

    def test_Nw(self):
        r = capillary_number(
            k_o_md=100.0, delta_p_psi=1000.0, L_ft=1000.0,
            phi=0.20, sigma_ow_dyn_cm=30.0,
        )
        assert isinstance(r, CapillaryNumberResult)
        assert r.N_w == pytest.approx(1.0 / 600.0, rel=1e-9)

    def test_category(self):
        r = capillary_number(
            k_o_md=100.0, delta_p_psi=1000.0, L_ft=1000.0,
            phi=0.20, sigma_ow_dyn_cm=30.0,
        )
        assert r.category == "transition"


class TestAggressiveEOR:
    """Low sigma (surfactant) pushes N_w above 1e-2."""

    def test_category(self):
        r = capillary_number(
            k_o_md=100.0, delta_p_psi=1000.0, L_ft=1000.0,
            phi=0.20, sigma_ow_dyn_cm=0.01,
        )
        assert r.N_w > 1e-2
        assert r.category == "aggressive_EOR"


class TestBelowThreshold:
    """Heavy oil with high sigma and low gradient sits below 1e-5."""

    def test_category(self):
        r = capillary_number(
            k_o_md=10.0, delta_p_psi=100.0, L_ft=5000.0,
            phi=0.20, sigma_ow_dyn_cm=30.0,
        )
        assert r.N_w < 1e-5
        assert r.category == "below_threshold"


class TestSorAfter:
    """Sor_before=0.30 at N_w ~ 1.67e-5: reduction ~0.96, so
    Sor_after ~ 0.29."""

    def test_sor_after(self):
        r = capillary_number(
            k_o_md=100.0, delta_p_psi=1000.0, L_ft=1000.0,
            phi=0.20, sigma_ow_dyn_cm=30.0, Sor_before=0.30,
        )
        assert r.sor_after is not None
        assert 0.20 < r.sor_after < 0.31

    def test_strong_reduction_at_low_sigma(self):
        r = capillary_number(
            k_o_md=100.0, delta_p_psi=1000.0, L_ft=1000.0,
            phi=0.20, sigma_ow_dyn_cm=0.01, Sor_before=0.30,
        )
        # reduction ~ 0.0 at very high Nw, so Sor_after ~ 0
        assert r.sor_after is not None
        assert r.sor_after < 0.05


class TestValidation:
    def test_k_zero(self):
        with pytest.raises(ValueError, match="k_o_md must be > 0"):
            capillary_number(0.0, 1000.0, 1000.0, 0.20, 30.0)

    def test_dp_zero(self):
        with pytest.raises(ValueError, match="delta_p_psi must be > 0"):
            capillary_number(100.0, 0.0, 1000.0, 0.20, 30.0)

    def test_L_zero(self):
        with pytest.raises(ValueError, match="L_ft must be > 0"):
            capillary_number(100.0, 1000.0, 0.0, 0.20, 30.0)

    def test_phi_out(self):
        with pytest.raises(ValueError, match="phi must be in"):
            capillary_number(100.0, 1000.0, 1000.0, 1.5, 30.0)

    def test_sigma_zero(self):
        with pytest.raises(ValueError, match="sigma_ow_dyn_cm must be > 0"):
            capillary_number(100.0, 1000.0, 1000.0, 0.20, 0.0)

    def test_Sor_before_negative(self):
        with pytest.raises(ValueError, match="Sor_before must be in"):
            capillary_number(100.0, 1000.0, 1000.0, 0.20, 30.0, -0.1)


class TestDeterminism:
    def test_repeatable(self):
        a = capillary_number(100.0, 1000.0, 1000.0, 0.20, 30.0)
        b = capillary_number(100.0, 1000.0, 1000.0, 0.20, 30.0)
        assert a.N_w == b.N_w


class TestParametrizedSigma:
    """Lower sigma increases Nw (more favorable EOR regime)."""

    @pytest.mark.parametrize("sig_pair", [(30.0, 1.0), (1.0, 0.01)])
    def test_Nw_increases(self, sig_pair):
        s1, s2 = sig_pair
        r1 = capillary_number(100.0, 1000.0, 1000.0, 0.20, s1)
        r2 = capillary_number(100.0, 1000.0, 1000.0, 0.20, s2)
        assert r2.N_w > r1.N_w
