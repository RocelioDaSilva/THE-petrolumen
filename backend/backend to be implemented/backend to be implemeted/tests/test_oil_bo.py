"""Tests for backend/app/reservoir/oil_bo.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 1, Sec. 6.2, pp. 34-37, Eqs. (1.29)-(1.30),
Example 1.7 (pp. 42-43).
"""

import pytest

from app.reservoir.oil_bo import BoResult, oil_bo


class TestExample17:
    """Book Example 1.7 (pp. 42-43): T=180 F, pb=2500 psia, gas_sg=0.80,
    API=40. Book answers: Bob=1.456, Bo(4000)=1.429, Bo(2000)=1.354.
    Tolerance: 0.005 bbl/STB absolute (book rounds to 3 decimals).
    """

    def test_at_pb(self):
        r = oil_bo(
            p_psia=2500.0, T_F=180.0, gas_sg=0.80,
            oil_api=40.0, pb_psia=2500.0,
        )
        assert isinstance(r, BoResult)
        assert r.bo_bbl_stb == pytest.approx(1.456, abs=0.005)
        assert r.clamped is False
        assert r.co_used is None

    def test_above_pb(self):
        r = oil_bo(
            p_psia=4000.0, T_F=180.0, gas_sg=0.80,
            oil_api=40.0, pb_psia=2500.0,
        )
        assert r.bo_bbl_stb == pytest.approx(1.429, abs=0.005)
        assert r.clamped is True
        assert r.co_used is not None
        # Book co used here is ~12.7e-6 psi^-1
        assert r.co_used == pytest.approx(12.7e-6, rel=0.05)

    def test_below_pb(self):
        r = oil_bo(
            p_psia=2000.0, T_F=180.0, gas_sg=0.80,
            oil_api=40.0, pb_psia=2500.0,
        )
        assert r.bo_bbl_stb == pytest.approx(1.354, abs=0.005)
        assert r.clamped is False
        assert r.co_used is None


class TestGammaO:
    """gamma_o = 141.5 / (131.5 + API). At API=40 -> 0.825."""

    def test_api_40(self):
        r = oil_bo(
            p_psia=2500.0, T_F=180.0, gas_sg=0.80,
            oil_api=40.0, pb_psia=2500.0,
        )
        assert r.gamma_o == pytest.approx(0.825, abs=1e-3)


class TestMonotonicity:
    """Bo decreases monotonically as p decreases below pb (gas liberation)."""

    @pytest.mark.parametrize(
        "p1,p2",
        [(2200.0, 2400.0), (1500.0, 2000.0), (500.0, 1500.0)],
    )
    def test_increasing_with_p(self, p1, p2):
        a = oil_bo(p1, 180.0, 0.80, 40.0, 2500.0)
        b = oil_bo(p2, 180.0, 0.80, 40.0, 2500.0)
        assert b.bo_bbl_stb > a.bo_bbl_stb


class TestCoOverride:
    """Explicit co_psi_inv should be honoured, bypassing Feature 6."""

    def test_override(self):
        r = oil_bo(
            p_psia=4000.0, T_F=180.0, gas_sg=0.80, oil_api=40.0,
            pb_psia=2500.0, co_psi_inv=12.7e-6,
        )
        assert r.co_used == pytest.approx(12.7e-6, rel=1e-12)
        assert r.bo_bbl_stb == pytest.approx(1.429, abs=0.005)


class TestValidation:
    def test_p_zero(self):
        with pytest.raises(ValueError, match="p_psia must be > 0"):
            oil_bo(0.0, 180.0, 0.80, 40.0, 2500.0)

    def test_pb_zero(self):
        with pytest.raises(ValueError, match="pb_psia must be > 0"):
            oil_bo(2000.0, 180.0, 0.80, 40.0, 0.0)

    def test_T_below_abs(self):
        with pytest.raises(ValueError, match="T_F must be above"):
            oil_bo(2000.0, -500.0, 0.80, 40.0, 2500.0)

    def test_gas_sg_invalid(self):
        with pytest.raises(ValueError, match="gas_sg must be in"):
            oil_bo(2000.0, 180.0, 2.5, 40.0, 2500.0)

    def test_api_invalid(self):
        with pytest.raises(ValueError, match="oil_api must be in"):
            oil_bo(2000.0, 180.0, 0.80, 150.0, 2500.0)

    def test_co_nonpositive(self):
        with pytest.raises(ValueError, match="co_psi_inv must be > 0"):
            oil_bo(
                p_psia=4000.0, T_F=180.0, gas_sg=0.80, oil_api=40.0,
                pb_psia=2500.0, co_psi_inv=0.0,
            )


class TestValidityFlag:
    def test_in_range(self):
        r = oil_bo(2000.0, 180.0, 0.80, 40.0, 2500.0)
        assert r.in_validity_range is True

    def test_api_out_of_range(self):
        # API=10 below book minimum 16.5
        r = oil_bo(2000.0, 180.0, 0.80, 10.0, 2500.0)
        assert r.in_validity_range is False


class TestDeterminism:
    def test_repeatable(self):
        a = oil_bo(2000.0, 180.0, 0.80, 40.0, 2500.0)
        b = oil_bo(2000.0, 180.0, 0.80, 40.0, 2500.0)
        assert a.bo_bbl_stb == b.bo_bbl_stb
