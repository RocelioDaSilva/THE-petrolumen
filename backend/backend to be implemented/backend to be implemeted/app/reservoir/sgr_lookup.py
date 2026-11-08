"""Residual gas saturation lookup (Craft Table 3.3, p. 80)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class SgrLookupResult:
    Sgr: float
    Sgr_pct: float
    used_table_average: bool
    rock_name_resolved: str


# (min_pct, max_pct) per Table 3.3; single values stored as (x, x)
_SGR_TABLE = {
    "unconsolidated sand": (16.0, 16.0),
    "slightly consolidated sand": (21.0, 21.0),
    "selas porcelain": (17.0, 17.0),
    "norton alundum": (24.0, 24.0),
    "wilcox": (25.0, 25.0),
    "frio": (30.0, 30.0),
    "nellie bly": (30.0, 36.0),
    "frontier": (31.0, 34.0),
    "springer": (33.0, 33.0),
    "frio (14 cores)": (30.0, 38.0),
    "torpedo": (34.0, 37.0),
    "tensleep": (40.0, 50.0),
    "canyon reef": (50.0, 50.0),
}

TABLE_AVG_PCT = 30.0


def lookup_sgr(rock_name: str) -> SgrLookupResult:
    """Return representative Sgr for a rock type from Table 3.3.

    Args:
        rock_name: Rock type (case-insensitive). Falls back to the
            table-wide average if unknown.

    Returns:
        SgrLookupResult.

    Raises:
        ValueError: if rock_name is empty.
    """
    if not isinstance(rock_name, str) or not rock_name.strip():
        raise ValueError(f"rock_name must be non-empty, got {rock_name!r}")
    key = rock_name.strip().lower()
    if key in _SGR_TABLE:
        lo, hi = _SGR_TABLE[key]
        mid = 0.5 * (lo + hi)
        return SgrLookupResult(
            Sgr=mid / 100.0, Sgr_pct=mid,
            used_table_average=False, rock_name_resolved=key,
        )
    return SgrLookupResult(
        Sgr=TABLE_AVG_PCT / 100.0, Sgr_pct=TABLE_AVG_PCT,
        used_table_average=True, rock_name_resolved="[table average]",
    )


def list_rocks() -> list[str]:
    """Return the sorted list of recognized rock names."""
    return sorted(_SGR_TABLE.keys())
