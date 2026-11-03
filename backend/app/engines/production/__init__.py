"""Production analysis, optimization, and economic evaluation engines."""

from importlib import import_module
from typing import Any

from .economic_analysis import EconomicAnalysis

_LAZY_EXPORTS = {
    "FlowHistoryMatching": ".flow_history_matching",
    "HistoryMatching": ".history_matching",
    "ProductionAnalysis": ".production_analysis",
    "ProductionForecasting": ".production_forecasting",
    "ProductionOptimization": ".production_optimization",
    "ReservesEstimate": ".reserves_evaluation",
    "ReservesEvaluation": ".reserves_evaluation",
    "ReserveCategory": ".reserves_evaluation",
}

__all__ = ["EconomicAnalysis", *_LAZY_EXPORTS]


def __getattr__(name: str) -> Any:
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value
