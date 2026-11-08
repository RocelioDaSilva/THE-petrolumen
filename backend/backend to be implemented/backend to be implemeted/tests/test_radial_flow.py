"""Tests for backend/app/reservoir/radial_flow.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 7, Sec. 4.6-4.8, pp. 226-229,
Eqs. (7.19)-(7.22).
"""

import math
import pytest

from app.reservoir.radial_flow import (
    RadialFlowResult,
    radial_flow_gas_high_p,
    radial_flow_gas_low_p,
    radial_flow_incompressible,
    radial_flow_slightly_compressible,
)


class TestIncompressibleHandCheck:
    """Hand check: k=100, h=15, pe=3000, pw=2000, mu=1, B=1, re=660,
    rw=0.25. Book factor: 0.00708*100*15*1000/(1*1*ln(2640)).
    """

    def test_q(self):
        r = radial_flow_incompressible(
            k=100.0, h=15.0, p_e=3000.0, p_w=2000.0,
            mu=1.0, B=1.0, r_e=660.0, r_w=0.25,
        )
        expected = 0.00708 * 100.0 * 15.0 * 1000.0 / math.log(660.0 / 0.25)
        assert isinstance(r, RadialFlowResult)
        assert r.q == pytest.approx(expected, rel=1e-12)
        assert r.form == "incompressible"


class TestSlightlyCompressible:
    def test_reduces_to_incompressible_at_small_c(self):
        # Very small c should approach the incompressible result
        r_inc = radial_flow_incompressible(
            k=100.0, h=15.0, p_e=3000.0, p_w=2000.0,
            mu=1.0, B=1.0, r_e=660.0, r_w=0.25,
        )
        r_sc = radial_flow_slightly_compressible(
            k=100.0, h=15.0, p_e=3000.0, p_w=2000.0, pR=2500.0,
            mu=1.0, c=1e-10, r_e=660.0, r_w=0.25,
        )
        assert r_sc.q == pytest.approx(r_inc.q, rel=0.01)


class TestGasLowP:
    """Low-pressure gas radial form consistency with the linear form."""

    def test_q_positive(self):
        r = radial_flow_gas_low_p(
            k=50.0, h=30.0, p_e=2000.0, p_w=1500.0,
            T_sc=520.0, p_sc=14.7, T=620.0, z=0.85, mu=0.02,
            r_e=660.0, r_w=0.25,
        )
        assert r.q > 0.0
        assert r.form == "gas_low_p"


class TestGasHighP:
    def test_q_positive(self):
        r = radial_flow_gas_high_p(
            k=50.0, h=30.0, p_e=5000.0, p_w=4500.0,
            T_sc=520.0, p_sc=14.7, T=680.0, mu_z_over_p=0.003,
            r_e=660.0, r_w=0.25,
        )
        assert r.q > 0.0
        assert r.form == "gas_high_p"


class TestValidation:
    def _ok_inc(self) -> dict:
        return dict(
            k=100.0, h=15.0, p_e=3000.0, p_w=2000.0,
            mu=1.0, B=1.0, r_e=660.0, r_w=0.25,
        )

    def test_k_zero(self):
        kw = self._ok_inc(); kw["k"] = 0.0
        with pytest.raises(ValueError, match="k must be > 0"):
            radial_flow_incompressible(**kw)

    def test_pe_le_pw(self):
        kw = self._ok_inc(); kw["p_e"] = 1000.0; kw["p_w"] = 2000.0
        with pytest.raises(ValueError, match="p_e .* must exceed p_w"):
            radial_flow_incompressible(**kw)

    def test_re_le_rw(self):
        kw = self._ok_inc(); kw["r_e"] = 0.10; kw["r_w"] = 0.25
        with pytest.raises(ValueError, match="r_e .* must exceed r_w"):
            radial_flow_incompressible(**kw)

    def test_gas_z_zero(self):
        with pytest.raises(ValueError, match="z must be > 0"):
            radial_flow_gas_low_p(
                50.0, 30.0, 2000.0, 1500.0, 520.0, 14.7,
                620.0, 0.0, 0.02, 660.0, 0.25,
            )

    def test_gas_mu_z_p_zero(self):
        with pytest.raises(ValueError, match="mu_z_over_p must be > 0"):
            radial_flow_gas_high_p(
                50.0, 30.0, 5000.0, 4500.0, 520.0, 14.7,
                680.0, 0.0, 660.0, 0.25,
            )


class TestReRatio:
    """ln_re_over_rw should equal log(re/rw)."""

    def test_value(self):
        r = radial_flow_incompressible(
            100.0, 15.0, 3000.0, 2000.0, 1.0, 1.0, 660.0, 0.25,
        )
        assert r.ln_re_over_rw == pytest.approx(math.log(660.0 / 0.25), rel=1e-12)


class TestDeterminism:
    def test_repeatable(self):
        a = radial_flow_incompressible(
            100.0, 15.0, 3000.0, 2000.0, 1.0, 1.0, 660.0, 0.25,
        )
        b = radial_flow_incompressible(
            100.0, 15.0, 3000.0, 2000.0, 1.0, 1.0, 660.0, 0.25,
        )
        assert a.q == b.q


class TestParametrizedRe:
    """Larger re (lower ln ratio effect) should reduce q."""

    @pytest.mark.parametrize("re_pair", [(1000.0, 2000.0)])
    def test_q_decreases(self, re_pair):
        re1, re2 = re_pair
        r1 = radial_flow_incompressible(
            100.0, 15.0, 3000.0, 2000.0, 1.0, 1.0, re1, 0.25,
        )
        r2 = radial_flow_incompressible(
            100.0, 15.0, 3000.0, 2000.0, 1.0, 1.0, re2, 0.25,
        )
        assert r2.q < r1.q
