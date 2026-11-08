import pytest
from app.reservoir.cycling_recovery import cycling_recovery


class TestBookExample:
    """Book p. 135: 0.80 * 0.80 * 0.80 = 0.512."""
    def test_value(self):
        r = cycling_recovery(0.80, 0.80, 0.80)
        assert r.E_total == pytest.approx(0.512, rel=1e-9)


class TestSensitivity:
    def test_sens_d(self):
        r = cycling_recovery(0.80, 0.80, 0.80)
        assert r.sens_E_d == pytest.approx(0.64, rel=1e-9)


class TestValidation:
    def test_out_of_range(self):
        with pytest.raises(ValueError, match="E_d must be in"):
            cycling_recovery(1.5, 0.80, 0.80)
