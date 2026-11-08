import pytest
from app.reservoir.abandonment import abandonment_gas

class TestVolumetric:
    """10 BCF, pi/zi=3000, pa/za=300 -> Gp,a=9 BCF, RF=90%."""
    def test_values(self):
        r = abandonment_gas(10e9, 3000.0, 300.0)
        assert r.Gp_at_abandonment_scf == pytest.approx(9e9, rel=1e-9)
        assert r.RF_at_abandonment == pytest.approx(0.90, rel=1e-9)
        assert r.method == "volumetric"

class TestWaterDriveSupplied:
    def test_uses_supplied(self):
        r = abandonment_gas(10e9, 3000.0, 300.0,
                            water_drive_Gpa_scf=8.5e9)
        assert r.Gp_at_abandonment_scf == pytest.approx(8.5e9, rel=1e-9)
        assert r.RF_at_abandonment == pytest.approx(0.85, rel=1e-9)
        assert r.method == "water_drive_supplied"

class TestValidation:
    def test_pa_ge_pi(self):
        with pytest.raises(ValueError, match="pa_over_za"):
            abandonment_gas(10e9, 3000.0, 3000.0)
