import runpy
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest

from app.engines.reservoir.simulation.history_matcher import HistoryMatcher


class QuadraticSimulator:
    def run_simulation(self, parameters):
        return {"pressure": np.array([parameters["permeability"]])}


def test_history_matcher_maps_optimizer_vector_to_named_parameters():
    matcher = HistoryMatcher(
        QuadraticSimulator(), {"pressure": np.array([3.0])}
    )
    matcher.add_parameter("permeability", 0.0, 10.0, 1.0)

    result = matcher.run_matching(max_iterations=100)

    assert result["success"]
    assert result["parameters"]["permeability"] == pytest.approx(3.0, abs=1e-4)
    assert result["misfit"] == pytest.approx(0.0, abs=1e-8)
    assert matcher.parameters["permeability"]["current"] == pytest.approx(3.0, abs=1e-4)


def test_history_matcher_uncertainty_reports_sample_statistics():
    matcher = HistoryMatcher(
        QuadraticSimulator(), {"pressure": np.array([3.0])}
    )
    matcher.add_parameter("permeability", 0.0, 10.0, 1.0)

    result = matcher.analyze_uncertainty(n_samples=50, random_state=4)

    assert result["pressure"]["mean"].shape == (1,)
    assert result["pressure"]["p10"][0] <= result["pressure"]["p50"][0]
    assert result["pressure"]["p50"][0] <= result["pressure"]["p90"][0]


def _load_mesh_module():
    pyvista = ModuleType("pyvista")
    pyvista.CellType = SimpleNamespace(HEXAHEDRON=12, TETRA=10, TRIANGLE=5)
    mesh_path = (
        Path(__file__).parents[1]
        / "app"
        / "engines"
        / "geology"
        / "mesh.py"
    )
    with patch.dict(sys.modules, {"pyvista": pyvista}):
        return runpy.run_path(str(mesh_path))


def test_structured_mesh_connectivity_handles_non_cubic_grid():
    mesh_module = _load_mesh_module()
    mesh = mesh_module["Mesh"]()

    mesh.create_structured_mesh(2, 1, 3, 2.0, 3.0, 4.0)

    first_cell = mesh.vertices[mesh.cells[0]]
    second_cell = mesh.vertices[mesh.cells[1]]
    np.testing.assert_allclose(first_cell.min(axis=0), [0.0, 0.0, 0.0])
    np.testing.assert_allclose(first_cell.max(axis=0), [2.0, 3.0, 4.0])
    np.testing.assert_allclose(second_cell.min(axis=0), [2.0, 0.0, 0.0])
    np.testing.assert_allclose(second_cell.max(axis=0), [4.0, 3.0, 4.0])
    np.testing.assert_allclose(mesh.volumes[:2], [24.0, 24.0])


def test_grid3d_supports_variable_positive_cell_widths():
    grid_type = _load_mesh_module()["Grid3D"]
    grid = grid_type(
        2,
        2,
        1,
        np.array([1.0, 2.0]),
        np.array([3.0, 4.0]),
        2.0,
    )

    assert grid.get_cell_volume(0, 0, 0) == pytest.approx(6.0)
    assert grid.get_cell_volume(1, 1, 0) == pytest.approx(16.0)
    assert grid.get_face_area(1, 1, 0, "x+") == pytest.approx(8.0)
    np.testing.assert_allclose(grid.nodes[2, 2, 1], [3.0, 7.0, 2.0])

    with pytest.raises(ValueError):
        grid_type(2, 1, 1, [1.0], 1.0, 1.0)
