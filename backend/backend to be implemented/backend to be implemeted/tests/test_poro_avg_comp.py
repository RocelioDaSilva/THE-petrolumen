import pytest
from app.reservoir.poro_avg_comp import poro_avg_compressibility

class TestChinExample:
    """Chin p. 65: 99% porous -> fluid dominated; 1% porous -> rock
    dominated."""
    def test_high_porosity(self):
        r = poro_avg_compressibility(0.99, 1e-5, 1e-6)
        assert r.fluid_fraction > 0.9
    def test_low_porosity(self):
        r = poro_avg_compressibility(0.01, 1e-5, 1e-6)
        assert r.rock_fraction > 0.9

class TestExactValue:
    def test_mid(self):
        r = poro_avg_compressibility(0.5, 1e-5, 1e-6)
        assert r.c_eff_psi_inv == pytest.approx(5.5e-6)

class TestValidation:
    def test_phi_zero(self):
        with pytest.raises(ValueError, match="phi must be in"):
            poro_avg_compressibility(0.0, 1e-5, 1e-6)
