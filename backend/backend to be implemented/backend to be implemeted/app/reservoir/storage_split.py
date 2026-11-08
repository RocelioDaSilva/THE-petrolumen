"""Storage reservoir base/working gas split (Craft pp. 95-96, Fig 3.11)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class StorageGasResult:
    base_gas_scf: float
    working_gas_scf: float
    max_gas_scf: float
    unused_gas_scf: float
    base_fraction: float
    working_fraction: float


def storage_gas_split(
    G_scf: float, pi_over_zi: float,
    base_pz: float, max_pz: float,
) -> StorageGasResult:
    """Storage base/working/unused gas split.

    Args:
        G_scf: Initial gas in place at the storage reservoir's
            starting conditions, SCF (> 0).
        pi_over_zi: p/z at initial storage pressure (psia; > 0).
        base_pz: p/z at base (cushion) pressure (psia; > 0).
        max_pz: p/z at max injection pressure (psia; > 0).

    Returns:
        StorageGasResult.

    Raises:
        ValueError: any input out of range or ordering violated.
    """
    if not (G_scf > 0.0):
        raise ValueError(f"G_scf must be > 0, got {G_scf!r}")
    for n, v in [("pi_over_zi", pi_over_zi), ("base_pz", base_pz),
                 ("max_pz", max_pz)]:
        if not (v > 0.0):
            raise ValueError(f"{n} must be > 0, got {v!r}")
    if base_pz >= max_pz:
        raise ValueError(
            f"base_pz ({base_pz!r}) must be < max_pz ({max_pz!r})"
        )
    if max_pz > pi_over_zi * (1.0 + 1e-9):
        # max can exceed initial if the field is over-pressurized; that's
        # physically valid but requires the caller to confirm. Here we
        # allow it as the reservoir may be deliberately over-pressured.
        pass

    base = G_scf * base_pz / pi_over_zi
    g_max = G_scf * max_pz / pi_over_zi
    working = g_max - base
    unused = max(0.0, G_scf - g_max)
    return StorageGasResult(
        base_gas_scf=base,
        working_gas_scf=working,
        max_gas_scf=g_max,
        unused_gas_scf=unused,
        base_fraction=base / G_scf,
        working_fraction=working / G_scf,
    )
