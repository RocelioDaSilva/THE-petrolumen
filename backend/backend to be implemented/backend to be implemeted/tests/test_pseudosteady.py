"""Tests for backend/app/reservoir/pseudosteady.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 7, Sec. 7, pp. 242-246, Eqs. (7.47), (7.61)-(7.63),
Example 7.2 (pp. 256-258).
"""

import math
import pytest

from app.reservoir.pseudosteady import (
    PseudosteadyResult,
    drainage_area_from_slope,
    pseudosteady_pwf,
    re_from_area,
    time_to_pseudosteady,
)


class TestPwf:
    """Eq. 7.47 with circular drainage (C_A=30.88)."""

    def test_pwf_positive(self):
        r = pseudosteady_pwf(
            pi_psia=4000.0, q_stb_d=500.0, mu_cp=1.5, B_bbl_stb=1.2,
            k_md=85.1, h_ft=20.0, A_ft2=2_508_000.0, CA=30.88,
            rw_ft=0.333, t_hr=100.0, phi=0.25, ct_psi_inv=30e-6,
        )
        assert isinstance(r, PseudosteadyResult)
        assert r.pwf_psia is not None
        assert 0.0 < r.pwf_psia < 4000.0
        assert r.log_term_psi is not None
        assert r.time_term_psi is not None

    def test_pwf_decreases_with_time(self):
        r1 = pseudosteady_pwf(
            4000.0, 500.0, 1.5, 1.2, 85.1, 20.0,
            2_508_000.0, 30.88, 0.333, 10.0, 0.25, 30e-6,
        )
        r2 = pseudosteady_pwf(
            4000.0, 500.0, 1.5, 1.2, 85.1, 20.0,
            2_508_000.0, 30.88, 0.333, 100.0, 0.25, 30e-6,
        )
        assert r2.pwf_psia < r1.pwf_psia


class TestAreaFromSlope:
    """Example 7.2 p. 257: m'=-0.373, q=500, B=1.2, h=20, phi=0.25,
    ct=30e-6 -> A=57.6 ac = 2,509,056 ft^2. Tolerance 2%.
    """

    def test_area(self):
        r = drainage_area_from_slope(
            m_prime_psi_per_hr=-0.373, q_stb_d=500.0, B_bbl_stb=1.2,
            h_ft=20.0, phi=0.25, ct_psi_inv=30e-6,
        )
        assert r.area_ft2 is not None
        assert r.area_ft2 == pytest.approx(2_509_056.0, rel=0.02)


class TestReFromArea:
    """re = sqrt(A/pi)."""

    def test_re(self):
        r = re_from_area(2_509_056.0)
        expected = math.sqrt(2_509_056.0 / math.pi)
        assert r.r_e_ft == pytest.approx(expected, rel=1e-12)


class TestTpss:
    """Eq. 7.6: t_pss = 1200 phi mu ct re^2 / k.
    Book example p. 217: phi=0.20, mu=1.5, ct=15e-6, re=1000, k=100
    -> t_pss = 54 hr.
    """

    def test_tpss(self):
        r = time_to_pseudosteady(
            phi=0.20, mu_cp=1.5, ct_psi_inv=15e-6, re_ft=1000.0, k_md=100.0,
        )
        assert r.t_pss_hr == pytest.approx(54.0, rel=0.05)


class TestRoundtrip:
    """re_from_area and back: A = pi re^2."""

    def test_roundtrip(self):
        A = 2_509_056.0
        r = re_from_area(A)
        A_back = math.pi * (r.r_e_ft ** 2)
        assert A_back == pytest.approx(A, rel=1e-12)


class TestValidation:
    def test_pi_zero(self):
        with pytest.raises(ValueError, match="pi_psia must be > 0"):
            pseudosteady_pwf(
                0.0, 500.0, 1.5, 1.2, 85.1, 20.0,
                2_508_000.0, 30.88, 0.333, 100.0, 0.25, 30e-6,
            )

    def test_CA_zero(self):
        with pytest.raises(ValueError, match="CA must be > 0"):
            pseudosteady_pwf(
                4000.0, 500.0, 1.5, 1.2, 85.1, 20.0,
                2_508_000.0, 0.0, 0.333, 100.0, 0.25, 30e-6,
            )

    def test_phi_out(self):
        with pytest.raises(ValueError, match="phi must be in"):
            pseudosteady_pwf(
                4000.0, 500.0, 1.5, 1.2, 85.1, 20.0,
                2_508_000.0, 30.88, 0.333, 100.0, 1.5, 30e-6,
            )

    def test_m_prime_positive(self):
        with pytest.raises(ValueError, match="m_prime_psi_per_hr must be < 0"):
            drainage_area_from_slope(
                0.5, 500.0, 1.2, 20.0, 0.25, 30e-6,
            )

    def test_A_zero(self):
        with pytest.raises(ValueError, match="A_ft2 must be > 0"):
            re_from_area(0.0)

    def test_tpss_k_zero(self):
        with pytest.raises(ValueError, match="k_md must be > 0"):
            time_to_pseudosteady(0.20, 1.5, 15e-6, 1000.0, 0.0)


class TestDeterminism:
    def test_repeatable(self):
        a = pseudosteady_pwf(
            4000.0, 500.0, 1.5, 1.2, 85.1, 20.0,
            2_508_000.0, 30.88, 0.333, 100.0, 0.25, 30e-6,
        )
        b = pseudosteady_pwf(
            4000.0, 500.0, 1.5, 1.2, 85.1, 20.0,
            2_508_000.0, 30.88, 0.333, 100.0, 0.25, 30e-6,
        )
        assert a.pwf_psia == b.pwf_psia


class TestParametrizedCA:
    """Smaller CA (worse shape) gives lower pwf (more pressure drop)."""

    @pytest.mark.parametrize("ca_pair", [(30.88, 19.06), (19.06, 8.45)])
    def test_pwf_decreases(self, ca_pair):
        ca1, ca2 = ca_pair
        r1 = pseudosteady_pwf(
            4000.0, 500.0, 1.5, 1.2, 85.1, 20.0,
            2_508_000.0, ca1, 0.333, 100.0, 0.25, 30e-6,
        )
        r2 = pseudosteady_pwf(
            4000.0, 500.0, 1.5, 1.2, 85.1, 20.0,
            2_508_000.0, ca2, 0.333, 100.0, 0.25, 30e-6,
        )
        assert r2.pwf_psia < r1.pwf_psia
