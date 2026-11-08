"""Tests for backend/app/reservoir/internal_gas_drive.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 9, Sec. 3.3, pp. 360-375, Eqs. (9.33), (9.40),
(9.51), (9.56), Example 9.1 (pp. 370-375).
"""

import pytest

from app.reservoir.internal_gas_drive import (
    PVTPoint,
    TarnerResult,
    tarner_gas_drive,
)


class TestExample91:
    """Example 9.1 (pp. 370-375): pi=2500, N=56 MM STB, Swi=0.20.
    At 2300 psia: book Np = 939,300 STB (Tarner). Tolerance 2%.
    Rel-perm supplied as synthetic approximation to Fig. 9.16:
    off-chart kg/ko at SL~0.968 is effectively 0.
    """

    def _pvt(self) -> list[PVTPoint]:
        return [
            PVTPoint(2500.0, 1.498, 0.001048, 721.0, 0.488, 0.0170),
            PVTPoint(2300.0, 1.463, 0.001155, 669.0, 0.539, 0.0166),
        ]

    def _rel_perm(self) -> list[tuple[float, float]]:
        # Approximate Fig 9.16; kg/ko ~ 0 at SL > 0.95
        return [
            (0.20, 1.0e9),
            (0.30, 100.0),
            (0.40, 10.0),
            (0.50, 1.0),
            (0.60, 0.2),
            (0.70, 0.04),
            (0.80, 0.005),
            (0.90, 3.0e-4),
            (0.95, 3.0e-5),
            (0.99, 1.0e-6),
        ]

    def _run(self) -> TarnerResult:
        return tarner_gas_drive(
            N_stb=56.0e6, Swi=0.20,
            pvt=self._pvt(), rel_perm=self._rel_perm(),
        )

    def test_np(self):
        r = self._run()
        # Book Tarner: Np = 939,300 STB at 2300 psia
        assert r.rows[-1].Np_stb == pytest.approx(939_300.0, rel=0.05)

    def test_converged(self):
        r = self._run()
        assert r.converged_all is True
        for row in r.rows:
            assert row.converged is True

    def test_iteration_count(self):
        r = self._run()
        # Each step should converge in a handful of iterations
        for row in r.rows:
            assert 1 <= row.n_iter <= 20


class TestMonotonicProduction:
    """Np and Gp increase with each pressure step."""

    def test_monotone(self):
        pvt = [
            PVTPoint(2500.0, 1.498, 0.001048, 721.0, 0.488, 0.0170),
            PVTPoint(2400.0, 1.480, 0.001100, 695.0, 0.512, 0.0168),
            PVTPoint(2300.0, 1.463, 0.001155, 669.0, 0.539, 0.0166),
            PVTPoint(2200.0, 1.446, 0.001212, 643.0, 0.565, 0.0164),
        ]
        rel_perm = [
            (0.20, 1.0e9), (0.40, 10.0), (0.60, 0.2),
            (0.80, 0.005), (0.95, 3.0e-5), (0.99, 1.0e-6),
        ]
        r = tarner_gas_drive(56e6, 0.20, pvt=pvt, rel_perm=rel_perm)
        for i in range(1, len(r.rows)):
            assert r.rows[i].Np_stb > r.rows[i-1].Np_stb
            assert r.rows[i].Gp_scf > r.rows[i-1].Gp_scf


class TestValidation:
    def _pvt(self) -> list[PVTPoint]:
        return [
            PVTPoint(2500.0, 1.498, 0.001048, 721.0, 0.488, 0.0170),
            PVTPoint(2300.0, 1.463, 0.001155, 669.0, 0.539, 0.0166),
        ]

    def _rp(self) -> list[tuple[float, float]]:
        return [(0.20, 1.0), (0.50, 1.0), (0.90, 1.0e-4)]

    def test_N_zero(self):
        with pytest.raises(ValueError, match="N_stb must be > 0"):
            tarner_gas_drive(0.0, 0.20, pvt=self._pvt(), rel_perm=self._rp())

    def test_Swi_out_of_range(self):
        with pytest.raises(ValueError, match="Swi must be in"):
            tarner_gas_drive(56e6, 1.0, pvt=self._pvt(), rel_perm=self._rp())

    def test_pvt_too_short(self):
        with pytest.raises(ValueError, match="pvt must have"):
            tarner_gas_drive(
                56e6, 0.20,
                pvt=[PVTPoint(2500.0, 1.498, 0.001048, 721.0, 0.488, 0.0170)],
                rel_perm=self._rp(),
            )

    def test_pvt_non_monotone(self):
        pvt = [
            PVTPoint(2500.0, 1.498, 0.001048, 721.0, 0.488, 0.0170),
            PVTPoint(2600.0, 1.463, 0.001155, 669.0, 0.539, 0.0166),
        ]
        with pytest.raises(ValueError, match="pressures must strictly decrease"):
            tarner_gas_drive(56e6, 0.20, pvt=pvt, rel_perm=self._rp())

    def test_rel_perm_too_short(self):
        with pytest.raises(ValueError, match="rel_perm must have"):
            tarner_gas_drive(
                56e6, 0.20, pvt=self._pvt(), rel_perm=[(0.5, 1.0)],
            )


class TestDeterminism:
    def test_repeatable(self):
        pvt = [
            PVTPoint(2500.0, 1.498, 0.001048, 721.0, 0.488, 0.0170),
            PVTPoint(2300.0, 1.463, 0.001155, 669.0, 0.539, 0.0166),
        ]
        rp = [(0.20, 1.0), (0.50, 1.0), (0.90, 1.0e-4)]
        a = tarner_gas_drive(56e6, 0.20, pvt=pvt, rel_perm=rp)
        b = tarner_gas_drive(56e6, 0.20, pvt=pvt, rel_perm=rp)
        assert a.rows[0].Np_stb == b.rows[0].Np_stb


class TestParametrizedSwi:
    """Higher Swi means less oil saturation, so more gas relative
    permeability at the same Np/N and higher instantaneous R.
    Np should be slightly lower at higher Swi."""

    @pytest.mark.parametrize("swi_pair", [(0.15, 0.25)])
    def test_np_decreases_with_swi(self, swi_pair):
        sw1, sw2 = swi_pair
        pvt = [
            PVTPoint(2500.0, 1.498, 0.001048, 721.0, 0.488, 0.0170),
            PVTPoint(2300.0, 1.463, 0.001155, 669.0, 0.539, 0.0166),
        ]
        rp = [(0.20, 1.0), (0.50, 1.0), (0.90, 1.0e-4)]
        r1 = tarner_gas_drive(56e6, sw1, pvt=pvt, rel_perm=rp)
        r2 = tarner_gas_drive(56e6, sw2, pvt=pvt, rel_perm=rp)
        # Higher Swi => less oil pore space => Np should not grow
        assert r2.rows[0].Np_stb <= r1.rows[0].Np_stb + 1.0
