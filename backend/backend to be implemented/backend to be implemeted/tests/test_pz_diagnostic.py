import pytest
from app.reservoir.pz_diagnostic import pz_diagnostic

class TestVolumetric:
    def test_straight_line(self):
        pts = [(3000.0, 0.0), (2800.0, 200.0e6), (2600.0, 400.0e6),
               (2400.0, 600.0e6)]
        r = pz_diagnostic(pts)
        assert r.classification == "volumetric"
        assert r.linear_r2 > 0.999

class TestWaterDrive:
    def test_curved(self):
        # Strongly curved: c large relative to b
        pts = [(3000.0, 0.0), (2900.0, 200.0e6), (2700.0, 400.0e6),
               (2400.0, 600.0e6)]
        r = pz_diagnostic(pts)
        assert r.classification in ("partial_water_drive",
                                    "complete_water_drive")

class TestValidation:
    def test_too_few(self):
        with pytest.raises(ValueError, match="at least 4"):
            pz_diagnostic([(3000.0, 0.0), (2800.0, 200.0e6)])
