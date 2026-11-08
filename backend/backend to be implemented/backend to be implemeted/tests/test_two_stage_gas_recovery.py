import pytest
from app.reservoir.two_stage_gas_recovery import two_stage_gas_recovery


class TestExample32:
    """Example 3.2 (p. 81): total = 5734 MM SCF at ps=2500, RF = 56%.
    Tolerance 1%."""
    def test_total(self):
        r = two_stage_gas_recovery(
            0.22, 0.23, 0.34, 0.00533, 0.00667, 0.03623, 6400.0,
        )
        assert r.gp_total_scf / 1e6 == pytest.approx(5734.0, rel=0.01)
        assert r.rf_total_pct == pytest.approx(56.0, abs=1.0)


class TestPureCompleteDrive:
    """ps=pi -> no Stage 1 -> pure water-drive recovery."""
    def test_no_stage1(self):
        r = two_stage_gas_recovery(
            0.22, 0.23, 0.34, 0.00533, 0.00533, 0.03623, 6400.0,
        )
        assert r.gp_stage1_scf == pytest.approx(0.0, abs=1.0)
        assert r.rf_total_pct > 0.0
