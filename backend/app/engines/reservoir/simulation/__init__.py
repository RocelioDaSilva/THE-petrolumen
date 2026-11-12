from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORTS = {
    "AdvancedSimulation": "advanced_simulation",
    "BlackOilSimulator": "black_oil_simulator",
    "CommercialSimulator": "commercial_simulator",
    "Component": "compositional_modeling",
    "CompositionalModel": "compositional_modeling",
    "EquationOfState": "compositional_modeling",
    "FlashCalculation": "compositional_modeling",
    "PengRobinsonEOS": "compositional_modeling",
    "CompositionalSimulator": "compositional_simulator",
    "EORSimulator": "eor_simulator",
    "ThermalSimulator": "thermal_simulator",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    value = getattr(import_module(f".{module_name}", __name__), name)
    globals()[name] = value
    return value
