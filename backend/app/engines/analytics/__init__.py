"""Time series, statistical, and ML analytics engines."""

from importlib import import_module
from typing import Any

from .event_detection import detect_zscore
from .sequences import create_sequences, normalize_timeseries

_LAZY_EXPORTS = {
    "AdvancedDataAnalysis": ".advanced_analytics",
    "AISeismicAnalysis": ".ai_seismic",
    "DataAnalytics": ".data_analytics",
    "DataIntegration": ".data_integration",
}

__all__ = [
    "AdvancedDataAnalysis",
    "AISeismicAnalysis",
    "DataAnalytics",
    "DataIntegration",
    "create_sequences",
    "detect_zscore",
    "normalize_timeseries",
]


def __getattr__(name: str) -> Any:
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value
