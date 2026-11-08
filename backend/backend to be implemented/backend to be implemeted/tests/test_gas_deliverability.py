import pytest
from app.reservoir.gas_deliverability import gas_well_deliverability


class TestBasic:
    """Well produces at q; pwf should be below pi and above 0."""
    def test_pwf_in_range(self):
        tbl = [(14.7, 0.011, 0.998), (2000.0, 0.015, 0.870),
               (4000.0, 0.021, 0.920)]
        r = gas_well_deliverability(
            4000.0, 5e6, 200.0, 10.0, 20.0, 0.15, 15e-6,
            0.3, 240.0, tbl,
        )
        assert 0.0 < r.pwf_psia < 4000.0
        assert r.dp_drawdown_psi > 0.0


class TestValidation:
    def test_q_zero(self):
        with pytest.raises(ValueError, match="q_scf_d"):
            gas_well_deliverability(
                3000.0, 0.0, 150.0, 10.0, 20.0, 0.15, 15e-6,
                0.3, 240.0, [(14.7, 0.011, 1.0), (3000.0, 0.02, 0.9)],
            )
