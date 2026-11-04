"""Fully implicit

TODO (Phase 7, Step 7.5): implement per playbook.
"""
from __future__ import annotations
from ..common.calculation_result import CalculationResult, Correlation
from ..common.correlations import register


def placeholder(*args, **kwargs) -> CalculationResult:
    raise NotImplementedError("Phase 7, Step 7.5")