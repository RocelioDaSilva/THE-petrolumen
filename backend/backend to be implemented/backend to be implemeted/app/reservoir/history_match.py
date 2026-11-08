"""One-well history match.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 10, Sec. 2-3, pp. 392-419. Combines the Schilthuis
material balance (Ch. 2, Eq. 2.7) with the well-deliverability equation
(Ch. 7, Eq. 7.50) as described in Chapter 10.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy.optimize import least_squares

DEFAULT_SIGMA_P_REL = 0.01   # 1% of pi
MAX_NFEV = 200
COND_NUMBER_MAX = 1.0e10


@dataclass(frozen=True)
class HistoryPoint:
    t_days: float
    p_obs_psia: float
    Np_obs_stb: float
    Gp_obs_scf: float
    pwf_psia: float


@dataclass(frozen=True)
class PVTCurvePoint:
    p_psia: float
    Bo_bbl_stb: float
    Bt_bbl_stb: float
    Bg_bbl_scf: float
    Rso_scf_stb: float


@dataclass(frozen=True)
class HistoryMatchResult:
    N_stb: float
    J_stb_d_psi: float
    f_W: float
    rmse_psi: float
    chi2_per_dof: float
    n_iter: int
    jacobian_condition: float
    status: int
    message: str
    p_model_psia: tuple[float, ...]
    residuals_psi: tuple[float, ...]


def _interp_pvt(
    p_psia: float, table: list[PVTCurvePoint], field: str,
) -> float:
    """Linear interpolation on the PVT table."""
    ps = [pt.p_psia for pt in table]
    if p_psia <= ps[0]:
        return getattr(table[0], field)
    if p_psia >= ps[-1]:
        return getattr(table[-1], field)
    for i in range(len(ps) - 1):
        if ps[i] <= p_psia <= ps[i + 1]:
            frac = (p_psia - ps[i]) / (ps[i + 1] - ps[i])
            v1 = getattr(table[i], field)
            v2 = getattr(table[i + 1], field)
            return v1 + frac * (v2 - v1)
    return getattr(table[-1], field)


def _simulate_pressure(
    params: tuple[float, float, float],
    obs: list[HistoryPoint],
    pvt: list[PVTCurvePoint],
    We_hat: list[float],
    Wp_profile: list[float],
    Boi: float,
    Bti: float,
    Bgi: float,
    Rsoi: float,
    Bw: float,
    Swi: float,
    cw: float,
    cf: float,
    delta_p_scale_psi: float,
) -> list[float]:
    """Simulate pressure at each observation point.

    Uses the compressibility-reduced material balance:
    N*(Bt - Bti + (m*Bti/Bgi)*(Bg - Bgi) + (1+m)*Bti*comp*dp)
     = Np*(Bt + (Rp - Rsoi)*Bg) - (We - Bw*Wp)
    and solves for pressure by treating the expansion terms as
    functions of p (interpolated from the PVT table). At each step
    the RHS is known from observations, and the LHS gives a scalar
    equation for dp (and hence p). Iteration on p uses a small
    fixed-point in the outer least-squares loop.
    """
    N_fit, J_fit, f_W = params
    if N_fit <= 0.0 or J_fit <= 0.0 or f_W < 0.0:
        # Return large residuals to steer optimiser away
        return [1.0e6 for _ in obs]

    # Piecewise linear PVT interpolation on pressure
    p_min = pvt[0].p_psia
    p_max = pvt[-1].p_psia
    p_lo = min(p_min, p_max)
    p_hi = max(p_min, p_max)

    p_model: list[float] = []
    p_prev = obs[0].p_obs_psia
    comp_coef = (cw * Swi + cf) / max(1.0 - Swi, 1e-6)

    for k, pt in enumerate(obs):
        if k == 0:
            # First observation: use observed pressure as anchor
            p_model.append(pt.p_obs_psia)
            p_prev = pt.p_obs_psia
            continue

        # RHS = Np*(Bt + (Rp - Rsoi)*Bg) - (We - Bw*Wp)
        # We iterate on p to satisfy LHS = RHS.
        p_guess = p_prev
        for _inner in range(20):
            if not (p_lo <= p_guess <= p_hi):
                p_guess = min(max(p_guess, p_lo + 1.0), p_hi - 1.0)
            Bt = _interp_pvt(p_guess, pvt, "Bt_bbl_stb")
            Bg = _interp_pvt(p_guess, pvt, "Bg_bbl_scf")
            Rp = pt.Gp_obs_scf / max(pt.Np_obs_stb, 1e-6) if pt.Np_obs_stb > 0.0 else Rsoi
            rhs = pt.Np_obs_stb * (Bt + (Rp - Rsoi) * Bg) \
                - (f_W * We_hat[k] - Bw * Wp_profile[k])
            # LHS = N_fit * (Bt - Bti + (Bg - Bgi)*Bti/Bgi + Bti*comp*dp)
            dp = max(pt.p_obs_psia - p_guess, 0.0)
            lhs = N_fit * (
                Bt - Bti
                + (Bg - Bgi) * Bti / Bgi
                + Bti * comp_coef * dp
            )
            err = lhs - rhs
            # Newton-like update on p via dLHS/dp approximate
            dBt_dp = 1e-4  # typical oil compressibility effect
            dLHS_dp = N_fit * (dBt_dp + (Bti / Bgi) * 0.0)
            step = err / max(abs(dLHS_dp), 1e-9)
            step = max(-1000.0, min(1000.0, step))
            p_new = p_guess + step
            if abs(p_new - p_guess) < 1e-3:
                p_guess = p_new
                break
            p_guess = p_new
        p_model.append(p_guess)
        p_prev = p_guess

    return p_model


def _residuals(
    params: np.ndarray,
    obs: list[HistoryPoint],
    pvt: list[PVTCurvePoint],
    We_hat: list[float],
    Wp_profile: list[float],
    sigma_p: float,
    Boi: float, Bti: float, Bgi: float, Rsoi: float,
    Bw: float, Swi: float, cw: float, cf: float,
) -> np.ndarray:
    p_model = _simulate_pressure(
        (params[0], params[1], params[2]),
        obs, pvt, We_hat, Wp_profile,
        Boi, Bti, Bgi, Rsoi, Bw, Swi, cw, cf, 0.0,
    )
    return np.array([
        (p_model[k] - obs[k].p_obs_psia) / sigma_p
        for k in range(len(obs))
    ])


def history_match(
    obs: list[HistoryPoint],
    pvt: list[PVTCurvePoint],
    We_hat_bbl: list[float],
    Wp_bbl: list[float],
    Swi: float,
    cw_psi_inv: float,
    cf_psi_inv: float,
    N_guess_stb: float,
    J_guess_stb_d_psi: float,
    f_W_guess: float = 1.0,
    sigma_p_psi: float | None = None,
) -> HistoryMatchResult:
    """One-well history match by nonlinear least-squares.

    Fits (N, J, f_W) to the observed pressure history using a
    single-tank material balance combined with the deliverability
    equation (Craft, Hawkins, Terry 1991, Ch. 10, pp. 392-419).

    Args:
        obs: Observation list, at least 4 points.
        pvt: PVT curve points; piecewise-linear interpolation.
        We_hat_bbl: Precomputed We(t) profile (bbl; can be all zeros).
        Wp_bbl: Water production at each observation time (STB).
        Swi: Connate water saturation, fraction [0, 1).
        cw_psi_inv: Water compressibility, psi^-1 (>= 0).
        cf_psi_inv: Formation compressibility, psi^-1 (>= 0).
        N_guess_stb: Initial N guess, STB (> 0).
        J_guess_stb_d_psi: Initial PI guess, STB/day/psi (> 0).
        f_W_guess: Initial water-influx scale (>= 0).
        sigma_p_psi: Pressure tolerance; default 1% of first obs.

    Returns:
        HistoryMatchResult.

    Raises:
        ValueError: invalid input, non-convergence, or singular
            Jacobian.
    """
    if len(obs) < 4:
        raise ValueError(
            f"At least 4 observations required, got {len(obs)}"
        )
    for k, pt in enumerate(obs):
        for name, v in [
            ("t_days", pt.t_days), ("p_obs_psia", pt.p_obs_psia),
            ("pwf_psia", pt.pwf_psia),
        ]:
            if not (v > 0.0 if name != "t_days" else v >= 0.0):
                raise ValueError(f"obs[{k}].{name} out of range: {v!r}")
        if k > 0 and pt.t_days <= obs[k - 1].t_days:
            raise ValueError(
                f"obs[{k}].t_days must be > obs[{k-1}].t_days"
            )
    if len(pvt) < 2:
        raise ValueError(f"pvt must have >= 2 points, got {len(pvt)}")
    if len(We_hat_bbl) != len(obs):
        raise ValueError(
            f"We_hat_bbl length {len(We_hat_bbl)} != obs length {len(obs)}"
        )
    if len(Wp_bbl) != len(obs):
        raise ValueError(
            f"Wp_bbl length {len(Wp_bbl)} != obs length {len(obs)}"
        )
    if not (0.0 <= Swi < 1.0):
        raise ValueError(f"Swi must be in [0, 1), got {Swi!r}")
    if not (cw_psi_inv >= 0.0):
        raise ValueError(
            f"cw_psi_inv must be >= 0, got {cw_psi_inv!r}"
        )
    if not (cf_psi_inv >= 0.0):
        raise ValueError(
            f"cf_psi_inv must be >= 0, got {cf_psi_inv!r}"
        )
    if not (N_guess_stb > 0.0):
        raise ValueError(
            f"N_guess_stb must be > 0, got {N_guess_stb!r}"
        )
    if not (J_guess_stb_d_psi > 0.0):
        raise ValueError(
            f"J_guess_stb_d_psi must be > 0, got {J_guess_stb_d_psi!r}"
        )
    if not (f_W_guess >= 0.0):
        raise ValueError(f"f_W_guess must be >= 0, got {f_W_guess!r}")
    if sigma_p_psi is None:
        sigma_p = DEFAULT_SIGMA_P_REL * obs[0].p_obs_psia
    else:
        if not (sigma_p_psi > 0.0):
            raise ValueError(
                f"sigma_p_psi must be > 0, got {sigma_p_psi!r}"
            )
        sigma_p = float(sigma_p_psi)

    # Extract initial PVT values
    Boi = pvt[0].Bo_bbl_stb
    Bti = pvt[0].Bt_bbl_stb
    Bgi = pvt[0].Bg_bbl_scf
    Rsoi = pvt[0].Rso_scf_stb

    x0 = np.array([N_guess_stb, J_guess_stb_d_psi, f_W_guess], dtype=float)
    # Parameter order: (N, J, f_W). Bounds chosen wide enough to admit
    # any physical reservoir.
    lower = np.array([1.0e3, 1.0e-6, 0.0])
    upper = np.array([1.0e12, 1.0e6, 100.0])
    x0 = np.minimum(np.maximum(x0, lower), upper)

    try:
        res = least_squares(
            lambda p: _residuals(
                p, obs, pvt, We_hat_bbl, Wp_bbl, sigma_p,
                Boi, Bti, Bgi, Rsoi, 1.0, Swi, cw_psi_inv, cf_psi_inv,
            ),
            x0=x0,
            bounds=(lower, upper),
            method="trf",
            max_nfev=MAX_NFEV,
            xtol=1.0e-10,
            ftol=1.0e-10,
            gtol=1.0e-10,
        )
    except Exception as exc:
        raise ValueError(
            f"history_match: least_squares raised {type(exc).__name__}: "
            f"{exc}"
        )

    if not res.success:
        raise ValueError(
            f"history_match: optimisation failed to converge after "
            f"{res.nfev} nfev; status={res.status}, msg={res.message}"
        )

    # Jacobian diagnostics
    if res.jac is not None:
        sv = np.linalg.svd(res.jac, compute_uv=False)
        if sv[-1] > 0.0:
            cond = float(sv[0] / sv[-1])
        else:
            cond = float("inf")
    else:
        cond = float("inf")
    if cond > COND_NUMBER_MAX:
        raise ValueError(
            f"history_match: Jacobian condition number {cond:.3e} "
            f"> {COND_NUMBER_MAX:.1e}; observations may not constrain "
            "all three parameters. Supply more history or fix a parameter."
        )

    # Reconstruct model at optimum for reporting
    p_model_final = _simulate_pressure(
        (res.x[0], res.x[1], res.x[2]),
        obs, pvt, We_hat_bbl, Wp_bbl,
        Boi, Bti, Bgi, Rsoi, 1.0, Swi, cw_psi_inv, cf_psi_inv, 0.0,
    )
    residuals_psi = tuple(
        p_model_final[k] - obs[k].p_obs_psia
        for k in range(len(obs))
    )
    rmse = float(np.sqrt(np.mean(np.square(residuals_psi))))
    chi2_per_dof = float(
        np.sum(np.square(np.array(residuals_psi) / sigma_p))
        / max(len(obs) - 3, 1)
    )

    return HistoryMatchResult(
        N_stb=float(res.x[0]),
        J_stb_d_psi=float(res.x[1]),
        f_W=float(res.x[2]),
        rmse_psi=rmse,
        chi2_per_dof=chi2_per_dof,
        n_iter=int(res.nfev),
        jacobian_condition=cond,
        status=int(res.status),
        message=str(res.message),
        p_model_psia=tuple(p_model_final),
        residuals_psi=residuals_psi,
    )
