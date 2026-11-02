from typing import Literal

UnitSystem = Literal["field", "metric"]


def convert(value: float, from_unit: str, to_unit: str) -> float:
    """Port of src/lib/units.ts convert function.

    Preserves exact conversion factors and bi-directional conversions.
    """
    if from_unit == to_unit or not isinstance(value, (int, float)):
        return float(value)

    # Pressure
    if from_unit in ("psi", "psia") and to_unit == "kPa":
        return value * 6.89476
    if from_unit == "kPa" and to_unit in ("psi", "psia"):
        return value / 6.89476
    if from_unit in ("psi", "psia") and to_unit == "bar":
        return value * 0.0689476
    if from_unit == "bar" and to_unit in ("psi", "psia"):
        return value / 0.0689476
    if from_unit in ("psi", "psia") and to_unit == "MPa":
        return value * 0.00689476
    if from_unit == "MPa" and to_unit in ("psi", "psia"):
        return value / 0.00689476

    # Temperature
    if from_unit == "F" and to_unit == "C":
        return ((value - 32.0) * 5.0) / 9.0
    if from_unit == "C" and to_unit == "F":
        return (value * 9.0) / 5.0 + 32.0

    # Flow rate
    if from_unit in ("STB/d", "bbl/day", "bbl/d") and to_unit in ("m3/d", "m3/day"):
        return value * 0.1589873
    if from_unit in ("m3/d", "m3/day") and to_unit in ("STB/d", "bbl/day", "bbl/d"):
        return value / 0.1589873
    if from_unit == "Mscf/d" and to_unit in ("m3/d", "m3/day"):
        return value * 28.3168

    # Volume
    if from_unit == "bbl" and to_unit == "m3":
        return value * 0.1589873
    if from_unit == "m3" and to_unit == "bbl":
        return value / 0.1589873
    if from_unit == "scf" and to_unit == "m3":
        return value * 0.0283168
    if from_unit == "m3" and to_unit == "scf":
        return value / 0.0283168

    # Length
    if from_unit == "ft" and to_unit == "m":
        return value * 0.3048
    if from_unit == "m" and to_unit == "ft":
        return value / 0.3048
    if from_unit == "in" and to_unit == "mm":
        return value * 25.4
    if from_unit == "mm" and to_unit == "in":
        return value / 25.4

    # Density
    if from_unit in ("lb/gal", "ppg") and to_unit in ("kg/m3", "kg/m²"):
        return value * 119.826
    if from_unit in ("kg/m3", "kg/m²") and to_unit in ("lb/gal", "ppg"):
        return value / 119.826
    if from_unit in ("lb/gal", "ppg") and to_unit == "g/cm3":
        return value * 0.119826
    if from_unit == "g/cm3" and to_unit in ("lb/gal", "ppg"):
        return value / 0.119826

    # Viscosity (1 cP = 1 mPa·s)
    if from_unit == "cP" and to_unit == "mPa·s":
        return value
    if from_unit == "mPa·s" and to_unit == "cP":
        return value

    # Permeability
    if from_unit == "mD" and to_unit == "m2":
        return value * 9.869233e-16
    if from_unit == "m2" and to_unit == "mD":
        return value / 9.869233e-16

    return value
