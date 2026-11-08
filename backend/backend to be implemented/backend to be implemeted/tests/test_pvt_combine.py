"""Tests for backend/app/reservoir/pvt_combine.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 6, Sec. 5, pp. 200-201, Eqs. (6.6)-(6.8),
worked examples on p. 201.
"""

import pytest

from app.reservoir.pvt_combine import (
    PVTCombineResult,
    oil_pvt_from_lab,
)


class TestWorkedExampleAbovePb:
    """Book p. 201: p=5000, sep 200 psig, RV=0.9739, Bob=1.337,
    Rsob=557. Book: Bo=1.302, Rso=557 (constant above Pb).
    Tolerance: 0.005 bbl/STB on Bo, 1 SCF/STB on Rso.
    """

    def _run(self) -> PVTCombineResult:
        return oil_pvt_from_lab(
            p_psia=5000.0, pb_psia=2695.0,
            Bob=1.337, Bodb=1.391, Rsob=557.0, Rsodb=638.0,
            RV=0.9739,
        )

    def test_bo(self):
        r = self._run()
        assert isinstance(r, PVTCombineResult)
        assert r.bo_bbl_stb == pytest.approx(1.302, abs=0.005)

    def test_rso(self):
        r = self._run()
        assert r.rso_scf_stb == pytest.approx(557.0, abs=1.0)

    def test_regime(self):
        r = self._run()
        assert r.regime == "above_pb"


class TestWorkedExampleBelowPb:
    """Book p. 201: p=2512, Bod=1.373, Rsod=596. Book: Bo=1.320,
    Rso=516. Tolerance: 0.005 bbl/STB on Bo, 2 SCF/STB on Rso.
    """

    def _run(self) -> PVTCombineResult:
        return oil_pvt_from_lab(
            p_psia=2512.0, pb_psia=2695.0,
            Bob=1.337, Bodb=1.391, Rsob=557.0, Rsodb=638.0,
            Bod_current=1.373, Rsod_current=596.0,
        )

    def test_bo(self):
        r = self._run()
        assert r.bo_bbl_stb == pytest.approx(1.320, abs=0.005)

    def test_rso(self):
        r = self._run()
        assert r.rso_scf_stb == pytest.approx(516.0, abs=2.0)

    def test_regime(self):
        r = self._run()
        assert r.regime == "below_pb"


class TestAtPb:
    """At p=pb, above-Pb branch is used; RV should equal 1.0 to yield
    Bob directly."""

    def test_at_pb(self):
        r = oil_pvt_from_lab(
            p_psia=2695.0, pb_psia=2695.0,
            Bob=1.337, Bodb=1.391, Rsob=557.0, Rsodb=638.0,
            RV=1.0,
        )
        assert r.bo_bbl_stb == pytest.approx(1.337, abs=1e-6)
        assert r.rso_scf_stb == pytest.approx(557.0, abs=1e-6)
        assert r.regime == "above_pb"


class TestValidation:
    def _ok_above(self) -> dict:
        return dict(
            p_psia=5000.0, pb_psia=2695.0,
            Bob=1.337, Bodb=1.391, Rsob=557.0, Rsodb=638.0,
            RV=0.9739,
        )

    def _ok_below(self) -> dict:
        return dict(
            p_psia=2512.0, pb_psia=2695.0,
            Bob=1.337, Bodb=1.391, Rsob=557.0, Rsodb=638.0,
            Bod_current=1.373, Rsod_current=596.0,
        )

    def test_p_zero(self):
        kw = self._ok_above(); kw["p_psia"] = 0.0
        with pytest.raises(ValueError, match="p_psia must be > 0"):
            oil_pvt_from_lab(**kw)

    def test_Bob_zero(self):
        kw = self._ok_above(); kw["Bob"] = 0.0
        with pytest.raises(ValueError, match="Bob must be > 0"):
            oil_pvt_from_lab(**kw)

    def test_Rsob_negative(self):
        kw = self._ok_above(); kw["Rsob"] = -1.0
        with pytest.raises(ValueError, match="Rsob must be >= 0"):
            oil_pvt_from_lab(**kw)

    def test_missing_RV_above(self):
        kw = self._ok_above(); kw["RV"] = None
        with pytest.raises(ValueError, match="RV.*required above"):
            oil_pvt_from_lab(**kw)

    def test_RV_negative(self):
        kw = self._ok_above(); kw["RV"] = -0.5
        with pytest.raises(ValueError, match="RV must be > 0"):
            oil_pvt_from_lab(**kw)

    def test_missing_Bod_current_below(self):
        kw = self._ok_below(); kw["Bod_current"] = None
        with pytest.raises(ValueError, match="Bod_current and Rsod_current"):
            oil_pvt_from_lab(**kw)

    def test_Bod_current_zero(self):
        kw = self._ok_below(); kw["Bod_current"] = 0.0
        with pytest.raises(ValueError, match="Bod_current must be > 0"):
            oil_pvt_from_lab(**kw)

    def test_Rsod_current_negative(self):
        kw = self._ok_below(); kw["Rsod_current"] = -1.0
        with pytest.raises(ValueError, match="Rsod_current must be >= 0"):
            oil_pvt_from_lab(**kw)


class TestDeterminism:
    def test_repeatable(self):
        a = oil_pvt_from_lab(
            2512.0, 2695.0, 1.337, 1.391, 557.0, 638.0,
            Bod_current=1.373, Rsod_current=596.0,
        )
        b = oil_pvt_from_lab(
            2512.0, 2695.0, 1.337, 1.391, 557.0, 638.0,
            Bod_current=1.373, Rsod_current=596.0,
        )
        assert a.bo_bbl_stb == b.bo_bbl_stb
        assert a.rso_scf_stb == b.rso_scf_stb


class TestParametrizedBelowPb:
    """As p decreases further, Rso should decrease; Bo should decrease
    (in the undersaturated case below Pb)."""

    @pytest.mark.parametrize(
        "p_pair",
        [
            ((2512.0, 1.373, 596.0), (2008.0, 1.322, 549.0)),
        ],
    )
    def test_rso_decreases(self, p_pair):
        (p1, bod1, rsod1), (p2, bod2, rsod2) = p_pair
        r1 = oil_pvt_from_lab(
            p1, 2695.0, 1.337, 1.391, 557.0, 638.0,
            Bod_current=bod1, Rsod_current=rsod1,
        )
        r2 = oil_pvt_from_lab(
            p2, 2695.0, 1.337, 1.391, 557.0, 638.0,
            Bod_current=bod2, Rsod_current=rsod2,
        )
        assert r2.rso_scf_stb < r1.rso_scf_stb
