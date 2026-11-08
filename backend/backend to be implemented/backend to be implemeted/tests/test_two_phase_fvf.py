import pytest
from app.reservoir.two_phase_fvf import two_phase_fvf


class TestExample51:
    """Example 5.1 (p. 156): Bo=1.520, Bg=0.00102, Rsoi=1100,
    Rso=900 -> Bt = 1.724."""
    def test_bt(self):
        r = two_phase_fvf(1.520, 0.00102, 1100.0, 900.0)
        assert r.Bt_bbl_stb == pytest.approx(1.724, rel=1e-6)
        assert r.free_gas_term_bbl_stb == pytest.approx(0.204, rel=1e-6)


class TestAtBubblePoint:
    """Above Pb, Rso=Rsoi, so Bt=Bo."""
    def test_identity(self):
        r = two_phase_fvf(1.35, 0.0015, 600.0, 600.0)
        assert r.Bt_bbl_stb == pytest.approx(1.35, rel=1e-12)
        assert r.Rso_gt_Rsoi is False


class TestValidation:
    def test_bo_zero(self):
        with pytest.raises(ValueError, match="Bo must be > 0"):
            two_phase_fvf(0.0, 0.001, 600.0, 500.0)
    def test_rso_negative(self):
        with pytest.raises(ValueError, match="Rso must be >= 0"):
            two_phase_fvf(1.35, 0.001, 600.0, -1.0)
