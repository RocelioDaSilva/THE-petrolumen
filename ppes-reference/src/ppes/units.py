"""Unit conversions per the book's Appendix A (p. 281).

The book's equations embed unit-specific constants (141.2, 162.6, 8074,
18.062, etc.). Each public function in this package documents the units
it expects. Only the common helpers are centralized here.
"""
from __future__ import annotations
from enum import Enum


class UnitSystem(str, Enum):
    FIELD = "field"   # psia, Â°F, stb/day, scf/stb, ft, in, lbm/ft3, cp, md
    SI    = "SI"      # kPa,  Â°C, m3/day, m3/m3, m, mm, kg/m3, PaÂ·s, mD


def api_to_sg(api: float) -> float:
    """Eq. 2.3 (p. 2/20): gamma_o = 141.5 / (API + 131.5)."""
    return 141.5 / (api + 131.5)


def sg_to_api(gamma_o: float) -> float:
    """Eq. 2.3 inverted."""
    return 141.5 / gamma_o - 131.5


CONVERSIONS = {
    ("ft", "m"): 0.3048,
    ("m", "ft"): 3.28084,
    ("in", "mm"): 25.4,
    ("bbl", "m3"): 0.158987,
    ("m3", "bbl"): 6.28981,
    ("psi", "kPa"): 6.89476,
    ("kPa", "psi"): 0.145038,
    ("cp", "Pa_s"): 0.001,
    ("md", "m2"): 9.86923e-16,
}


def convert(value: float, from_unit: str, to_unit: str) -> float:
    """Convert between common units using Appendix A factors."""
    if from_unit == "F" and to_unit == "C":
        return (value - 32.0) * 5.0 / 9.0
    if from_unit == "C" and to_unit == "F":
        return value * 9.0 / 5.0 + 32.0
    if from_unit == "R" and to_unit == "K":
        return value * 5.0 / 9.0
    if from_unit == "K" and to_unit == "R":
        return value * 9.0 / 5.0
    key = (from_unit, to_unit)
    if key not in CONVERSIONS:
        raise KeyError(f"No conversion {from_unit} -> {to_unit}")
    return value * CONVERSIONS[key]