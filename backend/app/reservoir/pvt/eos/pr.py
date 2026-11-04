"""Peng-Robinson EoS

TODO (Phase 2, Step 2.6): implement per playbook.
"""
from __future__ import annotations
from ..common.calculation_result import CalculationResult, Correlation
from ..common.correlations import register


def placeholder(*args, **kwargs) -> CalculationResult:
    raise NotImplementedError("Phase 2, Step 2.6")