"""Wichert-Aziz Z-factor correction for acid gases (Craft ref. 37, p. 21)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class WichertAzizResult:
    Tpc_adj_R: float
    ppc_adj_psia: float
    epsilon_R: float
    A_total: float


def wichert_aziz_correction(
    y_H2S: float, y_CO2: float,
    Tpc_R: float, ppc_psia: float,
) -> WichertAzizResult:
    """Apply Wichert-Aziz (1972) pseudocritical correction.

    Args:
        y_H2S: H2S mole fraction, [0, 1).
        y_CO2: CO2 mole fraction, [0, 1).
        Tpc_R: Uncorrected pseudocritical temperature, deg R (> 0).
        ppc_psia: Uncorrected pseudocritical pressure, psia (> 0).

    Returns:
        WichertAzizResult with adjusted pseudocriticals.

    Raises:
        ValueError: any input out of physical range, or adjusted
            pseudocritical would be <= 0.
    """
    if not (0.0 <= y_H2S < 1.0):
        raise ValueError(f"y_H2S must be in [0, 1), got {y_H2S!r}")
    if not (0.0 <= y_CO2 < 1.0):
        raise ValueError(f"y_CO2 must be in [0, 1), got {y_CO2!r}")
    if y_H2S + y_CO2 >= 1.0:
        raise ValueError(
            f"y_H2S + y_CO2 = {y_H2S + y_CO2!r} must be < 1"
        )
    if not (Tpc_R > 0.0):
        raise ValueError(f"Tpc_R must be > 0, got {Tpc_R!r}")
    if not (ppc_psia > 0.0):
        raise ValueError(f"ppc_psia must be > 0, got {ppc_psia!r}")

    A = y_H2S + y_CO2
    B = y_H2S
    if A <= 0.0:
        # No contaminants: no correction
        return WichertAzizResult(
            Tpc_adj_R=Tpc_R, ppc_adj_psia=ppc_psia,
            epsilon_R=0.0, A_total=0.0,
        )
    epsilon = 120.0 * (A**0.9 - A**1.6) + 15.0 * (B**0.5 - B**4)
    Tpc_adj = Tpc_R - epsilon
    if Tpc_adj <= 0.0:
        raise ValueError(
            f"epsilon = {epsilon!r} too large: Tpc_adj <= 0"
        )
    denom = Tpc_R + B * (1.0 - B) * epsilon
    if denom <= 0.0:
        raise ValueError(f"p'pc denominator = {denom!r} <= 0")
    ppc_adj = ppc_psia * Tpc_adj / denom
    return WichertAzizResult(
        Tpc_adj_R=Tpc_adj, ppc_adj_psia=ppc_adj,
        epsilon_R=epsilon, A_total=A,
    )
