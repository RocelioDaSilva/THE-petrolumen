"""Gas viscosity, Lee-Gonzalez-Eakin correlation.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 1, Sec. 5.6, pp. 27-31, Eq. (1.25) and (1.25a)-(1.25d).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Eq. (1.25a), p. 28: density prefactor. Units: (g/cc) per (psia * g/mol / degR)
RHO_PREFACTOR = 1.4935e-3

# Validity range from book p. 30
P_MIN_PSIA = 100.0
P_MAX_PSIA = 8000.0
T_MIN_F = 100.0
T_MAX_F = 340.0

# Molecular weight of air (used to convert gas SG to Mw)
MW_AIR = 28.97  # g/mol
MIN_T_F = -459.67


@dataclass(frozen=True)
class GasViscosityResult:
    mu_cp: float
    rho_gcc: float
    K: float
    X: float
    Y: float
    in_validity_range: bool


def _density_gcc(p_psia: float, T_R: float, Mw: float, z: float) -> float:
    """Gas density in g/cc, Eq. (1.25a)."""
    return RHO_PREFACTOR * p_psia * Mw / (z * T_R)


def gas_viscosity(
    p_psia: float,
    T_F: float,
    z: float,
    Mw_g_mol: float | None = None,
    gas_sg: float | None = None,
) -> GasViscosityResult:
    """Return gas viscosity (cp) via Lee-Gonzalez-Eakin, Eq. (1.25).

    Implements Eq. (1.25) and sub-equations (1.25a)-(1.25d) from
    Craft, Hawkins, Terry (1991), Ch. 1, Sec. 5.6, pp. 27-31.

    Exactly one of ``Mw_g_mol`` or ``gas_sg`` must be provided; the other
    is derived (Mw = 28.97 * gas_sg).

    Args:
        p_psia: Pressure in psia. Must be > 0.
        T_F: Temperature in deg F. Must be above absolute zero.
        z: Gas deviation factor. Must be > 0.
        Mw_g_mol: Gas molecular weight in g/mol, optional (>0).
        gas_sg: Gas specific gravity (air=1), optional, in (0, 2).

    Returns:
        GasViscosityResult(mu_cp, rho_gcc, K, X, Y, in_validity_range).

    Raises:
        ValueError: any input out of range, both or neither of Mw/gas_sg.
    """
    if not (p_psia > 0.0):
        raise ValueError(f"p_psia must be > 0, got {p_psia!r}")
    if not (T_F > MIN_T_F):
        raise ValueError(f"T_F must be above {MIN_T_F} deg F, got {T_F!r}")
    if not (z > 0.0):
        raise ValueError(f"z must be > 0, got {z!r}")

    if (Mw_g_mol is None) == (gas_sg is None):
        raise ValueError(
            "Provide exactly one of Mw_g_mol or gas_sg (not both, not neither)"
        )
    if Mw_g_mol is not None:
        if not (Mw_g_mol > 0.0):
            raise ValueError(f"Mw_g_mol must be > 0, got {Mw_g_mol!r}")
        Mw = float(Mw_g_mol)
    else:
        if not (0.0 < gas_sg < 2.0):
            raise ValueError(f"gas_sg must be in (0, 2), got {gas_sg!r}")
        Mw = MW_AIR * float(gas_sg)

    T_R = T_F + 460.0
    if not (T_R > 0.0):
        raise ValueError(f"T_R = T_F + 460.0 must be > 0, got {T_R!r}")

    # Eq. (1.25a)
    rho = _density_gcc(p_psia, T_R, Mw, z)

    # Eq. (1.25b)
    K = (9.4 + 0.02 * Mw) * math.pow(T_R, 1.5) / (209.0 + 19.0 * Mw + T_R)

    # Eq. (1.25c)
    X = 3.5 + 986.0 / T_R + 0.01 * Mw

    # Eq. (1.25d)
    Y = 2.4 - 0.2 * X

    # Eq. (1.25): mu = 1e-4 * K * exp(X * rho^Y).
    # Evaluate rho^Y via exp(Y*log(rho)) for numerical stability when rho
    # spans decades. At rho==0 the limit is 0^Y = 0 (Y > 0 always here).
    if rho > 0.0:
        rho_pow_Y = math.exp(Y * math.log(rho))
    else:
        rho_pow_Y = 0.0
    mu_cp = 1.0e-4 * K * math.exp(X * rho_pow_Y)

    in_range = (
        P_MIN_PSIA <= p_psia <= P_MAX_PSIA
        and T_MIN_F <= T_F <= T_MAX_F
    )
    return GasViscosityResult(
        mu_cp=mu_cp, rho_gcc=rho, K=K, X=X, Y=Y, in_validity_range=in_range,
    )
