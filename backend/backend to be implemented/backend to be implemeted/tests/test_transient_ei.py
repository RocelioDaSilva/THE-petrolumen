import math
import pytest
from scipy.special import expi
from app.reservoir.transient_ei import transient_line_source


class TestBookExample:
    """Book p. 237: pi=3000, q=200, mu=0.72, B=1.475, k=100, h=15,
    phi=0.234, ct=15e-6, r=1000, t=240 -> p=2981.8 psia."""
    def test_pressure(self):
        r = transient_line_source(
            3000.0, 200.0, 0.72, 1.475, 100.0, 15.0,
            0.234, 15e-6, 1000.0, 240.0,
        )
        assert r.p_psia == pytest.approx(2981.8, rel=0.002)
        assert r.used_log_approx is False


class TestLogApproxBranch:
    def test_small_x_uses_log(self):
        # Make x tiny by large t
        r = transient_line_source(
            3000.0, 200.0, 0.72, 1.475, 100.0, 15.0,
            0.234, 15e-6, 1.0, 1e6,
        )
        assert r.used_log_approx is True


class TestValidation:
    def test_r_zero(self):
        with pytest.raises(ValueError, match="r_ft must be > 0"):
            transient_line_source(
                3000.0, 200.0, 0.72, 1.475, 100.0, 15.0,
                0.234, 15e-6, 0.0, 240.0,
            )
    def test_t_zero(self):
        with pytest.raises(ValueError, match="t_hr must be > 0"):
            transient_line_source(
                3000.0, 200.0, 0.72, 1.475, 100.0, 15.0,
                0.234, 15e-6, 1000.0, 0.0,
            )
