"""Tests for backend/app/reservoir/superposition.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 7, Sec. 9, pp. 249-253, Eq. (7.36), (7.57),
Example 7.1 (pp. 250-252).
"""

import pytest

from app.reservoir.superposition import (
    SuperpositionResult,
    SuperpositionSource,
    superposition_pressure_drop,
)


class TestExample71:
    """Example 7.1 (pp. 250-252): 4 wells, t=240 hr, k=47, h=50,
    mu=0.40, B=1.50, phi=0.112, ct=15e-6.
    Book: dp1=6.6, dp2=5.7, dp4=6.4, dp5=6.6, total=25.3 psi.
    Tolerance 5% (book uses -Ei lookup table).
    """

    def _run(self) -> SuperpositionResult:
        return superposition_pressure_drop(
            observation_time_hr=240.0,
            sources=[
                SuperpositionSource(
                    q_stb_d=265.0, t_start_hr=0.0, distance_ft=1700.0,
                ),
                SuperpositionSource(
                    q_stb_d=270.0, t_start_hr=0.0, distance_ft=1920.0,
                ),
                SuperpositionSource(
                    q_stb_d=260.0, t_start_hr=0.0, distance_ft=1870.0,
                ),
                SuperpositionSource(
                    q_stb_d=287.0, t_start_hr=0.0, distance_ft=1680.0,
                ),
            ],
            k_md=47.0, h_ft=50.0, mu_cp=0.40, B_bbl_stb=1.50,
            phi=0.112, ct_psi_inv=15e-6,
        )

    def test_dp1(self):
        r = self._run()
        assert r.dp_per_source_psi[0] == pytest.approx(6.6, abs=0.4)

    def test_dp2(self):
        r = self._run()
        assert r.dp_per_source_psi[1] == pytest.approx(5.7, abs=0.4)

    def test_dp4(self):
        r = self._run()
        assert r.dp_per_source_psi[2] == pytest.approx(6.4, abs=0.4)

    def test_dp5(self):
        r = self._run()
        assert r.dp_per_source_psi[3] == pytest.approx(6.6, abs=0.4)

    def test_dp_total(self):
        r = self._run()
        assert r.dp_total_psi == pytest.approx(25.3, abs=1.5)


class TestSingleWellMatchesLineSource:
    """A single source should exactly match Eq. 7.36."""

    def test_single(self):
        from scipy.special import expi
        q, mu, B, k, h = 200.0, 1.0, 1.2, 100.0, 20.0
        phi, ct = 0.20, 15e-6
        r_ft, t_hr = 500.0, 100.0
        x = (phi * mu * ct * r_ft * r_ft) / (0.00105 * k * t_hr)
        expected = (70.6 * q * mu * B / (k * h)) * (-float(expi(-x)))
        r = superposition_pressure_drop(
            observation_time_hr=t_hr,
            sources=[SuperpositionSource(
                q_stb_d=q, t_start_hr=0.0, distance_ft=r_ft,
            )],
            k_md=k, h_ft=h, mu_cp=mu, B_bbl_stb=B,
            phi=phi, ct_psi_inv=ct,
        )
        assert r.dp_total_psi == pytest.approx(expected, rel=1e-10)


class TestLateStartingSource:
    """A source that has not yet started should contribute zero and be
    flagged."""

    def test_inactive(self):
        r = superposition_pressure_drop(
            observation_time_hr=10.0,
            sources=[
                SuperpositionSource(q_stb_d=100.0, t_start_hr=0.0,
                                    distance_ft=500.0),
                SuperpositionSource(q_stb_d=200.0, t_start_hr=20.0,
                                    distance_ft=800.0),
            ],
            k_md=100.0, h_ft=20.0, mu_cp=1.0, B_bbl_stb=1.2,
            phi=0.20, ct_psi_inv=15e-6,
        )
        assert len(r.inactive_source_indices) == 1
        assert r.inactive_source_indices[0] == 1
        assert r.dp_per_source_psi[1] == 0.0


