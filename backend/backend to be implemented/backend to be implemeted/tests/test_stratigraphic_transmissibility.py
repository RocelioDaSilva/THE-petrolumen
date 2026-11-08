import numpy as np
import pytest
from app.reservoir.stratigraphic_transmissibility import (
    stratigraphic_transmissibility,
)

class TestFlatEquivalent:
    """Flat layers should reproduce the standard formula."""
    def test_flat(self):
        Z = np.zeros((2, 2, 2))
        Z[:, :, 0] = 0.0
        Z[:, :, 1] = 10.0
        k = np.full((2, 2, 1), 100.0)
        r = stratigraphic_transmissibility(Z, k, 100.0, 100.0)
        assert r.TX[0, 0, 0] == pytest.approx(1000.0)
        assert r.hz_min == 10.0

class TestDipping:
    """Dipping layer: hz varies with (i,j)."""
    def test_dip(self):
        Z = np.zeros((2, 2, 2))
        Z[0, :, 1] = 5.0
        Z[1, :, 1] = 15.0
        k = np.full((2, 2, 1), 100.0)
        r = stratigraphic_transmissibility(Z, k, 100.0, 100.0)
        assert r.TX[0, 0, 0] == pytest.approx(5.0 * 100.0)
        assert r.TX[1, 0, 0] == pytest.approx(0.0)
        assert r.hz_min == 5.0
        assert r.hz_max == 15.0

class TestPinchOut:
    def test_zero_hz(self):
        Z = np.zeros((2, 2, 2))
        Z[:, :, 1] = 0.0
        k = np.full((2, 2, 1), 100.0)
        with pytest.raises(ValueError, match="pinch-out"):
            stratigraphic_transmissibility(Z, k, 100.0, 100.0)
