"""Plotting and visualization helpers for engineering results."""

from importlib import import_module
from typing import Any

_LAZY_EXPORTS = {
    "AdvancedVisualization": ".advanced_visualization",
    "ResultsVisualizer": ".results_visualizer",
    "Visualizer3D": ".visualizer3d",
}

__all__ = list(_LAZY_EXPORTS)


def __getattr__(name: str) -> Any:
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value