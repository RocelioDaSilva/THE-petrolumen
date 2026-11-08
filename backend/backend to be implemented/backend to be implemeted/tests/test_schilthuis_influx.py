"""Tests for backend/app/reservoir/schilthuis_influx.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 8, Sec. 2, pp. 275-280, Eqs. (8.1)-(8.4),
Example 8.1 (p. 278).
"""

import pytest

from app.reservoir.schilthuis_influx import (
    SchilthuisResult,
    schilthuis_cumulative_influx,
    schilthuis_influx_constant_stabilized,
)


class TestExample81:
    """Example 8.1 (p. 278): Conroe Field, stabilized pressure.
    Book k'=2170 cu ft/day/psi; using bbl units and B_t=7.520/5.615,
    B_g=0.00693/5.615, k' is the same numeric value in bbl/day/psi.
    We test the two-phase form; k' computed from book data.
    """

    def _run(self) -> SchilthuisResult:
        return schilthuis_influx_constant_stabilized(
            dNp_dt_stb_d=44100.0,
            R_scf_stb=825.0,
            Rsoi_scf_stb=600.0,
            dWp_dt_stb_d=0.0,
            B_t_bbl_stb=7.520 / 5.615,
            B_g_bbl_scf=0.00693 / 5.615,
            B_w_bbl_stb=1.0,
            pi_psia=2275.0,
            ps_psia=2090.0,
        )

    def test_k_prime(self):
        r = self._run()
        # Book 2170 cu ft/day/psi => 2170/5.615 bbl/day/psi ~ 386.5
        assert r.k_prime == pytest.approx(386.5, rel=0.02)

    def test_daily_voidage(self):
        r = self._run()
        assert r.daily_voidage_bbl is not None
        # Book daily voidage 401,000 cu ft => 401000/5.615 ~ 71,417 bbl
        assert r.daily_voidage_bbl == pytest.approx(71417.0, rel=0.02)


class TestCumulativeFromHistory:
    """Constant drawdown for 100 days: W_e = k' * dp * t."""

    def test_constant_drawdown(self):
        r = schilthuis_cumulative_influx(
            k_prime=100.0,
            pi_psia=3000.0,
            p_history=[(0.0, 3000.0), (100.0, 2900.0)],
        )
        # dp_bar = 3000 - 2950 = 50, t=100 => W_e = 100*50*100 = 500,000
        assert r.we_cumulative_bbl == pytest.approx(500000.0, rel=1e-9)
        assert r.we_at_points_bbl == (0.0, 500000.0)


class TestMultipleIntervals:
    """Two intervals with different pressures -> sum of two
    trapezoidal increments."""

    def test_sum(self):
        r = schilthuis_cumulative_influx(
            k_prime=100.0,
            pi_psia=3000.0,
            p_history=[(0.0, 3000.0), (10.0, 2900.0), (20.0, 2800.0)],
        )
        # Interval 1: dp_bar=2950, dt=10 -> 100*50*10 = 50,000
        # Interval 2: dp_bar=2850, dt=10 -> 100*150*10 = 150,000
        # Cumulative = 200,000
        assert r.we_cumulative_bbl == pytest.approx(200000.0, rel=1e-9)


class TestValidation:
    def test_pi_le_ps(self):
        with pytest.raises(ValueError, match="must exceed ps_psia"):
            schilthuis_influx_constant_stabilized(
                44100.0, 825.0, 600.0, 0.0, 1.34, 0.0012, 1.0, 2090.0, 2275.0,
            )

    def test_bad_Bt(self):
        with pytest.raises(ValueError, match="B_t_bbl_stb must be > 0"):
            schilthuis_influx_constant_stabilized(
                44100.0, 825.0, 600.0, 0.0, 0.0, 0.0012, 1.0, 2275.0, 2090.0,
            )

    def test_negative_rate(self):
        with pytest.raises(ValueError, match="dNp_dt_stb_d must be >= 0"):
            schilthuis_influx_constant_stabilized(
                -1.0, 825.0, 600.0, 0.0, 1.34, 0.0012, 1.0, 2275.0, 2090.0,
            )

    def test_voidage_zero(self):
        with pytest.raises(ValueError, match="voidage"):
            schilthuis_influx_constant_stabilized(
                0.0, 825.0, 600.0, 0.0, 1.34, 0.0012, 1.0, 2275.0, 2090.0,
            )

    def test_history_too_short(self):
        with pytest.raises(ValueError, match=">= 2 points"):
            schilthuis_cumulative_influx(100.0, 3000.0, [(0.0, 3000.0)])

    def test_negative_time(self):
        with pytest.raises(ValueError, match="t_days must be >= 0"):
            schilthuis_cumulative_influx(
                100.0, 3000.0, [(-1.0, 3000.0), (100.0, 2900.0)],
            )

    def test_non_increasing_time(self):
        with pytest.raises(ValueError, match="strictly increasing"):
            schilthuis_cumulative_influx(
                100.0, 3000.0, [(50.0, 3000.0), (50.0, 2900.0)],
            )

    def test_k_prime_zero(self):
        with pytest.raises(ValueError, match="k_prime must be > 0"):
            schilthuis_cumulative_influx(
                0.0, 3000.0, [(0.0, 3000.0), (100.0, 2900.0)],
            )


class TestDeterminism:
    def test_repeatable(self):
        a = schilthuis_cumulative_influx(
            100.0, 3000.0,
            [(0.0, 3000.0), (50.0, 2950.0), (100.0, 2900.0)],
        )
        b = schilthuis_cumulative_influx(
            100.0, 3000.0,
            [(0.0, 3000.0), (50.0, 2950.0), (100.0, 2900.0)],
        )
        assert a.we_cumulative_bbl == b.we_cumulative_bbl


class TestParametrizedKPrime:
    """Doubling k' doubles W_e for the same history."""

    @pytest.mark.parametrize("k_pair", [(50.0, 100.0), (100.0, 200.0)])
    def test_doubles(self, k_pair):
        k1, k2 = k_pair
        r1 = schilthuis_cumulative_influx(
            k1, 3000.0, [(0.0, 3000.0), (100.0, 2900.0)],
        )
        r2 = schilthuis_cumulative_influx(
            k2, 3000.0, [(0.0, 3000.0), (100.0, 2900.0)],
        )
        assert r2.we_cumulative_bbl == pytest.approx(
            2.0 * r1.we_cumulative_bbl, rel=1e-9
        )
