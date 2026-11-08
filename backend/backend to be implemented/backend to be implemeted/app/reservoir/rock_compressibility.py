"""Rock pore-volume (formation) compressibility correlations.

Source: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir Engineering,
2nd edition, Ch. 1, Sec. 4.2, pp. 10-11, Eqs. (1.2) and (1.3).
"""

from __future__ import annotations

import math
from typing import Literal

RockType = Literal["sandstone", "limestone"]

# Eq. (1.2), p. 10: sandstone coefficients
SANDSTONE_C1 = 97.3200e-6      # psi^-1
SANDSTONE_PHI_MUL = 55.8721    # dimensionless
SANDSTONE_EXP = 1.42859        # dimensionless

# Eq. (1.3), p. 11: limestone coefficients
LIMESTONE_C1 = 0.853531        # psi^-1 (implicit; see book)
LIMESTONE_PHI_MUL = 2.47664e6  # dimensionless
LIMESTONE_EXP = 0.92990        # dimensionless

# Book-stated validity ranges (p. 11)
SANDSTONE_PHI_MIN = 0.02
SANDSTONE_PHI_MAX = 0.23
LIMESTONE_PHI_MIN = 0.02
LIMESTONE_PHI_MAX = 0.33


def formation_compressibility(
    phi: float,
    rock_type: RockType,
    strict: bool = False,
) -> float:
    """Return pore-volume (formation) compressibility cf in psi^-1.

    Implements Eq. (1.2) and Eq. (1.3) from Craft, Hawkins, Terry (1991),
    Applied Petroleum Reservoir Engineering, 2nd ed., Ch. 1, Sec. 4.2,
    pp. 10-11 (Newman's correlations, ref. 29 in the book).

    Args:
        phi: Porosity as a fraction (dimensionless). 0 < phi < 1.
        rock_type: Either "sandstone" or "limestone".
        strict: If True, enforce the book's stated validity range
            (sandstone 0.02 <= phi <= 0.23; limestone 0.02 <= phi <= 0.33).

    Returns:
        Pore-volume compressibility cf in psi^-1.

    Raises:
        ValueError: phi out of range, non-numeric, NaN, or invalid rock_type.
    """
    if not isinstance(phi, (int, float)):
        raise ValueError(f"phi must be numeric, got {type(phi).__name__}")
    phi = float(phi)
    # NaN-safe check: any comparison with NaN is False, so
    # `not (0.0 < phi < 1.0)` also catches NaN.
    if not (0.0 < phi < 1.0):
        raise ValueError(f"phi must be in (0, 1), got {phi!r}")

    if rock_type == "sandstone":
        if strict and not (SANDSTONE_PHI_MIN <= phi <= SANDSTONE_PHI_MAX):
            raise ValueError(
                f"sandstone phi={phi} outside book validity "
                f"[{SANDSTONE_PHI_MIN}, {SANDSTONE_PHI_MAX}]"
            )
        # Eq. (1.2), p. 10
        return SANDSTONE_C1 / math.pow(1.0 + SANDSTONE_PHI_MUL * phi, SANDSTONE_EXP)

    if rock_type == "limestone":
        if strict and not (LIMESTONE_PHI_MIN <= phi <= LIMESTONE_PHI_MAX):
            raise ValueError(
                f"limestone phi={phi} outside book validity "
                f"[{LIMESTONE_PHI_MIN}, {LIMESTONE_PHI_MAX}]"
            )
        # Eq. (1.3), p. 11
        return LIMESTONE_C1 / math.pow(1.0 + LIMESTONE_PHI_MUL * phi, LIMESTONE_EXP)

    raise ValueError(
        f"rock_type must be 'sandstone' or 'limestone', got {rock_type!r}"
    )
