import sys
from types import ModuleType

import pytest

from app.engines.analytics.data_integration import DataIntegration


def test_import_eclipse_grid_uses_optional_libecl(tmp_path, monkeypatch):
    grid_file = tmp_path / "CASE.DATA"
    grid_file.write_text("grid")
    libecl = ModuleType("libecl")

    class FakeGrid:
        dims = (2, 3, 4)

        def __init__(self, path):
            assert path == str(grid_file)

        def get_num_active(self):
            return 20

        def get_num_global(self):
            return 24

    libecl.EclGrid = FakeGrid
    monkeypatch.setitem(sys.modules, "libecl", libecl)

    integration = DataIntegration()
    result = integration.import_eclipse_data(str(grid_file), "grid")

    assert result == {
        "grid": result["grid"],
        "dimensions": (2, 3, 4),
        "active_cells": 20,
        "total_cells": 24,
    }
    assert integration.grid_data is result


def test_import_eclipse_properties_selects_records_and_rejects_missing_names(
    tmp_path, monkeypatch
):
    property_file = tmp_path / "CASE.INIT"
    property_file.write_text("properties")
    libecl = ModuleType("libecl")
    values = {"PORO": [0.2, 0.3], "PERMX": [100.0, 200.0]}

    class FakeEclFile:
        def __init__(self, path):
            assert path == str(property_file)

        def keys(self):
            return values.keys()

        def __getitem__(self, name):
            return [values[name]]

    libecl.EclFile = FakeEclFile
    monkeypatch.setitem(sys.modules, "libecl", libecl)

    integration = DataIntegration()
    result = integration.import_eclipse_data(
        str(property_file), "properties", ["PORO"]
    )

    assert result == {"PORO": values["PORO"]}
    assert integration.eclipse_properties == result
    with pytest.raises(KeyError, match="MISSING"):
        integration.import_eclipse_properties(str(property_file), ["MISSING"])
    assert integration.eclipse_properties == result


def test_import_eclipse_grid_reports_missing_optional_dependency(tmp_path, monkeypatch):
    grid_file = tmp_path / "CASE.DATA"
    grid_file.write_text("grid")
    monkeypatch.setitem(sys.modules, "libecl", None)

    with pytest.raises(ImportError, match="libecl is required"):
        DataIntegration().import_eclipse_grid(str(grid_file))
