"""Tests for backend/app/reservoir/productivity_index.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 7, Sec. 8, pp. 246-248, Eqs. (7.52)-(7.56).
"""

import pytest

from app.reservoir.productivity_index import (
    ProductivityIndexResult,
    productivity_index_empirical,
    productivity_index_theoretical,
    productivity_ratio,
)


class TestEmpirical:
    """Example 7.2 (p. 256): q=500 STB/day, pi=4000, pwf,1hr=3526.
    Empirical PI at initial drawdown uses steady-state form;
    J = 500 / (4000 - 3526) = 1.055 STB/day/psi.
    """

    def test_J(self):
        r = productivity_index_empirical(
            q_stb_d=500.0, p_avg_psia=4000.0, p_wf_psia=3526.0,
        )
        assert isinstance(r, ProductivityIndexResult)
        assert r.J_stb_per_psi == pytest.approx(500.0 / 474.0, rel=1e-12)

    def test_Js_with_h(self):
        r = productivity_index_empirical(
            q_stb_d=500.0, p_avg_psia=4000.0, p_wf_psia=3526.0,
            h_ft=20.0,
        )
        assert r.Js_stb_per_psi_ft == pytest.approx(
            500.0 / 474.0 / 20.0, rel=1e-12
        )


class TestInjectivity:
    """Injection case (Eq. 7.53): pwf > p_avg required."""

    def test_I(self):
        r = productivity_index_empirical(
            q_stb_d=200.0, p_avg_psia=2000.0, p_wf_psia=2500.0,
            injection=True,
        )
        assert r.injectivity_index == pytest.approx(200.0 / 500.0, rel=1e-12)


class TestTheoretical:
    """Example 7.2 (p. 257): k=85.1, h=20, mu=1.5, B=1.2, re=?, rw=0.333,
    S=1.04. Use r_e=660 (typical). Book reports k and S; theoretical J
    is not explicitly given but is computable.
    """

    def test_J_positive(self):
        J = productivity_index_theoretical(
            k_md=85.1, h_ft=20.0, mu_cp=1.5, B_bbl_stb=1.2,
            r_e_ft=660.0, r_w_ft=0.333, S=1.04,
        )
        assert J > 0.0

    def test_damage_reduces_J(self):
        J_virgin = productivity_index_theoretical(
            k_md=85.1, h_ft=20.0, mu_cp=1.5, B_bbl_stb=1.2,
            r_e_ft=660.0, r_w_ft=0.333, S=0.0,
        )
        J_damaged = productivity_index_theoretical(
            k_md=85.1, h_ft=20.0, mu_cp=1.5, B_bbl_stb=1.2,
            r_e_ft=660.0, r_w_ft=0.333, S=1.04,
        )
        assert J_damaged < J_virgin


class TestPR_BookExample:
    """Book p. 248: doubling borehole 8->16 in (r_w 0.333->0.667) with
    r_e=660 gives PR=1.11."""

    def test_pr(self):
        J8 = productivity_index_theoretical(
            100.0, 20.0, 1.0, 1.0, 660.0, 0.333, 0.0,
        )
        J16 = productivity_index_theoretical(
            100.0, 20.0, 1.0, 1.0, 660.0, 0.667, 0.0,
        )
        pr = productivity_ratio(J16, J8)
        assert pr == pytest.approx(1.11, rel=0.02)


class TestValidation:
    def test_no_drawdown(self):
        with pytest.raises(ValueError, match="drawdown"):
            productivity_index_empirical(
                q_stb_d=100.0, p_avg_psia=2000.0, p_wf_psia=2000.0,
            )

    def test_injection_wrong_sign(self):
        with pytest.raises(ValueError, match="injection requires"):
            productivity_index_empirical(
                q_stb_d=100.0, p_avg_psia=2000.0, p_wf_psia=1900.0,
                injection=True,
            )

    def test_h_zero(self):
        with pytest.raises(ValueError, match="h_ft must be > 0"):
            productivity_index_empirical(
                q_stb_d=100.0, p_avg_psia=2000.0, p_wf_psia=1900.0,
                h_ft=0.0,
            )

    def test_k_zero(self):
        with pytest.raises(ValueError, match="k_md must be > 0"):
            productivity_index_theoretical(
                0.0, 20.0, 1.0, 1.0, 660.0, 0.333, 0.0,
            )

    def test_r_e_le_r_w(self):
        with pytest.raises(ValueError, match="r_e_ft .* must exceed r_w_ft"):
            productivity_index_theoretical(
                100.0, 20.0, 1.0, 1.0, 0.10, 0.333, 0.0,
            )

    def test_denominator_negative(self):
        with pytest.raises(ValueError, match="ln\\(re/rw\\) - 0.75 \\+ S"):
            productivity_index_theoretical(
                100.0, 20.0, 1.0, 1.0, 1.05, 1.0, -10.0,
            )

    def test_pr_J_zero(self):
        with pytest.raises(ValueError, match="J must be > 0"):
            productivity_ratio(0.0, 1.0)


class TestDeterminism:
    def test_repeatable(self):
        a = productivity_index_empirical(
            q_stb_d=500.0, p_avg_psia=4000.0, p_wf_psia=3526.0,
        )
        b = productivity_index_empirical(
            q_stb_d=500.0, p_avg_psia=4000.0, p_wf_psia=3526.0,
        )
        assert a.J_stb_per_psi == b.J_stb_per_psi


class TestParametrizedSkin:
    """Increasing skin (positive) reduces J monotonically."""

    @pytest.mark.parametrize("S_pair", [(0.0, 1.0), (1.0, 5.0)])
    def test_J_decreases(self, S_pair):
        S1, S2 = S_pair
        J1 = productivity_index_theoretical(
            100.0, 20.0, 1.0, 1.0, 660.0, 0.333, S1,
        )
        J2 = productivity_index_theoretical(
            100.0, 20.0, 1.0, 1.0, 660.0, 0.333, S2,
        )
        assert J2 < J1
