"""Tests for backend/app/reservoir/gc_initial.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 4, Sec. 2, pp. 110-118, Example 4.1 (pp. 112-114).
"""

import pytest

from app.reservoir.gc_initial import (
    GCInitialRateResult,
    gas_condensate_initial_place_rate,
)


class TestExample41:
    """Example 4.1 (pp. 112-114). Book answers:
    gamma_o=0.788, M_wo=151.9, R1=12,810, R3=496, gamma_w=0.896,
    G_unit=1326 M SCF/ac-ft, f_s=0.951, G_gas=1261, N=94.8 STB/ac-ft.
    Tolerance 1% relative on G and N, 0.5% on gamma_w and f_s.
    """

    def _run(self) -> GCInitialRateResult:
        return gas_condensate_initial_place_rate(
            pi_psia=2740.0, T_F=215.0, phi_frac=0.25, Swi_frac=0.30,
            oil_rate_stb_d=242.0,
            gas_sep_rate_scf_d=3_100_000.0, gas_sep_sg=0.650,
            gas_tank_rate_scf_d=120_000.0, gas_tank_sg=1.20,
            oil_api=48.0, z_at_pi=0.825,
        )

    def test_gamma_o(self):
        r = self._run()
        assert r.gamma_o == pytest.approx(0.788, abs=0.002)

    def test_mw_o(self):
        r = self._run()
        assert r.mw_o == pytest.approx(151.9, rel=0.01)

    def test_r1_r3(self):
        r = self._run()
        assert r.r1_sep_scf_stb == pytest.approx(12810.0, rel=0.001)
        assert r.r3_tank_scf_stb == pytest.approx(496.0, rel=0.01)

    def test_gamma_w(self):
        r = self._run()
        assert r.gamma_w == pytest.approx(0.896, abs=0.005)

    def test_f_s(self):
        r = self._run()
        assert r.f_s_gas_frac == pytest.approx(0.951, abs=0.005)

    def test_g_unit(self):
        r = self._run()
        assert r.g_unit_mmscf_per_acft == pytest.approx(1326.0, rel=0.01)

    def test_g_gas_unit(self):
        r = self._run()
        assert r.g_gas_unit_mmscf_per_acft == pytest.approx(1261.0, rel=0.01)

    def test_n_oil(self):
        r = self._run()
        assert r.n_oil_unit_stb_per_acft == pytest.approx(94.8, rel=0.01)


class TestValidation:
    def _ok(self) -> dict:
        return dict(
            pi_psia=2740.0, T_F=215.0, phi_frac=0.25, Swi_frac=0.30,
            oil_rate_stb_d=242.0, gas_sep_rate_scf_d=3e6,
            gas_sep_sg=0.65, gas_tank_rate_scf_d=1.2e5,
            gas_tank_sg=1.2, oil_api=48.0, z_at_pi=0.825,
        )

    def test_pi_zero(self):
        kw = self._ok(); kw["pi_psia"] = 0.0
        with pytest.raises(ValueError, match="pi_psia must be > 0"):
            gas_condensate_initial_place_rate(**kw)

    def test_oil_rate_zero(self):
        kw = self._ok(); kw["oil_rate_stb_d"] = 0.0
        with pytest.raises(ValueError, match="oil_rate_stb_d must be > 0"):
            gas_condensate_initial_place_rate(**kw)

    def test_phi_out(self):
        kw = self._ok(); kw["phi_frac"] = 1.0
        with pytest.raises(ValueError, match="phi_frac must be in"):
            gas_condensate_initial_place_rate(**kw)

    def test_api_too_low(self):
        kw = self._ok(); kw["oil_api"] = 8.811
        with pytest.raises(ValueError, match="oil_api must be in"):
            gas_condensate_initial_place_rate(**kw)

    def test_z_zero(self):
        kw = self._ok(); kw["z_at_pi"] = 0.0
        with pytest.raises(ValueError, match="z_at_pi must be > 0"):
            gas_condensate_initial_place_rate(**kw)

    def test_gas_sg_out(self):
        kw = self._ok(); kw["gas_sep_sg"] = 3.0
        with pytest.raises(ValueError, match="gas_sep_sg must be in"):
            gas_condensate_initial_place_rate(**kw)


class TestNoTankGas:
    """Tank gas = 0 is valid; R3 = 0."""

    def test_no_tank(self):
        r = gas_condensate_initial_place_rate(
            pi_psia=3000.0, T_F=200.0, phi_frac=0.20, Swi_frac=0.20,
            oil_rate_stb_d=100.0, gas_sep_rate_scf_d=1.5e6,
            gas_sep_sg=0.65, gas_tank_rate_scf_d=0.0,
            gas_tank_sg=1.0, oil_api=45.0, z_at_pi=0.85,
        )
        assert r.r3_tank_scf_stb == 0.0
        assert r.f_s_gas_frac > 0.0


class TestDeterminism:
    def test_repeatable(self):
        a = gas_condensate_initial_place_rate(
            pi_psia=2740.0, T_F=215.0, phi_frac=0.25, Swi_frac=0.30,
            oil_rate_stb_d=242.0, gas_sep_rate_scf_d=3e6,
            gas_sep_sg=0.65, gas_tank_rate_scf_d=1.2e5,
            gas_tank_sg=1.2, oil_api=48.0, z_at_pi=0.825,
        )
        b = gas_condensate_initial_place_rate(
            pi_psia=2740.0, T_F=215.0, phi_frac=0.25, Swi_frac=0.30,
            oil_rate_stb_d=242.0, gas_sep_rate_scf_d=3e6,
            gas_sep_sg=0.65, gas_tank_rate_scf_d=1.2e5,
            gas_tank_sg=1.2, oil_api=48.0, z_at_pi=0.825,
        )
        assert a.gamma_w == b.gamma_w
        assert a.g_gas_unit_mmscf_per_acft == b.g_gas_unit_mmscf_per_acft
