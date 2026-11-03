"""Reservoir modeling and uncertainty-analysis engines."""
"""Static, thermal, geomechanical, and uncertainty modeling engines."""

from importlib import import_module
from typing import Any

_LAZY_EXPORTS = {
    "FractureModel": ".geomechanics",
    "GeomechanicalModel": ".geomechanics",
    "StaticModeling": ".static_modeling",
    "SteamInjectionModel": ".thermal_modeling",
    "ThermalModel": ".thermal_modeling",
    "UncertaintyAnalysis": ".uncertainty_analysis",
    "WorkflowAutomation": ".workflow_automation",
}

__all__ = list(_LAZY_EXPORTS)


def __getattr__(name: str) -> Any:
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value
