import pytest
from app.reservoir.three_stage_ge import three_stage_total_gp


class TestBookExample:
    """Book p. 92: Gps=6.0 MM, Gss=0.3 MM, Gst=0.021 MM, Np=100,
    gamma_o=0.780, M_wo=138 -> GE=752, Gp=6.396 MM SCF/day."""
    def test_gp(self):
        r = three_stage_total_gp(
            6.0e6, 0.3e6, 0.021e6, 100.0,
            gamma_o=0.780, M_wo=138.0,
        )
        assert r.GE_scf_per_bbl == pytest.approx(752.0, rel=0.01)
        assert r.Gp_total_scf == pytest.approx(6.396e6, rel=0.01)


class TestTwoStage:
    """Two-stage drops Gss."""
    def test_two_stage(self):
        r = three_stage_total_gp(
            6.0e6, 0.3e6, 0.021e6, 100.0,
            gamma_o=0.780, M_wo=138.0, two_stage=True,
        )
        # Difference should equal Gss
        r3 = three_stage_total_gp(
            6.0e6, 0.3e6, 0.021e6, 100.0,
            gamma_o=0.780, M_wo=138.0, two_stage=False,
        )
        assert r3.Gp_total_scf - r.Gp_total_scf == pytest.approx(0.3e6, rel=1e-9)


class TestValidation:
    def test_negative_Gps(self):
        with pytest.raises(ValueError, match="Gps_scf must be >= 0"):
            three_stage_total_gp(-1.0, 0.0, 0.0, 10.0, oil_api=50.0)
