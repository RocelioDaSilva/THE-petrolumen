"""Global registry of every reservoir correlation.

The UI reads from this to populate the method selector.
"""
from __future__ import annotations

from .calculation_result import Correlation


_REGISTRY: dict[str, Correlation] = {}


def register(correlation: Correlation) -> Correlation:
    _REGISTRY[correlation.name] = correlation
    return correlation


def get(name: str) -> Correlation:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown correlation: {name}")
    return _REGISTRY[name]


def list_all() -> list[str]:
    return sorted(_REGISTRY.keys())


def list_by_domain(domain: str) -> list[str]:
    return [n for n in _REGISTRY if n.startswith(domain)]