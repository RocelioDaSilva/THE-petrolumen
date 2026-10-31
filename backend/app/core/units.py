from typing import Literal

UnitSystem = Literal["field", "metric"]


def convert(value: float, from_unit: str, to_unit: str) -> float:
    """Port of src/lib/units.ts convert function.

    Preserves exact conversion factors and behavior.
    """
    if from_unit == to_unit:
        return value

    # Pressure
    if from_unit == "psi" and to_unit == "kPa":
        return value * 6.89476
    if from_unit == "kPa" and to_unit == "psi":
        return value / 6.89476
    if from_unit == "psi" and to_unit == "bar":
        return value * 0.0689476
    if from_unit == "bar" and to_unit == "psi":
        return value / 0.0689476

    # Temperature
    if from_unit == "F" and to_unit == "C":
        return ((value - 32.0) * 5.0) / 9.0
    if from_unit == "C" and to_unit == "F":
        return (value * 9.0) / 5.0 + 32.0

    # Flow rate
    if from_unit == "STB/d" and to_unit == "m3/d":
        return value * 0.158987
    if from_unit == "m3/d" and to_unit == "STB/d":
        return value / 0.158987
    if from_unit == "Mscf/d" and to_unit == "m3/d":
        return value * 28.3168

    # Volume
    if from_unit == "bbl" and to_unit == "m3":
        return value * 0.158987
    if from_unit == "m3" and to_unit == "bbl":
        return value / 0.158987
    if from_unit == "scf" and to_unit == "m3":
        return value * 0.0283168

    # Length
    if from_unit == "ft" and to_unit == "m":
        return value * 0.3048
    if from_unit == "m" and to_unit == "ft":
        return value / 0.3048

    return value
