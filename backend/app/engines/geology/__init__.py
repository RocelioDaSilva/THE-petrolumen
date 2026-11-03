"""Geological models, gridding, geostatistics, and rock characterization."""

from importlib import import_module
from typing import Any

_LAZY_EXPORTS = {
    "DigitalRockAnalysis": ".digital_rock",
    "GeologicalModel3D": ".model3d",
    "Geostatistics": ".geostatistics",
    "Grid3D": ".mesh",
    "Mesh": ".mesh",
    "NMRAnalysis": ".nmr_analysis",
    "PetrophysicalMapping": ".petrophysics",
    "ReservoirCharacterization": ".reservoir_characterization",
    "SensitivityAnalysis": ".sensitivity",
    "SeismicIntegration": ".seismic_integration",
}

__all__ = list(_LAZY_EXPORTS)


def __getattr__(name: str) -> Any:
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value