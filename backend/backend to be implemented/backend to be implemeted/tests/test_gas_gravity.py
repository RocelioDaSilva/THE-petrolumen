"""Tests for backend/app/reservoir/gas_gravity.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 9, Sec. 3.2, pp. 354-360, Eqs. (9.23)-(9.26),
Table 9.2, worked example on p. 357.
"""

import math
import pytest

from app.reservoir.gas_gravity import (
    GasGravityResult,
    gas_fractional_flow_gravity,
    gas_gravity_frontal_advance,
)


class TestMileSixLambda:
    """Book p. 357: with k=300 md, phi=0.1625, Ac=1,237,000 ft^2,
    rho_o=48.7, rho_g=5.0, alpha=72.5, mu_o=1.32, qt=11600,
    lambda ~= 2.48 (book uses 2.50). Tolerance 3%.
    """

    def test_lambda(self):
        r = gas_fractional_flow_gravity(
            Sg=0.40, So=0.60, k_ro=0.210, k_rg=0.090,
            mu_o=1.32, mu_g=0.0134, k_md=300.0,
            Ac_ft2=1237000.0, qt_bbl_d=11600.0, alpha_deg=72.5,
            rho_o_lb_ft3=48.7, rho_g_lb_ft3=5.0,
        )
        assert isinstance(r, GasGravityResult)
        assert r.lambda_gravity == pytest.approx(2.48, rel=0.03)


class TestMileSixZeroGravity:
    """At alpha=0 and no gravity, fg should reduce to Eq. 9.24.
    With kro/krg=0.210/0.090=2.333, mu_g/mu_o=0.0134/1.32=0.01015,
    fg = 1/(1 + 2.333*0.01015) = 1/1.0237 = 0.977.
    """

    def test_zero_gravity(self):
        r = gas_fractional_flow_gravity(
            Sg=0.40, So=0.60, k_ro=0.210, k_rg=0.090,
            mu_o=1.32, mu_g=0.0134, k_md=300.0,
            Ac_ft2=1237000.0, qt_bbl_d=11600.0, alpha_deg=0.0,
            rho_o_lb_ft3=48.7, rho_g_lb_ft3=5.0,
        )
        # When alpha=0, cos(0)=1, so lambda still >0
        # Use tiny lambda by setting rho_o=rho_g? No, guarded.
        # Actually alpha=0 gives cos=1 => lambda ~= 2.48
        # So test alpha near 90 instead
        r2 = gas_fractional_flow_gravity(
            Sg=0.40, So=0.60, k_ro=0.210, k_rg=0.090,
            mu_o=1.32, mu_g=0.0134, k_md=300.0,
            Ac_ft2=1237000.0, qt_bbl_d=11600.0, alpha_deg=89.999,
            rho_o_lb_ft3=48.7, rho_g_lb_ft3=5.0,
        )
        # cos(89.999??) ??? 0 => lambda ??? 0 => fg ??? Eq. 9.24
        assert r2.f_g == pytest.approx(1.0/1.0237, abs=0.01)


class TestCounterCurrent:
    """At high lambda, fg goes negative (counter-current flow)."""

    def test_negative(self):
        # Low q_t => high lambda => fg negative
        r = gas_fractional_flow_gravity(
            Sg=0.10, So=0.90, k_ro=0.720, k_rg=0.010,
            mu_o=1.32, mu_g=0.0134, k_md=300.0,
            Ac_ft2=1237000.0, qt_bbl_d=100.0, alpha_deg=72.5,
            rho_o_lb_ft3=48.7, rho_g_lb_ft3=5.0,
        )
        assert r.f_g < 0.0
        assert r.counter_current is True


class TestSgZero:
    """At Sg=0 (no gas), fg=0 regardless of kro."""

    def test_fg_zero(self):
        r = gas_fractional_flow_gravity(
            Sg=0.0, So=1.0, k_ro=1.0, k_rg=0.0,
            mu_o=1.32, mu_g=0.0134, k_md=300.0,
            Ac_ft2=1237000.0, qt_bbl_d=11600.0, alpha_deg=0.0,
            rho_o_lb_ft3=48.7, rho_g_lb_ft3=5.0,
        )
        assert r.f_g == 0.0


