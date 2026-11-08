"""Waterflood recovery efficiency decomposition.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 9, Sec. 2, pp. 335-347, Sec. 4.3, pp. 378-380,
Eq. (9.1); Eq. (5.4), p. 150 (analogous microscopic displacement form).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WaterfloodEfficiencyResult:
    E_a: float | None
    E_i: float | None
    E_d: float | None
    E_v: float
    E: float


def _check_unit(name: str, v: float) -> None:
    if not (0.0 <= v <= 1.0):
        raise ValueError(f"{name} must be in [0, 1], got {v!r}")


def waterflood_efficiency_from_components(
    E_a: float, E_i: float, E_d: float,
) -> WaterfloodEfficiencyResult:
    """E = Ea * Ei * Ed via Eqs. (9.1) and (p. 336) decomposition.

    Args:
        E_a: Areal sweep efficiency, [0, 1].
        E_i: Vertical sweep efficiency, [0, 1].
        E_d: Microscopic displacement efficiency, [0, 1].

    Returns:
        WaterfloodEfficiencyResult with E_v and E.

    Raises:
        ValueError: any component outside [0, 1].
    """
    _check_unit("E_a", E_a)
    _check_unit("E_i", E_i)
    _check_unit("E_d", E_d)
    E_v = E_a * E_i
    E = E_v * E_d
    return WaterfloodEfficiencyResult(
        E_a=E_a, E_i=E_i, E_d=E_d, E_v=E_v, E=E,
    )


def waterflood_ed_from_saturations(
    Swr: float, Sor: float,
) -> float:
    """Microscopic Ed from residual saturations (analog of Eq. 5.4).

    Ed = (1 - Swr - Sor) / (1 - Swr).

    Args:
        Swr: Initial (connate) water saturation, fraction (0, 1).
        Sor: Residual oil saturation at waterflood termination,
            fraction (>= 0; Swr + Sor < 1).

    Returns:
        Ed, fraction [0, 1].

    Raises:
        ValueError: saturations out of range or Swr+Sor >= 1.
    """
    if not (0.0 < Swr < 1.0):
        raise ValueError(f"Swr must be in (0, 1), got {Swr!r}")
    if not (Sor >= 0.0):
        raise ValueError(f"Sor must be >= 0, got {Sor!r}")
    if not (Swr + Sor < 1.0):
        raise ValueError(
            f"Swr + Sor = {Swr + Sor!r} must be < 1 "
            "(hydrocarbon pore space is non-negative)"
        )
    return (1.0 - Swr - Sor) / (1.0 - Swr)


def waterflood_efficiency_from_saturations(
    Swr: float, Sor: float,
    E_a: float, E_i: float,
) -> WaterfloodEfficiencyResult:
    """E = Ea * Ei * Ed(Swr, Sor) using the Eq. 5.4 analogy.

    Args:
        Swr: Initial water saturation (0, 1).
        Sor: Residual oil saturation at termination (>= 0;
            Swr + Sor < 1).
        E_a: Areal sweep efficiency, [0, 1].
        E_i: Vertical sweep efficiency, [0, 1].

    Returns:
        WaterfloodEfficiencyResult.

    Raises:
        ValueError: any input out of range.
    """
    Ed = waterflood_ed_from_saturations(Swr, Sor)
    _check_unit("E_a", E_a)
    _check_unit("E_i", E_i)
    E_v = E_a * E_i
    E = E_v * Ed
    return WaterfloodEfficiencyResult(
        E_a=E_a, E_i=E_i, E_d=Ed, E_v=E_v, E=E,
    )
