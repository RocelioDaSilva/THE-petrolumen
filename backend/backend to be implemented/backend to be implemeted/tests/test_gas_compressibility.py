"""Tests for backend/app/reservoir/gas_compressibility.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 1, Sec. 5.5, pp. 24-26, Eq. (1.19) and Ex. 1.4.
"""

import pytest

from app.reservoir.gas_compressibility import (
    GasCompressibilityResult,
    gas_compressibility,
    gas_compressibility_from_z_curve,
)


class TestIdealGas:
    """Ideal gas: z(p)=1, dz/dp=0, so cg = 1/p exactly."""

    def test_1000_psia(self):
        r = gas_compressibility_from_z_curve(
            p_psia=1000.0, z_func=lambda p: 1.0,
        )
        assert isinstance(r, GasCompressibilityResult)
        assert r.cg_psi_inv == pytest.approx(1.0e-3, rel=1e-10)
        assert r.z_at_p == 1.0
        assert abs(r.dz_dp_psi_inv) < 1e-10


class TestLinearZ:
    """z(p) = 1 + a*p => analytic cg = 1/p - a/(1+a*p)."""

    def test_2000_psia(self):
        a = 1.0e-4
        p = 2000.0
        r = gas_compressibility_from_z_curve(
            p_psia=p, z_func=lambda pp: 1.0 + a * pp,
        )
        expected = 1.0 / p - a / (1.0 + a * p)
        assert r.cg_psi_inv == pytest.approx(expected, rel=1e-3)
        assert r.z_at_p == pytest.approx(1.0 + a * p, rel=1e-12)
        assert r.dz_dp_psi_inv == pytest.approx(a, rel=1e-6)


class TestBookExample14:
    """Book Example 1.4 (p. 24): sg=0.90 gas at 150 F, cg values.

    Fig. 1.6 gives dz/dp = 110e-6 psi^-1 at 4500 psia (graphically).
    Tolerance 50%: covers (a) DAK vs Standing-Katz z-correlation
    difference, (b) slope read from a graph.
    """

    @pytest.mark.parametrize(
        "p_psia,expected_cg",
        [
            (1000.0, 1153.0e-6),
            (2500.0, 400.0e-6),
            (4500.0, 100.0e-6),
        ],
    )
    def test_example14(self, p_psia, expected_cg):
        r = gas_compressibility(p_psia=p_psia, T_F=150.0, gas_sg=0.90)
        assert r.cg_psi_inv == pytest.approx(expected_cg, rel=0.5)


class TestValidation:
    def test_p_zero(self):
        with pytest.raises(ValueError, match="p_psia must be > 0"):
            gas_compressibility_from_z_curve(0.0, lambda p: 1.0)

    def test_p_negative(self):
        with pytest.raises(ValueError, match="p_psia must be > 0"):
            gas_compressibility_from_z_curve(-1.0, lambda p: 1.0)

    def test_T_below_abs_zero(self):
        with pytest.raises(ValueError, match="T_F must be above"):
            gas_compressibility(p_psia=1000.0, T_F=-500.0, gas_sg=0.7)

    def test_gas_sg_zero(self):
        with pytest.raises(ValueError, match="gas_sg must be in"):
            gas_compressibility(p_psia=1000.0, T_F=150.0, gas_sg=0.0)

    def test_gas_sg_too_high(self):
        with pytest.raises(ValueError, match="gas_sg must be in"):
            gas_compressibility(p_psia=1000.0, T_F=150.0, gas_sg=2.5)

    def test_z_nonpositive(self):
        with pytest.raises(ValueError, match="z at p must be > 0"):
            gas_compressibility_from_z_curve(
                p_psia=1000.0, z_func=lambda p: 0.0,
            )

    def test_h_negative(self):
        with pytest.raises(ValueError, match="h_psi must be > 0"):
            gas_compressibility_from_z_curve(
                p_psia=1000.0, z_func=lambda p: 1.0, h_psi=-1.0,
            )


class TestNonConvergence:
    """If z_func raises (e.g. z-factor iteration diverges), the exception
    propagates unchanged so the API layer can map it to HTTP 500."""

    def test_z_func_raises(self):
        def bad_z(p: float) -> float:
            raise RuntimeError("z-factor diverged")
        with pytest.raises(RuntimeError, match="z-factor diverged"):
            gas_compressibility_from_z_curve(1000.0, bad_z)


class TestNearZeroPressure:
    """p < h must trigger forward-difference fallback, not error."""

    def test_forward_difference_branch(self):
        # p=0.1, h=ABS_STEP_PSI=0.5 => p-h<0 => forward branch
        r = gas_compressibility_from_z_curve(
            p_psia=0.1, z_func=lambda p: 1.0,
        )
        assert r.cg_psi_inv == pytest.approx(1.0 / 0.1, rel=1e-6)


class TestDeterminism:
    def test_repeatable(self):
        a = gas_compressibility(4500.0, 150.0, 0.90)
        b = gas_compressibility(4500.0, 150.0, 0.90)
        assert a.cg_psi_inv == b.cg_psi_inv
        assert a.dz_dp_psi_inv == b.dz_dp_psi_inv