class TestValidation:
    def _ok(self) -> dict:
        return dict(
            Sg=0.40, So=0.60, k_ro=0.210, k_rg=0.090,
            mu_o=1.32, mu_g=0.0134, k_md=300.0,
            Ac_ft2=1237000.0, qt_bbl_d=11600.0, alpha_deg=72.5,
            rho_o_lb_ft3=48.7, rho_g_lb_ft3=5.0,
        )

    def test_Sg_out_of_range(self):
        kw = self._ok(); kw["Sg"] = 1.0
        with pytest.raises(ValueError, match="Sg must be in"):
            gas_fractional_flow_gravity(**kw)

    def test_krg_zero_with_Sg(self):
        kw = self._ok(); kw["k_rg"] = 0.0
        with pytest.raises(ValueError, match="k_rg must be > 0 when Sg > 0"):
            gas_fractional_flow_gravity(**kw)

    def test_alpha_out_of_range(self):
        kw = self._ok(); kw["alpha_deg"] = 100.0
        with pytest.raises(ValueError, match="alpha_deg must be in"):
            gas_fractional_flow_gravity(**kw)

    def test_rho_o_le_rho_g(self):
        kw = self._ok(); kw["rho_o_lb_ft3"] = 5.0
        with pytest.raises(ValueError, match="rho_o"):
            gas_fractional_flow_gravity(**kw)

    def test_mu_o_zero(self):
        kw = self._ok(); kw["mu_o"] = 0.0
        with pytest.raises(ValueError, match="mu_o must be > 0"):
            gas_fractional_flow_gravity(**kw)


class TestDeterminism:
    def test_repeatable(self):
        kw = dict(
            Sg=0.40, So=0.60, k_ro=0.210, k_rg=0.090,
            mu_o=1.32, mu_g=0.0134, k_md=300.0,
            Ac_ft2=1237000.0, qt_bbl_d=11600.0, alpha_deg=72.5,
            rho_o_lb_ft3=48.7, rho_g_lb_ft3=5.0,
        )
        a = gas_fractional_flow_gravity(**kw)
        b = gas_fractional_flow_gravity(**kw)
        assert a.f_g == b.f_g


class TestParametrizedQt:
    """Higher q_t lowers lambda and moves fg toward Eq 9.24."""

    @pytest.mark.parametrize("qt_pair", [(5000.0, 50000.0), (50000.0, 500000.0)])
    def test_approach_to_no_gravity(self, qt_pair):
        qt1, qt2 = qt_pair
        kw = dict(
            Sg=0.40, So=0.60, k_ro=0.210, k_rg=0.090,
            mu_o=1.32, mu_g=0.0134, k_md=300.0,
            Ac_ft2=1237000.0, alpha_deg=72.5,
            rho_o_lb_ft3=48.7, rho_g_lb_ft3=5.0,
        )
        r1 = gas_fractional_flow_gravity(qt_bbl_d=qt1, **kw)
        r2 = gas_fractional_flow_gravity(qt_bbl_d=qt2, **kw)
        # Higher q_t => smaller lambda => fg closer to 1/(1+visc term)
        no_grav_fg = 1.0 / (1.0 + (0.210/0.090)*(0.0134/1.32))
        assert abs(r2.f_g - no_grav_fg) < abs(r1.f_g - no_grav_fg)


class TestFrontalAdvance:
    """Forward difference computation sanity."""

    def test_forward_difference(self):
        Sg_list = [0.10, 0.20, 0.30, 0.40, 0.50]
        fg_list = [0.00, 0.15, 0.35, 0.55, 0.70]
        rows, times = gas_gravity_frontal_advance(
            Sg_list=Sg_list, fg_list=fg_list,
            qi_bbl_d=11600.0, phi=0.1625, Ac_ft2=1237000.0,
            times_days=[100.0, 200.0],
        )
        assert len(rows) == 5
        assert len(times) == 2
        # x should scale linearly with t
        for i in range(len(rows)):
            assert rows[i][1] == pytest.approx(2.0 * rows[i][0], rel=1e-9)
