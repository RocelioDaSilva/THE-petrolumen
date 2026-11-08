"""Tests for backend/app/reservoir/oil_material_balance.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 2, Sec. 2-3, pp. 56-64; Ch. 6, Sec. 2,
pp. 186-191, Example 6.1 (p. 187).
"""

import pytest

from app.reservoir.oil_material_balance import (
    OilMaterialBalanceResult,
    oil_material_balance,
)


class TestExample61:
    """Example 6.1 (p. 187): combination-drive reservoir.

    Book answer: N = 98.97 MM STB (barrel units). Tolerance 1% relative.
    Compressibilities neglected (Example 6.1 does not include them).
    """

    def test_n_estimated(self):
        r = oil_material_balance(
            Np=20.0e6,
            Rp=700.0,
            Wp=1.05e6,
            Bt=1.4954,
            Bti=1.3400,
            Bg=0.008479 / 5.615,   # book prints cu ft/SCF -> bbl/SCF
            Rsoi=562.0,
            m=0.175,
            Bgi=0.006266 / 5.615,  # book prints cu ft/SCF -> bbl/SCF
            We=11.58e6,
            Bw=1.028,
        )
        assert isinstance(r, OilMaterialBalanceResult)
        assert r.n_estimated / 1.0e6 == pytest.approx(98.97, rel=0.01)


class TestDriveIndices:
    """Book p. 63: for the 12-month Conroe state, DDI+SDI+WDI = 1
    exactly when the compressibility term is zero. Check the identity
    on a synthetic case."""

    def test_sum_equals_one_when_comp_zero(self):
        r = oil_material_balance(
            Np=1.0e6, Rp=600.0, Wp=0.0,
            Bt=1.30, Bti=1.25, Bg=0.0015, Rsoi=600.0,
            m=0.0, We=0.0, Bw=1.0,
            Swi=0.0, cw=0.0, cf=0.0, delta_p=0.0,
        )
        assert r.index_sum == pytest.approx(1.0, abs=1e-9)
        assert r.ddi > 0.0
        assert r.sdi == pytest.approx(0.0, abs=1e-12)
        assert r.wdi == pytest.approx(0.0, abs=1e-12)


class TestWaterDriveOnly:
    """When only water influx drives production (Bt = Bti), DDI=0."""

    def test_ddi_zero(self):
        r = oil_material_balance(
            Np=1.0e6, Rp=600.0, Wp=0.0,
            Bt=1.25, Bti=1.25, Bg=0.0015, Rsoi=600.0,
            m=0.0, We=1.20e6, Bw=1.0,
        )
        assert r.ddi == pytest.approx(0.0, abs=1e-9)
        assert r.wdi > 0.0


class TestCompressibilityContribution:
    """Adding a compressibility term nudges the index sum above 1
    (documented consequence of the book's convention)."""

    def test_sum_slightly_above_one(self):
        r = oil_material_balance(
            Np=1.0e6, Rp=600.0, Wp=0.0,
            Bt=1.28, Bti=1.25, Bg=0.0015, Rsoi=600.0,
            m=0.0, We=0.0, Bw=1.0,
            Swi=0.20, cw=3e-6, cf=4e-6, delta_p=1000.0,
        )
        assert r.index_sum > 1.0
        assert r.index_sum < 1.5


class TestValidation:
    def test_Np_negative(self):
        with pytest.raises(ValueError, match="Np must be >= 0"):
            oil_material_balance(
                Np=-1.0, Rp=600.0, Wp=0.0,
                Bt=1.30, Bti=1.25, Bg=0.0015, Rsoi=600.0,
            )

    def test_Bt_zero(self):
        with pytest.raises(ValueError, match="Bt must be > 0"):
            oil_material_balance(
                Np=1.0e6, Rp=600.0, Wp=0.0,
                Bt=0.0, Bti=1.25, Bg=0.0015, Rsoi=600.0,
            )

    def test_m_positive_requires_Bgi(self):
        with pytest.raises(ValueError, match="Bgi is required"):
            oil_material_balance(
                Np=1.0e6, Rp=600.0, Wp=0.0,
                Bt=1.30, Bti=1.25, Bg=0.0015, Rsoi=600.0,
                m=0.1, Bgi=None,
            )

    def test_We_negative(self):
        with pytest.raises(ValueError, match="We must be >= 0"):
            oil_material_balance(
                Np=1.0e6, Rp=600.0, Wp=0.0,
                Bt=1.30, Bti=1.25, Bg=0.0015, Rsoi=600.0,
                We=-1.0,
            )

    def test_Swi_one(self):
        with pytest.raises(ValueError, match="Swi must be in"):
            oil_material_balance(
                Np=1.0e6, Rp=600.0, Wp=0.0,
                Bt=1.30, Bti=1.25, Bg=0.0015, Rsoi=600.0,
                Swi=1.0,
            )


class TestDegenerate:
    def test_rhs_hc_zero(self):
        # Np=0 -> RHS_hc=0 -> raise
        with pytest.raises(ValueError, match="RHS_hc"):
            oil_material_balance(
                Np=0.0, Rp=600.0, Wp=0.0,
                Bt=1.30, Bti=1.25, Bg=0.0015, Rsoi=600.0,
            )

    def test_denominator_zero(self):
        # Bt = Bti, m = 0, comp = 0 -> denom = 0
        with pytest.raises(ValueError, match="denominator"):
            oil_material_balance(
                Np=1.0e6, Rp=600.0, Wp=0.0,
                Bt=1.25, Bti=1.25, Bg=0.0015, Rsoi=600.0,
            )


class TestNumericRegression:
    """Fixed input -> fixed output to 1e-4 relative, guards against
    silent behaviour changes from future refactors."""

    def test_known_value(self):
        r = oil_material_balance(
            Np=2.0e6, Rp=500.0, Wp=0.0,
            Bt=1.28, Bti=1.25, Bg=0.0015, Rsoi=500.0,
        )
        # F = 2e6 * (1.28 + 0) = 2.56e6
        # denom = 0.03
        # N = 2.56e6 / 0.03 = 8.5333e7
        assert r.n_estimated == pytest.approx(2.56e6 / 0.03, rel=1e-4)


class TestParametrizedM:
    """Higher m means larger SDI for the same production history
    (all else equal)."""

    @pytest.mark.parametrize("m_vals", [(0.0, 0.1, 0.2, 0.4)])
    def test_sdi_increases_with_m(self, m_vals):
        sdis = []
        for m in m_vals:
            r = oil_material_balance(
                Np=1.0e6, Rp=600.0, Wp=0.0,
                Bt=1.30, Bti=1.25, Bg=0.0015, Rsoi=600.0,
                m=m, Bgi=0.0010,
            )
            sdis.append(r.sdi)
        for i in range(1, len(sdis)):
            assert sdis[i] > sdis[i - 1]
