"""Tests for CalculationResult, registry, validation."""
import pytest

from app.reservoir.common.calculation_result import (
    CalculationResult, Correlation)
from app.reservoir.common import correlations, validation


def test_calc_result_constructs():
    cor = Correlation(name="t", reference="r", validity="v",
                      assumptions=["a"])
    r = CalculationResult(value=42.0, correlation=cor, inputs={"x": 1.0})
    assert r.value == 42.0
    assert r.warnings == []


def test_to_method_panel():
    cor = Correlation(name="t", reference="r", validity="v")
    r = CalculationResult(value=1.0, correlation=cor, inputs={})
    p = r.to_method_panel()
    assert set(p.keys()) == {"name", "reference", "validity",
                             "assumptions", "warnings"}


def test_registry_roundtrip():
    c = Correlation(name="unit_test_corr", reference="x", validity="y")
    correlations.register(c)
    assert "unit_test_corr" in correlations.list_all()
    assert correlations.get("unit_test_corr").name == "unit_test_corr"


def test_registry_unknown_raises():
    with pytest.raises(KeyError):
        correlations.get("not_registered_corr")


def test_check_range_inside():
    assert validation.check_range("x", 35, 15, 50) is None


def test_check_range_outside():
    w = validation.check_range("x", 60, 15, 50)
    assert w is not None and "outside validity range" in w


def test_check_all_collects_warnings():
    ws = validation.check_all({"a": (0, 10), "b": (0, 10)},
                              {"a": 5, "b": 20})
    assert len(ws) == 1 and "b=20" in ws[0]