class TestImageWellFault:
    """Fault doubles drawdown vs no fault (image is at same rate at 2d)."""

    def test_doubles(self):
        no_fault = superposition_pressure_drop(
            observation_time_hr=100.0,
            sources=[SuperpositionSource(
                q_stb_d=200.0, t_start_hr=0.0, distance_ft=500.0,
            )],
            k_md=100.0, h_ft=20.0, mu_cp=1.0, B_bbl_stb=1.2,
            phi=0.20, ct_psi_inv=15e-6,
        )
        with_fault = superposition_pressure_drop(
            observation_time_hr=100.0,
            sources=[
                SuperpositionSource(
                    q_stb_d=200.0, t_start_hr=0.0, distance_ft=500.0,
                ),
                SuperpositionSource(
                    q_stb_d=200.0, t_start_hr=0.0, distance_ft=1000.0,
                ),
            ],
            k_md=100.0, h_ft=20.0, mu_cp=1.0, B_bbl_stb=1.2,
            phi=0.20, ct_psi_inv=15e-6,
        )
        assert with_fault.dp_total_psi > no_fault.dp_total_psi


class TestValidation:
    def _one(self) -> list[SuperpositionSource]:
        return [SuperpositionSource(
            q_stb_d=200.0, t_start_hr=0.0, distance_ft=500.0,
        )]

    def test_t_zero(self):
        with pytest.raises(ValueError, match="observation_time_hr must be"):
            superposition_pressure_drop(
                0.0, self._one(), 100.0, 20.0, 1.0, 1.2, 0.20, 15e-6,
            )

    def test_empty_sources(self):
        with pytest.raises(ValueError, match="non-empty"):
            superposition_pressure_drop(
                100.0, [], 100.0, 20.0, 1.0, 1.2, 0.20, 15e-6,
            )

    def test_phi_too_small(self):
        with pytest.raises(ValueError, match="phi must be in"):
            superposition_pressure_drop(
                100.0, self._one(), 100.0, 20.0, 1.0, 1.2, 1e-5, 15e-6,
            )

    def test_r_zero(self):
        with pytest.raises(ValueError, match="distance_ft must be > 0"):
            superposition_pressure_drop(
                100.0,
                [SuperpositionSource(q_stb_d=200.0, t_start_hr=0.0,
                                     distance_ft=0.0)],
                100.0, 20.0, 1.0, 1.2, 0.20, 15e-6,
            )

    def test_k_zero(self):
        with pytest.raises(ValueError, match="k_md must be > 0"):
            superposition_pressure_drop(
                100.0, self._one(), 0.0, 20.0, 1.0, 1.2, 0.20, 15e-6,
            )


class TestDeterminism:
    def test_repeatable(self):
        a = superposition_pressure_drop(
            240.0,
            [SuperpositionSource(q_stb_d=265.0, t_start_hr=0.0,
                                 distance_ft=1700.0)],
            47.0, 50.0, 0.40, 1.50, 0.112, 15e-6,
        )
        b = superposition_pressure_drop(
            240.0,
            [SuperpositionSource(q_stb_d=265.0, t_start_hr=0.0,
                                 distance_ft=1700.0)],
            47.0, 50.0, 0.40, 1.50, 0.112, 15e-6,
        )
        assert a.dp_total_psi == b.dp_total_psi


class TestParametrizedQ:
    """Doubling q doubles dp for a single source."""

    @pytest.mark.parametrize("q_pair", [(100.0, 200.0), (200.0, 400.0)])
    def test_linear_in_q(self, q_pair):
        q1, q2 = q_pair
        r1 = superposition_pressure_drop(
            100.0,
            [SuperpositionSource(q_stb_d=q1, t_start_hr=0.0,
                                 distance_ft=500.0)],
            100.0, 20.0, 1.0, 1.2, 0.20, 15e-6,
        )
        r2 = superposition_pressure_drop(
            100.0,
            [SuperpositionSource(q_stb_d=q2, t_start_hr=0.0,
                                 distance_ft=500.0)],
            100.0, 20.0, 1.0, 1.2, 0.20, 15e-6,
        )
        assert r2.dp_total_psi == pytest.approx(2.0 * r1.dp_total_psi, rel=1e-9)
