import pytest
from app.reservoir.gc_water_drive import gc_water_drive_recovery


class TestTable49:
    """Table 4.9 (p. 137): Swi=0.30, Sgr=0.20, F=0.80 -> 57.1%."""
    def test_recovery(self):
        r = gc_water_drive_recovery(0.30, 0.20, 0.80)
        assert r.recovery == pytest.approx(0.571, rel=0.01)
        assert r.out_of_physical_range is False


class TestValidation:
    def test_swi_plus_sgr(self):
        with pytest.raises(ValueError, match="Swi \\+ Sgr"):
            gc_water_drive_recovery(0.70, 0.40, 0.80)
    def test_F_out_of_range(self):
        with pytest.raises(ValueError, match="F_invaded"):
            gc_water_drive_recovery(0.30, 0.20, 1.5)


class TestMonotonic:
    def test_F_increases_recovery(self):
        a = gc_water_drive_recovery(0.30, 0.20, 0.40)
        b = gc_water_drive_recovery(0.30, 0.20, 0.90)
        assert b.recovery > a.recovery
