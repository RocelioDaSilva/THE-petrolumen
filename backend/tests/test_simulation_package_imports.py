import os
import subprocess
import sys
from pathlib import Path


def test_black_oil_api_import_does_not_require_optional_simulation_engines():
    backend_path = Path(__file__).resolve().parents[1]
    script = """
import builtins
import sys

original_import = builtins.__import__

def import_without_optional_engines(name, *args, **kwargs):
    if name.split(".", 1)[0] in {"tensorflow", "pyvista"}:
        raise ModuleNotFoundError(f"No module named {name!r}")
    return original_import(name, *args, **kwargs)

builtins.__import__ = import_without_optional_engines
sys.path.insert(0, sys.argv[1])
from app.engines.reservoir.simulation import BlackOilSimulator
assert BlackOilSimulator.__name__ == "BlackOilSimulator"
assert "tensorflow" not in sys.modules
assert "pyvista" not in sys.modules
"""
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    subprocess.run(
        [sys.executable, "-c", script, str(backend_path)],
        check=True,
        env=environment,
        capture_output=True,
        text=True,
    )
