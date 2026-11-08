"""Tests for backend/app/reservoir/layered_perm.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 7, Sec. 4.4 pp. 223-226, Sec. 4.9 pp. 229-230,
Eqs. (7.12)-(7.14), (7.24).
"""

import math
import pytest

from app.reservoir.layered_perm import (
    LayerPermResult,
    linear_parallel,
    linear_series,
    radial_parallel,
    radial_series,
)


class TestSeriesBookExample:
    """Book p. 223: k={10,50,1000}, L={6,18,40} -> 64 md.
    Tolerance 1% (book rounds to nearest md).
    """

    def test_k_avg(self):
        r = linear_series(
            k_list=[10.0, 50.0, 1000.0],
            L_list=[6.0, 18.0, 40.0],
        )
        assert isinstance(r, LayerPermResult)
        assert r.k_avg_md == pytest.approx(64.0, rel=0.01)

    def test_total_length(self):
        r = linear_series(
            k_list=[10.0, 50.0, 1000.0],
            L_list=[6.0, 18.0, 40.0],
        )
        assert r.total_length_or_thickness == 64.0


class TestParallelBookExample:
    """Book p. 224: k={10,50,1000}, h={6,18,36} -> 616 md.
    Tolerance 1%.
    """

    def test_k_avg(self):
        r = linear_parallel(
            k_list=[10.0, 50.0, 1000.0],
            h_list=[6.0, 18.0, 36.0],
        )
        assert r.k_avg_md == pytest.approx(616.0, rel=0.01)

    def test_capacity(self):
        r = linear_parallel(
            k_list=[10.0, 50.0, 1000.0],
            h_list=[6.0, 18.0, 36.0],
        )
        assert r.total_capacity_md_ft == pytest.approx(
            10.0 * 6.0 + 50.0 * 18.0 + 1000.0 * 36.0, rel=1e-12
        )


class TestRadialParallel:
    """Same as linear_parallel (book p. 229)."""

    def test_equals_linear(self):
        r_par = linear_parallel([10.0, 50.0, 1000.0], [6.0, 18.0, 36.0])
        r_rad = radial_parallel([10.0, 50.0, 1000.0], [6.0, 18.0, 36.0])
        assert r_rad.k_avg_md == r_par.k_avg_md


class TestRadialSeriesNoAlteration:
    """When k_a == k_e, Eq. 7.24 must reduce to k_e."""

    def test_identity(self):
        r = radial_series(
            k_e=100.0, k_a=100.0, r_e=660.0, r_a=10.0, r_w=0.25,
        )
        assert r.k_avg_md == pytest.approx(100.0, rel=1e-12)


class TestRadialSeriesDamage:
    """Damaged inner zone (k_a << k_e) lowers k_avg below k_e."""

    def test_damage_lowers(self):
        r = radial_series(
            k_e=100.0, k_a=1.0, r_e=660.0, r_a=10.0, r_w=0.25,
        )
        assert r.k_avg_md < 100.0
        assert r.k_avg_md > 0.0


class TestValidation:
    def test_empty_series(self):
        with pytest.raises(ValueError, match="k_list list must be non-empty"):
            linear_series([], [])

    def test_k_zero(self):
        with pytest.raises(ValueError, match="k_list\\[1\\] must be > 0"):
            linear_series([10.0, 0.0], [6.0, 18.0])

    def test_length_mismatch(self):
        with pytest.raises(ValueError, match="same length"):
            linear_series([10.0, 50.0], [6.0])

    def test_L_negative(self):
        with pytest.raises(ValueError, match="L_list\\[0\\] must be > 0"):
            linear_series([10.0], [-6.0])

    def test_radial_ordering(self):
        with pytest.raises(ValueError, match="radial ordering"):
            radial_series(
                k_e=100.0, k_a=50.0, r_e=100.0, r_a=200.0, r_w=0.25,
            )

    def test_radial_k_negative(self):
        with pytest.raises(ValueError, match="k_e must be > 0"):
            radial_series(
                k_e=-1.0, k_a=50.0, r_e=660.0, r_a=10.0, r_w=0.25,
            )


class TestDeterminism:
    def test_repeatable(self):
        a = linear_series([10.0, 50.0, 1000.0], [6.0, 18.0, 40.0])
        b = linear_series([10.0, 50.0, 1000.0], [6.0, 18.0, 40.0])
        assert a.k_avg_md == b.k_avg_md


class TestParametrizedThickness:
    """Adding a zero-thickness layer would keep k_avg the same (skipped
    here since zero thickness rejected). Adding a thick, low-k layer
    should decrease k_avg in parallel."""

    @pytest.mark.parametrize(
        "extra_h", [10.0, 50.0, 100.0]
    )
    def test_low_k_thick_layer_lowers_avg(self, extra_h):
        base = linear_parallel([100.0, 100.0], [10.0, 10.0])
        with_extra = linear_parallel(
            [100.0, 100.0, 10.0], [10.0, 10.0, extra_h]
        )
        assert with_extra.k_avg_md < base.k_avg_md
