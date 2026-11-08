"""Gas-well deliverability from pseudopressure (Craft Eq. 7.46)."""
from __future__ import annotations
import math
from dataclasses import dataclass

from scipy.integrate import simpson

EI_COEF = 1.637e3
EI_TIME = 0.00105
LOG_CONST = 3.23


@dataclass(frozen=True)
class GasDeliverabilityResult:
    m_pw: float
    pwf_psia: float
    m_pi: float
    dp_drawdown_psi: float


def _interp(p, table):
    ps = [t[0] for t in table]
    if p <= ps[0]:
        return table[0][1], table[0][2]
    if p >= ps[-1]:
        return table[-1][1], table[-1][2]
    for i in range(len(ps) - 1):
        if ps[i] <= p <= ps[i + 1]:
            f = (p - ps[i]) / (ps[i + 1] - ps[i])
            return (table[i][1] + f * (table[i + 1][1] - table[i][1]),
                    table[i][2] + f * (table[i + 1][2] - table[i][2]))
    return table[-1][1], table[-1][2]


def _m_of_p(p, table, p_ref=14.7, n_grid=500):
    grid = [p_ref + (p - p_ref) * i / (n_grid - 1) for i in range(n_grid)]
    import numpy as np
    arr_p = np.array(grid)
    arr_mu = np.array([_interp(g, table)[0] for g in grid])
    arr_z = np.array([_interp(g, table)[1] for g in grid])
    integrand = 2.0 * arr_p / (arr_mu * arr_z)
    return float(simpson(integrand, x=arr_p))


def gas_well_deliverability(
    pi_psia: float, q_scf_d: float, T_F: float,
    k_md: float, h_ft: float, phi: float, ct_psi_inv: float,
    rw_ft: float, t_hr: float,
    mu_z_table: list[tuple[float, float, float]],
) -> GasDeliverabilityResult:
    """Predict pwf from Eq. (7.46) then invert m(p).

    Args:
        pi_psia: Initial pressure, psia (> 0).
        q_scf_d: Gas rate, SCF/day (> 0).
        T_F: Reservoir temperature, deg F (> -459.67).
        k_md, h_ft, phi, ct_psi_inv, rw_ft, t_hr: all > 0; phi < 1.
        mu_z_table: (p, mu, z) table sorted by p.

    Returns:
        GasDeliverabilityResult.

    Raises:
        ValueError: any input out of range or inversion fails.
    """
    T_R = T_F + 459.67
    m_pi = _m_of_p(pi_psia, mu_z_table)
    mu_i = _interp(pi_psia, mu_z_table)[0]
    log_arg = k_md * t_hr / (phi * mu_i * ct_psi_inv * rw_ft * rw_ft)
    if log_arg <= 0.0:
        raise ValueError(f"log argument <= 0: {log_arg!r}")
    bracket = math.log10(log_arg) - LOG_CONST
    m_pw = m_pi - EI_COEF * q_scf_d * T_R / (k_md * h_ft) * bracket
    if m_pw < 0.0:
        raise ValueError(
            f"m(pw) = {m_pw!r} < 0; inputs imply negative pressure"
        )
    # Bisection to invert m(p) -> p
    p_lo = mu_z_table[0][0]
    p_hi = pi_psia
    for _ in range(80):
        p_mid = 0.5 * (p_lo + p_hi)
        m_mid = _m_of_p(p_mid, mu_z_table)
        if m_mid < m_pw:
            p_lo = p_mid
        else:
            p_hi = p_mid
        if p_hi - p_lo < 0.1:
            break
    pwf = 0.5 * (p_lo + p_hi)
    return GasDeliverabilityResult(
        m_pw=m_pw, pwf_psia=pwf, m_pi=m_pi,
        dp_drawdown_psi=pi_psia - pwf,
    )
