"""Tests for backend/app/reservoir/fetkovich_influx.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 8, Sec. 4, pp. 325-328, Eqs. (8.15)-(8.21),
Table 8.11, Example 8.5.
"""

import math
import pytest

from app.reservoir.fetkovich_influx import (
    FetkovichResult,
    fetkovich_productivity_index,
    fetkovich_water_influx,
)


class TestExample85_J:
    """Example 8.5: k=275, h=19.2, mu=0.25, r_e=83263, r_R=5807,
    theta=180, no_flow boundary. Book J=39.08 bbl/day/psi.
    Tolerance 1%.
    """

    def test_J(self):
        J = fetkovich_productivity_index(
            k_md=275.0, h_ft=19.2, mu_cp=0.25,
            r_e_ft=83263.0, r_R_ft=5807.0,
            theta_deg=180.0, outer_boundary="no_flow",
        )
        assert J == pytest.approx(39.08, rel=0.01)


class TestJConstantPressure:
    """Constant-pressure outer boundary has no -0.75 offset => higher J."""

    def test_higher_J(self):
        J_nf = fetkovich_productivity_index(
            275.0, 19.2, 0.25, 83263.0, 5807.0, 180.0, "no_flow",
        )
        J_cp = fetkovich_productivity_index(
            275.0, 19.2, 0.25, 83263.0, 5807.0, 180.0,
            "constant_pressure",
        )
        assert J_cp > J_nf


class TestInfluxFirstStep:
    """Example 8.5 quarter 2: p_R=3788, previous 3793. Book dWe=8,600.
    We use only 2-step history (3793, then 3788) so q matches book
    quarter 2 exactly.
    """

    def test_step2(self):
        r = fetkovich_water_influx(
            W_ei_bbl=176.3e6, p_i_psia=3793.0, J_bpd_psi=39.08,
            p_history=[(0.0, 3793.0), (91.3, 3793.0), (182.6, 3788.0)],
        )
        assert isinstance(r, FetkovichResult)
        assert r.delta_we_per_step_bbl[2] == pytest.approx(8600.0, rel=0.05)


class TestNoInfluxIfPressureConstant:
    """If p_R never drops, W_e stays zero."""

    def test_zero(self):
        r = fetkovich_water_influx(
            176.3e6, 3793.0, 39.08,
            [(0.0, 3793.0), (91.3, 3793.0), (182.6, 3793.0)],
        )
        assert r.we_cumulative_bbl == pytest.approx(0.0, abs=1e-6)
        assert r.delta_we_per_step_bbl[1] == pytest.approx(0.0, abs=1e-6)


class TestMonotonic:
    """Cumulative W_e increases with each pressure drop."""

    def test_monotone(self):
        r = fetkovich_water_influx(
            176.3e6, 3793.0, 39.08,
            [(0.0, 3793.0), (91.3, 3788.0), (182.6, 3781.0),
             (273.9, 3774.0)],
        )
        for i in range(2, len(r.we_at_points_bbl)):
            assert r.we_at_points_bbl[i] >= r.we_at_points_bbl[i-1]


class TestPbarDecreasing:
    """Aquifer average pressure decreases as W_e accumulates."""

    def test_pbar(self):
        r = fetkovich_water_influx(
            176.3e6, 3793.0, 39.08,
            [(0.0, 3793.0), (91.3, 3788.0), (182.6, 3781.0),
             (273.9, 3774.0), (365.2, 3748.0)],
        )
        # First entry is p_i, subsequent are decreasing
        assert r.pbar_per_step_psia[0] == pytest.approx(3793.0, rel=1e-9)
        for i in range(2, len(r.pbar_per_step_psia)):
            assert (r.pbar_per_step_psia[i]
                    < r.pbar_per_step_psia[i-1] + 1e-6)


class TestJValidation:
    def test_r_e_le_r_R(self):
        with pytest.raises(ValueError, match="r_e_ft .* must exceed r_R_ft"):
            fetkovich_productivity_index(
                275.0, 19.2, 0.25, 5000.0, 5807.0, 180.0, "no_flow",
            )

    def test_theta_zero(self):
        with pytest.raises(ValueError, match="theta_deg must be in"):
            fetkovich_productivity_index(
                275.0, 19.2, 0.25, 83263.0, 5807.0, 0.0, "no_flow",
            )

    def test_bad_boundary(self):
        with pytest.raises(ValueError, match="outer_boundary must be"):
            fetkovich_productivity_index(
                275.0, 19.2, 0.25, 83263.0, 5807.0, 180.0, "sideways",
            )

    def test_r_e_too_small(self):
        # r_e/r_R = 2.0, ln(2)-0.75 = -0.057 -> negative
        with pytest.raises(ValueError, match="ln\\(r_e/r_R\\) - 0.75"):
            fetkovich_productivity_index(
                275.0, 19.2, 0.25, 11614.0, 5807.0, 180.0, "no_flow",
            )


class TestInfluxValidation:
    def test_Wei_zero(self):
        with pytest.raises(ValueError, match="W_ei_bbl must be > 0"):
            fetkovich_water_influx(
                0.0, 3793.0, 39.08,
                [(0.0, 3793.0), (91.3, 3788.0)],
            )

    def test_p_i_zero(self):
        with pytest.raises(ValueError, match="p_i_psia must be > 0"):
            fetkovich_water_influx(
                176.3e6, 0.0, 39.08,
                [(0.0, 3793.0), (91.3, 3788.0)],
            )

    def test_J_zero(self):
        with pytest.raises(ValueError, match="J_bpd_psi must be > 0"):
            fetkovich_water_influx(
                176.3e6, 3793.0, 0.0,
                [(0.0, 3793.0), (91.3, 3788.0)],
            )

    def test_history_too_short(self):
        with pytest.raises(ValueError, match=">= 2 points"):
            fetkovich_water_influx(
                176.3e6, 3793.0, 39.08, [(0.0, 3793.0)],
            )

    def test_p_R_exceeds_p_i(self):
        with pytest.raises(ValueError, match="exceeds p_i_psia"):
            fetkovich_water_influx(
                176.3e6, 3793.0, 39.08,
                [(0.0, 3793.0), (91.3, 4000.0)],
            )

    def test_times_not_increasing(self):
        with pytest.raises(ValueError, match="strictly increasing"):
            fetkovich_water_influx(
                176.3e6, 3793.0, 39.08,
                [(0.0, 3793.0), (91.3, 3793.0), (50.0, 3788.0)],
            )


class TestDeterminism:
    def test_repeatable(self):
        a = fetkovich_water_influx(
            176.3e6, 3793.0, 39.08,
            [(0.0, 3793.0), (91.3, 3788.0), (182.6, 3781.0)],
        )
        b = fetkovich_water_influx(
            176.3e6, 3793.0, 39.08,
            [(0.0, 3793.0), (91.3, 3788.0), (182.6, 3781.0)],
        )
        assert a.we_cumulative_bbl == b.we_cumulative_bbl


class TestParametrizedTheta:
    """Larger theta (more contact) -> larger J."""

    @pytest.mark.parametrize("theta_pair", [(90.0, 180.0), (180.0, 270.0)])
    def test_J_increases(self, theta_pair):
        t1, t2 = theta_pair
        J1 = fetkovich_productivity_index(
            275.0, 19.2, 0.25, 83263.0, 5807.0, t1, "no_flow",
        )
        J2 = fetkovich_productivity_index(
            275.0, 19.2, 0.25, 83263.0, 5807.0, t2, "no_flow",
        )
        assert J2 > J1
