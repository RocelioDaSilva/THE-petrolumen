"""Appendix A -- unit conversions."""
from enum import Enum

class UnitSystem(str, Enum):
    FIELD = "field"
    SI = "SI"

def api_to_sg(api: float) -> float:
    """Eq. 2.3."""
    return 141.5 / (api + 131.5)

def sg_to_api(gamma_o: float) -> float:
    """Eq. 2.3 inverted."""
    return 141.5 / gamma_o - 131.5

CONVERSIONS = {
    ("ft","m"): 0.3048, ("m","ft"): 3.2808,
    ("in","mm"): 25.4,
    ("bbl","m3"): 0.158987, ("m3","bbl"): 6.2898,
    ("psi","kPa"): 6.89476, ("kPa","psi"): 0.145038,
    ("cp","Pa_s"): 0.001,
    ("md","m2"): 9.86923e-16,
    ("F","C"): lambda f: (f-32)*5/9,
    ("C","F"): lambda c: c*9/5+32,
    ("R","K"): lambda r: r*5/9,
    ("K","R"): lambda k: k*9/5,
}

def convert(value: float, from_unit: str, to_unit: str) -> float:
    key = (from_unit, to_unit)
    if key not in CONVERSIONS:
        raise KeyError(f"No conversion {from_unit}->{to_unit}")
    f = CONVERSIONS[key]
    return f(value) if callable(f) else value * f
