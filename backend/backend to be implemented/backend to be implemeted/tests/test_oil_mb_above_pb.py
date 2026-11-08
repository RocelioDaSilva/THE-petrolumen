"""Tests for backend/app/reservoir/oil_mb_above_pb.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 5, Sec. 6, pp. 170-176, Eqs. (5.21)-(5.28),
Example 5.3 (p. 172).
"""

import pytest

from app.reservoir.oil_mb_above_pb import (
    OilMBAbovePbResult,
    effective_compressibility,
    oil_mb_above_pb,
)


class TestExample53:
    """Example 5.3 (p. 172): N = 51.73 MM STB with compressibilities,
    N = 86.25 MM STB without. Tolerance 1% relative on each.
    """

    def test_with_comps(self):
        r = oil_mb_above_pb(
            Np_stb=1.25e6, Bt=1.37500, Bti=1.35469,
            Swi=0.20, cw=3.6e-6, cf=5.0e-6, delta_p=1400.0,
            We=0.0, Wp=32000.0, Bw=1.04,
        )
        assert isinstance(r, OilMBAbovePbResult)
        assert r.n_stb / 1.0e6 == pytest.approx(51.73, rel=0.01)

    def test_without_comps(self):
        r = oil_mb_above_pb(
            Np_stb=1.25e6, Bt=1.37500, Bti=1.35469,
            Swi=0.20, cw=0.0, cf=0.0, delta_p=1400.0,
            We=0.0, Wp=32000.0, Bw=1.04,
        )
        assert r.n_stb / 1.0e6 == pytest.approx(86.25, rel=0.01)


class TestEffectiveCompressibility:
    """Example 5.3 p. 172: ce = 17.86e-6 psi^-1."""

    def test_ce_value(self):
        ce = effective_compressibility(
            So=0.80, Swi=0.20, co=10.71e-6, cw=3.6e-6, cf=5.0e-6,
        )
        assert ce == pytest.approx(17.86e-6, rel=0.02)


class TestCeEcho:
    """When co and So supplied, ce is included in result."""

    def test_ce_present(self):
        r = oil_mb_above_pb(
            Np_stb=1.25e6, Bt=1.37500, Bti=1.35469,
            Swi=0.20, cw=3.6e-6, cf=5.0e-6, delta_p=1400.0,
            We=0.0, Wp=32000.0, Bw=1.04,
            co=10.71e-6, So=0.80,
        )
        assert r.ce_psi_inv is not None
        assert r.ce_psi_inv == pytest.approx(17.86e-6, rel=0.02)


class TestValidation:
    def _ok(self) -> dict:
        return dict(
            Np_stb=1.25e6, Bt=1.375, Bti=1.35469,
            Swi=0.20, cw=3.6e-6, cf=5.0e-6, delta_p=1400.0,
            We=0.0, Wp=0.0, Bw=1.0,
        )

    def test_Np_negative(self):
        kw = self._ok(); kw["Np_stb"] = -1.0
        with pytest.raises(ValueError, match="Np_stb must be >= 0"):
            oil_mb_above_pb(**kw)

    def test_Bt_less_than_Bti(self):
        kw = self._ok(); kw["Bt"] = 1.30
        with pytest.raises(ValueError, match="below bubble"):
            oil_mb_above_pb(**kw)

    def test_Swi_one(self):
        kw = self._ok(); kw["Swi"] = 1.0
        with pytest.raises(ValueError, match="Swi must be in"):
            oil_mb_above_pb(**kw)

    def test_delta_p_negative(self):
        kw = self._ok(); kw["delta_p"] = -100.0
        with pytest.raises(ValueError, match="delta_p must be >= 0"):
            oil_mb_above_pb(**kw)

    def test_We_negative(self):
        kw = self._ok(); kw["We"] = -1.0
        with pytest.raises(ValueError, match="We must be >= 0"):
            oil_mb_above_pb(**kw)

    def test_co_without_So(self):
        kw = self._ok(); kw["co"] = 10e-6
        with pytest.raises(ValueError, match="both co and So"):
            oil_mb_above_pb(**kw)

    def test_ce_So_plus_Swi_gt_one(self):
        with pytest.raises(ValueError, match="So \\+ Swi"):
            effective_compressibility(
                So=0.85, Swi=0.20, co=10e-6, cw=3e-6, cf=5e-6,
            )


class TestDeterminism:
    def test_repeatable(self):
        a = oil_mb_above_pb(
            1.25e6, 1.375, 1.35469, 0.20, 3.6e-6, 5.0e-6, 1400.0,
        )
        b = oil_mb_above_pb(
            1.25e6, 1.375, 1.35469, 0.20, 3.6e-6, 5.0e-6, 1400.0,
        )
        assert a.n_stb == b.n_stb


class TestParametrizedComp:
    """Increasing compressibility lowers N (denominator grows)."""

    @pytest.mark.parametrize("cf_pair", [(0.0, 5.0e-6), (5.0e-6, 1.0e-5)])
    def test_N_decreases(self, cf_pair):
        cf1, cf2 = cf_pair
        r1 = oil_mb_above_pb(
            1.25e6, 1.375, 1.35469, 0.20, 3.6e-6, cf1, 1400.0,
        )
        r2 = oil_mb_above_pb(
            1.25e6, 1.375, 1.35469, 0.20, 3.6e-6, cf2, 1400.0,
        )
        assert r2.n_stb < r1.n_stb
