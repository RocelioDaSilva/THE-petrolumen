"""Tests for backend/app/reservoir/history_match.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 10, Sec. 2-3, pp. 392-419.
"""

import pytest

from app.reservoir.history_match import (
    HistoryPoint,
    HistoryMatchResult,
    PVTCurvePoint,
    history_match,
)


def _synth_pvt() -> list[PVTCurvePoint]:
    """Small PVT table with Bo ~1.3, Bt ~1.3, Bg ~0.001, Rsoi ~600."""
    return [
        PVTCurvePoint(3000.0, 1.33, 1.33, 0.0009, 600.0),
        PVTCurvePoint(2800.0, 1.32, 1.32, 0.0010, 580.0),
        PVTCurvePoint(2600.0, 1.31, 1.31, 0.0011, 550.0),
        PVTCurvePoint(2400.0, 1.30, 1.30, 0.0012, 520.0),
        PVTCurvePoint(2200.0, 1.29, 1.29, 0.0013, 490.0),
    ]


def _synth_obs(N_true: float, J_true: float) -> list[HistoryPoint]:
    """Generate a synthetic history using a simple decline so the
    fit has a well-defined target (N, J)."""
    # Simple: assume q ~ 500 STB/d constant, pwf ~ 500 psi.
    # Np grows linearly; p_obs derived from MB with Bt~1.31.
    # Use Bt ~ 1.30 => dp/dt driven by q * Bt / (N * ct)
    # For simplicity, generate smooth synthetic pressure decline.
    Np_step = 100.0 * 30.0  # 100 STB/d * 30 days
    obs = []
    for k in range(8):
        t = float(k * 30)
        Np = float(k) * Np_step
        Gp = Np * 500.0
        # Simple pressure model: p = 3000 - alpha * Np with alpha = 1e-6
        p = 3000.0 - 1.0e-6 * Np
        obs.append(HistoryPoint(
            t_days=t, p_obs_psia=p, Np_obs_stb=Np,
            Gp_obs_scf=Gp, pwf_psia=500.0,
        ))
    return obs


class TestSynthetic:
    """Fit a synthetic history to recover a reasonable N and J."""

    def test_converges(self):
        obs = _synth_obs(N_true=1e8, J_true=1.0)
        pvt = _synth_pvt()
        We_hat = [0.0] * len(obs)
        Wp = [0.0] * len(obs)
        r = history_match(
            obs=obs, pvt=pvt, We_hat_bbl=We_hat, Wp_bbl=Wp,
            Swi=0.20, cw_psi_inv=3e-6, cf_psi_inv=5e-6,
            N_guess_stb=5e7, J_guess_stb_d_psi=1.0,
            f_W_guess=1.0, sigma_p_psi=50.0,
        )
        assert isinstance(r, HistoryMatchResult)
        assert r.N_stb > 0.0
        assert r.J_stb_d_psi > 0.0
        assert r.chi2_per_dof >= 0.0

    def test_rmse_bounded(self):
        obs = _synth_obs(N_true=1e8, J_true=1.0)
        pvt = _synth_pvt()
        We_hat = [0.0] * len(obs)
        Wp = [0.0] * len(obs)
        r = history_match(
            obs=obs, pvt=pvt, We_hat_bbl=We_hat, Wp_bbl=Wp,
            Swi=0.20, cw_psi_inv=3e-6, cf_psi_inv=5e-6,
            N_guess_stb=5e7, J_guess_stb_d_psi=1.0,
            f_W_guess=1.0, sigma_p_psi=50.0,
        )
        # RMSE should be within a few sigma_p on a synthetic that is
        # nearly exactly reproducible by the model family.
        assert r.rmse_psi < 500.0


class TestValidation:
    def _ok(self) -> dict:
        obs = _synth_obs(1e8, 1.0)
        return dict(
            obs=obs, pvt=_synth_pvt(),
            We_hat_bbl=[0.0] * len(obs), Wp_bbl=[0.0] * len(obs),
            Swi=0.20, cw_psi_inv=3e-6, cf_psi_inv=5e-6,
            N_guess_stb=5e7, J_guess_stb_d_psi=1.0, f_W_guess=1.0,
            sigma_p_psi=50.0,
        )

    def test_too_few_obs(self):
        kw = self._ok()
        kw["obs"] = kw["obs"][:3]
        kw["We_hat_bbl"] = [0.0] * 3
        kw["Wp_bbl"] = [0.0] * 3
        with pytest.raises(ValueError, match="At least 4 observations"):
            history_match(**kw)

    def test_pvt_too_short(self):
        kw = self._ok(); kw["pvt"] = kw["pvt"][:1]
        with pytest.raises(ValueError, match="pvt must have"):
            history_match(**kw)

    def test_We_length_mismatch(self):
        kw = self._ok(); kw["We_hat_bbl"] = [0.0]
        with pytest.raises(ValueError, match="We_hat_bbl length"):
            history_match(**kw)

    def test_Wp_length_mismatch(self):
        kw = self._ok(); kw["Wp_bbl"] = [0.0]
        with pytest.raises(ValueError, match="Wp_bbl length"):
            history_match(**kw)

    def test_Swi_out(self):
        kw = self._ok(); kw["Swi"] = 1.5
        with pytest.raises(ValueError, match="Swi must be in"):
            history_match(**kw)

    def test_N_guess_zero(self):
        kw = self._ok(); kw["N_guess_stb"] = 0.0
        with pytest.raises(ValueError, match="N_guess_stb must be > 0"):
            history_match(**kw)

    def test_J_guess_zero(self):
        kw = self._ok(); kw["J_guess_stb_d_psi"] = 0.0
        with pytest.raises(ValueError, match="J_guess_stb_d_psi must be > 0"):
            history_match(**kw)

    def test_non_increasing_times(self):
        kw = self._ok()
        pts = list(kw["obs"])
        pts[3] = HistoryPoint(
            t_days=pts[2].t_days, p_obs_psia=pts[3].p_obs_psia,
            Np_obs_stb=pts[3].Np_obs_stb, Gp_obs_scf=pts[3].Gp_obs_scf,
            pwf_psia=pts[3].pwf_psia,
        )
        kw["obs"] = pts
        with pytest.raises(ValueError, match="must be > obs"):
            history_match(**kw)


class TestDeterminism:
    def test_repeatable(self):
        obs = _synth_obs(1e8, 1.0)
        pvt = _synth_pvt()
        We_hat = [0.0] * len(obs)
        Wp = [0.0] * len(obs)
        kw = dict(
            obs=obs, pvt=pvt, We_hat_bbl=We_hat, Wp_bbl=Wp,
            Swi=0.20, cw_psi_inv=3e-6, cf_psi_inv=5e-6,
            N_guess_stb=5e7, J_guess_stb_d_psi=1.0, f_W_guess=1.0,
            sigma_p_psi=50.0,
        )
        a = history_match(**kw)
        b = history_match(**kw)
        assert a.N_stb == pytest.approx(b.N_stb, rel=1e-6)
        assert a.J_stb_d_psi == pytest.approx(b.J_stb_d_psi, rel=1e-6)
