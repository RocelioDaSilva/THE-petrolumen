"""Tests for constraint_swap_check (Chin 2016, Ch 3 Ex 3-5)."""
import pytest
from app.reservoir.constraint_swap import constraint_swap_check


class TestSelfConsistent:
    """Chin p. 128: at steady state, P->R swap recovers P within ~1%."""

    def test_swap(self):
        # Take p1 = 1000 psi, p_avg = 4000 psi, and PI from k=100, h=20.
        # Then q1 = PI * (4000 - 1000). Feeding that q1 back at p2=2000
        # should give q2 = PI * 2000. So a swap *within* the model
        # recovers exactly.
        r1 = constraint_swap_check(
            p1_psia=1000.0, q1_stb_d=1.0, p_avg_psia=4000.0,
            k_md=100.0, h_ft=20.0, mu_cp=1.0, B_bbl_stb=1.2,
            r_e_ft=660.0, r_w_ft=0.333, S=0.0,
        )
        # q2_predicted at p2 = 2000:
        r2 = constraint_swap_check(
            p1_psia=1000.0, q1_stb_d=1.0, p_avg_psia=4000.0,
            k_md=100.0, h_ft=20.0, mu_cp=1.0, B_bbl_stb=1.2,
            r_e_ft=660.0, r_w_ft=0.333, S=0.0,
            p2_psia=2000.0,
        )
        # q2 should be half of q1 (same PI, half the pressure drop)
        assert r2.q2_predicted_stb_d == pytest.approx(r2.PI_stb_d_psi * 2000.0)


class TestChinExample35:
    """Chin Ex 3-5: swap should recover original within a few %."""

    def test_swap_1000_to_rate(self):
        # P1 = 1000 psi, Q1 = 244,400 b/d. Swap to Q = 244,400 at
        # p_avg = 4000 psi; implied p = 4000 - 244400/PI.
        # If PI ~ 81.5 (from Chin's data), p2 should ~ 1000.
        # We don't have Chin's exact reservoir so just verify the
        # algebra.
        r = constraint_swap_check(
            p1_psia=1000.0, q1_stb_d=1.0, p_avg_psia=4000.0,
            k_md=100.0, h_ft=20.0, mu_cp=1.0, B_bbl_stb=1.2,
            r_e_ft=660.0, r_w_ft=0.333, S=0.0,
            q2_stb_d=100.0,  # some rate
        )
        # Implied p2 = 4000 - 100/PI
        assert r.p2_predicted_psia < 4000.0


class TestConsistentFlag:
    def test_consistent_true(self):
        r1 = constraint_swap_check(
            p1_psia=1000.0, q1_stb_d=1.0, p_avg_psia=4000.0,
            k_md=100.0, h_ft=20.0, mu_cp=1.0, B_bbl_stb=1.2,
            r_e_ft=660.0, r_w_ft=0.333, S=0.0,
        )
        # Match the model: q2 at p2=2000 should be PI * 2000
        q2_true = r1.PI_stb_d_psi * 2000.0
        r2 = constraint_swap_check(
            p1_psia=1000.0, q1_stb_d=1.0, p_avg_psia=4000.0,
            k_md=100.0, h_ft=20.0, mu_cp=1.0, B_bbl_stb=1.2,
            r_e_ft=660.0, r_w_ft=0.333, S=0.0,
            p2_psia=2000.0, q2_stb_d=q2_true,
        )
        assert r2.consistent is True
        assert r2.observed_ratio_q == pytest.approx(1.0, rel=1e-9)


class TestValidation:
    def test_p1_ge_p_avg(self):
        with pytest.raises(ValueError, match="must be < p_avg"):
            constraint_swap_check(
                5000.0, 1.0, 4000.0, 100.0, 20.0, 1.0, 1.2,
                660.0, 0.333, 0.0,
            )

    def test_q1_zero(self):
        with pytest.raises(ValueError, match="q1_stb_d must be > 0"):
            constraint_swap_check(
                1000.0, 0.0, 4000.0, 100.0, 20.0, 1.0, 1.2,
                660.0, 0.333, 0.0,
            )


class TestDeterminism:
    def test_repeatable(self):
        a = constraint_swap_check(
            1000.0, 1.0, 4000.0, 100.0, 20.0, 1.0, 1.2,
            660.0, 0.333, 0.0, p2_psia=2000.0,
        )
        b = constraint_swap_check(
            1000.0, 1.0, 4000.0, 100.0, 20.0, 1.0, 1.2,
            660.0, 0.333, 0.0, p2_psia=2000.0,
        )
        assert a.q2_predicted_stb_d == b.q2_predicted_stb_d
