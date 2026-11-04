"""Input validation and validity-range checking."""
from __future__ import annotations


def check_range(name: str, value: float, lo: float, hi: float,
                inclusive: bool = True) -> str | None:
    inside = (lo <= value <= hi) if inclusive else (lo < value < hi)
    if not inside:
        return (f"{name}={value:.4g} is outside validity range "
                f"[{lo:.4g}, {hi:.4g}]")
    return None


def check_all(ranges: dict[str, tuple[float, float]],
              values: dict[str, float]) -> list[str]:
    warnings = []
    for k, (lo, hi) in ranges.items():
        if k in values:
            w = check_range(k, values[k], lo, hi)
            if w:
                warnings.append(w)
    return warnings