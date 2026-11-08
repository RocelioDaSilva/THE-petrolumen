"""Schilthuis steady-state water influx.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 8, Sec. 2, pp. 275-280, Eqs. (8.1)-(8.4),
Example 8.1 (p. 278).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SchilthuisResult:
    k_prime: float
    we_cumulative_bbl: float
    we_at_points_bbl: tuple[float, ...]
    daily_voidage_bbl: float | None


def schilthuis_influx_constant_stabilized(
    dNp_dt_stb_d: float,
    R_scf_stb: float,
    Rsoi_scf_stb: float,
    dWp_dt_stb_d: float,
    B_t_bbl_stb: float,
    B_g_bbl_scf: float,
    B_w_bbl_stb: float,
    pi_psia: float,
    ps_psia: float,
) -> SchilthuisResult:
    """Solve for k' from a period of stabilized pressure (Eq. 8.2-8.4).

    Computes daily voidage via Eq. (8.4) and divides by the pressure
    drop pi - ps to yield k'. Uses the two-phase FVF form; callers
    who only have Bo and Rsoi can compute Bt via Eq. (1.28) first.

    Args:
        dNp_dt_stb_d: Daily oil production rate, STB/day (>= 0).
        R_scf_stb: Producing GOR, SCF/STB (>= 0).
        Rsoi_scf_stb: Initial solution GOR, SCF/STB (>= 0).
        dWp_dt_stb_d: Daily water production, STB/day (>= 0).
        B_t_bbl_stb: Two-phase FVF, bbl/STB (> 0).
        B_g_bbl_scf: Gas FVF, bbl/SCF (> 0).
        B_w_bbl_stb: Water FVF, bbl/STB (> 0).
        pi_psia: Initial pressure, psia (> 0).
        ps_psia: Stabilized pressure, psia (> 0; < pi).

    Returns:
        SchilthuisResult with k_prime and the daily voidage.

    Raises:
        ValueError: invalid input or pi <= ps.
    """
    if not (dNp_dt_stb_d >= 0.0):
        raise ValueError(
            f"dNp_dt_stb_d must be >= 0, got {dNp_dt_stb_d!r}"
        )
    if not (R_scf_stb >= 0.0):
        raise ValueError(f"R_scf_stb must be >= 0, got {R_scf_stb!r}")
    if not (Rsoi_scf_stb >= 0.0):
        raise ValueError(
            f"Rsoi_scf_stb must be >= 0, got {Rsoi_scf_stb!r}"
        )
    if not (dWp_dt_stb_d >= 0.0):
        raise ValueError(
            f"dWp_dt_stb_d must be >= 0, got {dWp_dt_stb_d!r}"
        )
    if not (B_t_bbl_stb > 0.0):
        raise ValueError(f"B_t_bbl_stb must be > 0, got {B_t_bbl_stb!r}")
    if not (B_g_bbl_scf > 0.0):
        raise ValueError(f"B_g_bbl_scf must be > 0, got {B_g_bbl_scf!r}")
    if not (B_w_bbl_stb > 0.0):
        raise ValueError(f"B_w_bbl_stb must be > 0, got {B_w_bbl_stb!r}")
    if not (pi_psia > 0.0):
        raise ValueError(f"pi_psia must be > 0, got {pi_psia!r}")
    if not (ps_psia > 0.0):
        raise ValueError(f"ps_psia must be > 0, got {ps_psia!r}")
    if not (pi_psia > ps_psia):
        raise ValueError(
            f"pi_psia ({pi_psia!r}) must exceed ps_psia ({ps_psia!r}); "
            "no drawdown => k' undefined."
        )

    # Eq. (8.4): daily voidage rate (in bbl)
    voidage = (
        B_t_bbl_stb * dNp_dt_stb_d
        + (R_scf_stb - Rsoi_scf_stb) * B_g_bbl_scf * dNp_dt_stb_d
        + B_w_bbl_stb * dWp_dt_stb_d
    )
    if not (voidage > 0.0):
        raise ValueError(
            f"Daily voidage = {voidage!r} bbl/day <= 0; check inputs."
        )
    k_prime = voidage / (pi_psia - ps_psia)
    return SchilthuisResult(
        k_prime=k_prime,
        we_cumulative_bbl=0.0,
        we_at_points_bbl=(),
        daily_voidage_bbl=voidage,
    )


def schilthuis_cumulative_influx(
    k_prime: float,
    pi_psia: float,
    p_history: list[tuple[float, float]],
) -> SchilthuisResult:
    """Cumulative influx by trapezoid over (t, p) history (Eq. 8.1).

    Args:
        k_prime: Schilthuis influx constant, bbl/day/psi (> 0).
        pi_psia: Initial pressure, psia (> 0).
        p_history: List of (t_days >= 0, p_psia > 0), non-empty,
            strictly increasing in t.

    Returns:
        SchilthuisResult with cumulative W_e at each history point.

    Raises:
        ValueError: invalid input.
    """
    if not (k_prime > 0.0):
        raise ValueError(f"k_prime must be > 0, got {k_prime!r}")
    if not (pi_psia > 0.0):
        raise ValueError(f"pi_psia must be > 0, got {pi_psia!r}")
    if len(p_history) < 2:
        raise ValueError(
            f"p_history must have >= 2 points for integration, "
            f"got {len(p_history)}"
        )
    for i, (t, p) in enumerate(p_history):
        if not (t >= 0.0):
            raise ValueError(
                f"p_history[{i}].t_days must be >= 0, got {t!r}"
            )
        if not (p > 0.0):
            raise ValueError(
                f"p_history[{i}].p_psia must be > 0, got {p!r}"
            )
        if i > 0 and not (t > p_history[i - 1][0]):
            raise ValueError(
                f"p_history times must be strictly increasing; "
                f"p_history[{i-1}].t_days = {p_history[i-1][0]!r}, "
                f"p_history[{i}].t_days = {t!r}"
            )

    cum: list[float] = [0.0]
    W_e = 0.0
    for i in range(1, len(p_history)):
        t_prev, p_prev = p_history[i - 1]
        t_curr, p_curr = p_history[i]
        dt = t_curr - t_prev
        p_bar = 0.5 * (p_prev + p_curr)
        dp_bar = pi_psia - p_bar
        W_e += k_prime * dp_bar * dt
        cum.append(W_e)

    return SchilthuisResult(
        k_prime=k_prime,
        we_cumulative_bbl=W_e,
        we_at_points_bbl=tuple(cum),
        daily_voidage_bbl=None,
    )
