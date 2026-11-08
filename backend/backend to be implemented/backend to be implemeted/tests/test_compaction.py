import pytest
from app.reservoir.compaction import compaction_porosity

class TestEkofiskScale:
    def test_compaction(self):
        r = compaction_porosity(0.30, -5e-6, 3000.0)
        assert r.phi_actual < 0.30
        assert r.compaction_compressibility_per_psi == pytest.approx(5e-6)

class TestNoCompaction:
    def test_a_zero(self):
        r = compaction_porosity(0.25, 0.0, 3000.0)
        assert r.phi_actual == 0.25
        assert r.delta_phi == 0.0

class TestNonPhysical:
    def test_a_times_p_very_negative(self):
        with pytest.raises(ValueError, match="phi_actual"):
            compaction_porosity(0.25, -1e-3, 2000.0)

class TestValidation:
    def test_phi_out(self):
        with pytest.raises(ValueError, match="phi_baseline"):
            compaction_porosity(1.2, -5e-6, 3000.0)
    def test_p_zero(self):
        with pytest.raises(ValueError, match="p_psia must be > 0"):
            compaction_porosity(0.25, -5e-6, 0.0)
