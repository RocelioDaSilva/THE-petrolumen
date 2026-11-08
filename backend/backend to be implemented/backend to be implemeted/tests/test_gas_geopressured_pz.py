"""Tests for backend/app/reservoir/gas_geopressured_pz.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 3, Sec. 8, pp. 97-99, Eq. (3.26).
No numeric example in book; use synthetic exact construction.
"""

import math
import pytest

from app.reservoir.gas_geopressured_pz import (
    GeopressuredPZPoint,
    GeopressuredPZResult,
    geopressured_pz,
)


def _make_point(pi: float, zi: float, G: float, C: float,
                Gp: float) -> GeopressuredPZPoint:
    """Construct a point exactly on Eq. (3.26) for given (G, C')."""
    pi_over_zi = pi / zi
    pz = (pi_over_zi - pi_over_zi * Gp / G) / (1.0 - C * Gp / G)
    # Solve p from p/z: we want pz = p/z so p = pz*z; choose z at random
    # to keep it decoupled from the model.
    # We'll pick p to satisfy pi - p = pressure drop; invert from pz:
    # Choose a realistic z sequence (roughly constant for simplicity)
    z = 0.9
    p = pz * z
    return GeopressuredPZPoint(p_psia=p, Gp_scf=Gp, z=z)


class TestSyntheticExact:
    """Construct 4 points exactly on Eq. (3.26) with G=50e9, C'=5e-5;
    recovered G and C' must equal input."""

    def _pts(self) -> list[GeopressuredPZPoint]:
        pi, zi, G, C = 8000.0, 1.10, 50.0e9, 5.0e-5
        # Choose Gp values that keep 1 - C*dp sane
        return [
            _make_point(pi, zi, G, C, 2.0e9),
            _make_point(pi, zi, G, C, 8.0e9),
            _make_point(pi, zi, G, C, 15.0e9),
            _make_point(pi, zi, G, C, 22.0e9),
        ]

    def test_g_initial(self):
        r = geopressured_pz(self._pts())
        assert isinstance(r, GeopressuredPZResult)
        assert r.g_initial_scf / 1.0e9 == pytest.approx(50.0, rel=0.01)

    def test_c_prime(self):
        r = geopressured_pz(self._pts())
        assert r.c_prime_psi_inv == pytest.approx(5.0e-5, rel=0.05)

    def test_residuals_small(self):
        r = geopressured_pz(self._pts())
        for res in r.residuals:
            assert abs(res) < 100.0


class TestNormalReservoir:
    """With C'=0, Eq. (3.26) reduces to the normal p/z line; the fit
    should return C' approximately 0 and G matching the normal fit."""

    def _pts(self) -> list[GeopressuredPZPoint]:
        pi, zi, G, C = 5000.0, 0.90, 20.0e9, 0.0
        return [
            _make_point(pi, zi, G, C, 2.0e9),
            _make_point(pi, zi, G, C, 8.0e9),
            _make_point(pi, zi, G, C, 14.0e9),
        ]

    def test_g_initial_matches(self):
        r = geopressured_pz(self._pts())
        assert r.g_initial_scf / 1.0e9 == pytest.approx(20.0, rel=0.02)

    def test_c_prime_near_zero(self):
        r = geopressured_pz(self._pts())
        assert abs(r.c_prime_psi_inv) < 1.0e-6

    def test_likely_normal_flag(self):
        r = geopressured_pz(self._pts())
        assert r.likely_normal is True


class TestValidation:
    def _pt(self, p: float = 7000.0, Gp: float = 1.0e9,
            z: float = 1.0) -> GeopressuredPZPoint:
        return GeopressuredPZPoint(p_psia=p, Gp_scf=Gp, z=z)

    def test_fewer_than_three(self):
        with pytest.raises(ValueError, match="At least 3 points"):
            geopressured_pz([self._pt(), self._pt(Gp=2.0e9)])

    def test_p_zero(self):
        with pytest.raises(ValueError, match="p_psia must be > 0"):
            geopressured_pz([
                self._pt(p=0.0), self._pt(Gp=2.0e9), self._pt(Gp=3.0e9),
            ])

    def test_Gp_negative(self):
        with pytest.raises(ValueError, match="Gp_scf must be >= 0"):
            geopressured_pz([
                self._pt(Gp=-1.0), self._pt(Gp=2.0e9), self._pt(Gp=3.0e9),
            ])

    def test_z_zero(self):
        with pytest.raises(ValueError, match="z must be > 0"):
            geopressured_pz([
                self._pt(z=0.0), self._pt(Gp=2.0e9), self._pt(Gp=3.0e9),
            ])

    def test_pressure_drop_zero(self):
        # pi defaults to first point's p = 7000; subsequent p = 7000
        # means dp = 0
        with pytest.raises(ValueError, match="positive pressure drop"):
            geopressured_pz([
                self._pt(p=7000.0), self._pt(p=7000.0, Gp=2.0e9),
                self._pt(p=7000.0, Gp=3.0e9),
            ])

    def test_pi_zero_override(self):
        with pytest.raises(ValueError, match="pi_psia must be > 0"):
            geopressured_pz(
                [self._pt(), self._pt(Gp=2.0e9), self._pt(Gp=3.0e9)],
                pi_psia=0.0,
            )


class TestNumericRegression:
    def test_fixed_input(self):
        # Fixed data generated from G=30e9, C'=3e-5, pi=6000, zi=1.0
        pts = [
            _make_point(6000.0, 1.0, 30.0e9, 3.0e-5, 1.0e9),
            _make_point(6000.0, 1.0, 30.0e9, 3.0e-5, 5.0e9),
            _make_point(6000.0, 1.0, 30.0e9, 3.0e-5, 10.0e9),
        ]
        r = geopressured_pz(pts)
        assert r.g_initial_scf / 1.0e9 == pytest.approx(30.0, rel=0.02)


class TestParametrizedC:
    """C' should scale linearly with the injected correction coefficient."""

    @pytest.mark.parametrize("c_val", [1.0e-5, 3.0e-5, 5.0e-5])
    def test_c_scales(self, c_val):
        pi, zi, G = 7000.0, 1.05, 40.0e9
        pts = [
            _make_point(pi, zi, G, c_val, 2.0e9),
            _make_point(pi, zi, G, c_val, 8.0e9),
            _make_point(pi, zi, G, c_val, 15.0e9),
        ]
        r = geopressured_pz(pts)
        assert r.c_prime_psi_inv == pytest.approx(c_val, rel=0.10)
