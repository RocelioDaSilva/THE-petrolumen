"""Production and reservoir prediction engines."""

from importlib import import_module
from typing import Any

__all__ = ["AIPrediction"]


def __getattr__(name: str) -> Any:
    if name != "AIPrediction":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(".ai_prediction", __name__), name)
    globals()[name] = value
    return value