import pytest
from app.reservoir.storage_split import storage_gas_split


class TestTypical:
    """10 BCF at p/z=4000; base p/z=2000; max p/z=4500 (over-pressure).
    base = 10*2000/4000 = 5 BCF; max = 10*4500/4000 = 11.25 BCF;
    working = 6.25 BCF; unused = 0."""
    def test_values(self):
        r = storage_gas_split(10e9, 4000.0, 2000.0, 4500.0)
        assert r.base_gas_scf == pytest.approx(5e9, rel=1e-9)
        assert r.working_gas_scf == pytest.approx(6.25e9, rel=1e-9)
        assert r.unused_gas_scf == 0.0


class TestUnderfilled:
    """max p/z below initial: unused > 0."""
    def test_unused(self):
        r = storage_gas_split(10e9, 4000.0, 2000.0, 3500.0)
        # max = 10*3500/4000 = 8.75 BCF; unused = 1.25 BCF
        assert r.unused_gas_scf == pytest.approx(1.25e9, rel=1e-9)


class TestValidation:
    def test_base_ge_max(self):
        with pytest.raises(ValueError, match="base_pz"):
            storage_gas_split(10e9, 4000.0, 4000.0, 3500.0)
