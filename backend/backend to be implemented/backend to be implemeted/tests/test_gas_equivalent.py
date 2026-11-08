"""Tests for backend/app/reservoir/gas_equivalent.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 3, Sec. 6, pp. 91-95, Eqs. (3.21)-(3.24).
Book example (p. 92): condensate gamma_o=0.780, M_wo=138 -> GE=752.
"""

import pytest

from app.reservoir.gas_equivalent import (
    GasEquivalentResult,
    gas_equivalent,
)


class TestBookExample:
    """Book p. 92: gamma_o=0.780, M_wo=138 -> GE=752 SCF/bbl."""

    def test_ge_value(self):
        r = gas_equivalent(
            Np_stb=1.0, gamma_o=0.780, M_wo=138.0,
        )
        assert isinstance(r, GasEquivalentResult)
        assert r.ge_scf_per_bbl == pytest.approx(752.0, rel=0.01)

    def test_ge_water_constant(self):
        r = gas_equivalent(
            Np_stb=1.0, gamma_o=0.780, M_wo=138.0,
        )
        assert r.ge_water_scf_per_bbl == pytest.approx(7390.0, abs=1.0)


class TestApiDerivation:
    """If caller supplies only oil_api, gamma_o and M_wo are derived."""

    def test_api_50(self):
        # API=50 -> gamma_o = 141.5/181.5 = 0.7796
        # M_wo = 5954/(50-8.811) = 144.54
        r = gas_equivalent(Np_stb=1.0, oil_api=50.0)
        assert r.gamma_o == pytest.approx(0.7796, abs=1e-3)
        assert r.mw_o == pytest.approx(144.54, rel=1e-3)
        assert r.ge_scf_per_bbl > 700.0
        assert r.ge_scf_per_bbl < 800.0


class TestGammaDerivation:
    """If caller supplies only gamma_o (no M_wo, no API), Mw is from
    the alternative form of Eq. 3.22."""

    def test_gamma_only(self):
        r = gas_equivalent(Np_stb=1.0, gamma_o=0.780)
        # Mw = 42.43*0.780 / (1.008 - 0.780) = 33.09/0.228 = 145.13
        assert r.mw_o == pytest.approx(145.13, rel=1e-2)


class TestTotalGas:
    """Total Gp = Gp_surf + GE * Np (Eq. 3.23)."""

    def test_total(self):
        r = gas_equivalent(
            Np_stb=1000.0, gamma_o=0.78, M_wo=138.0,
            Gp_surf_scf=1.0e6,
        )
        expected = 1.0e6 + 752.0 * 1000.0
        assert r.gp_total_scf == pytest.approx(expected, rel=1e-3)

    def test_water_equiv(self):
        r = gas_equivalent(
            Np_stb=0.0, gamma_o=0.78, M_wo=138.0,
            Wp_water_bbl=100.0,
        )
        assert r.gw_total_scf == pytest.approx(7390.0 * 100.0, rel=1e-6)


class TestValidation:
    def test_no_identity(self):
        with pytest.raises(ValueError, match="at least one of"):
            gas_equivalent(Np_stb=1.0)

    def test_Np_negative(self):
        with pytest.raises(ValueError, match="Np_stb must be >= 0"):
            gas_equivalent(Np_stb=-1.0, gamma_o=0.78, M_wo=138.0)

    def test_Mwo_negative(self):
        with pytest.raises(ValueError, match="M_wo must be > 0"):
            gas_equivalent(Np_stb=1.0, gamma_o=0.78, M_wo=-1.0)

    def test_gamma_o_above_asymptote(self):
        with pytest.raises(ValueError, match="gamma_o must be in"):
            gas_equivalent(Np_stb=1.0, gamma_o=1.5, M_wo=138.0)

    def test_api_too_low(self):
        with pytest.raises(ValueError, match="oil_api must be in"):
            gas_equivalent(Np_stb=1.0, oil_api=5.0)

    def test_Wp_negative(self):
        with pytest.raises(ValueError, match="Wp_water_bbl must be >= 0"):
            gas_equivalent(
                Np_stb=1.0, gamma_o=0.78, M_wo=138.0,
                Wp_water_bbl=-1.0,
            )

    def test_Gp_surf_negative(self):
        with pytest.raises(ValueError, match="Gp_surf_scf must be >= 0"):
            gas_equivalent(
                Np_stb=1.0, gamma_o=0.78, M_wo=138.0,
                Gp_surf_scf=-1.0,
            )


class TestDeterminism:
    def test_repeatable(self):
        a = gas_equivalent(Np_stb=1000.0, gamma_o=0.78, M_wo=138.0)
        b = gas_equivalent(Np_stb=1000.0, gamma_o=0.78, M_wo=138.0)
        assert a.ge_scf_per_bbl == b.ge_scf_per_bbl


class TestParametrizedMw:
    """GE decreases with increasing M_wo (heavier condensate)."""

    @pytest.mark.parametrize(
        "mw_pair", [(110.0, 130.0), (130.0, 150.0), (150.0, 180.0)]
    )
    def test_ge_decreases(self, mw_pair):
        mw1, mw2 = mw_pair
        a = gas_equivalent(Np_stb=1.0, gamma_o=0.78, M_wo=mw1)
        b = gas_equivalent(Np_stb=1.0, gamma_o=0.78, M_wo=mw2)
        assert a.ge_scf_per_bbl > b.ge_scf_per_bbl
