"""Every reservoir calculation returns a CalculationResult.

The CalculationResult carries the numerical answer PLUS the metadata
that the UI Method Panel, the audit trail, and the bilingual
Worked-Solution view all consume. Never return a bare number.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Correlation:
    """Metadata for a correlation or correlation set."""
    name: str
    reference: str
    validity: str
    assumptions: list[str] = field(default_factory=list)


@dataclass
class CalculationResult:
    """Result of any reservoir calculation."""
    value: Any
    correlation: Correlation
    inputs: dict[str, Any]
    intermediate: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0

    def to_method_panel(self) -> dict:
        return {
            "name": self.correlation.name,
            "reference": self.correlation.reference,
            "validity": self.correlation.validity,
            "assumptions": self.correlation.assumptions,
            "warnings": self.warnings,
        }

    def to_step_by_step(self) -> list[dict]:
        return [{"step": k, "value": v} for k, v in self.intermediate.items()]