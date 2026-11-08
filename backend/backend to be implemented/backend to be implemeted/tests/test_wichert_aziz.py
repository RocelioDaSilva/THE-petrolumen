import pytest
from app.reservoir.wichert_aziz import wichert_aziz_correction


class TestNoContaminants:
    def test_identity(self):
        r = wichert_aziz_correction(0.0, 0.0, 400.0, 700.0)
        assert r.Tpc_adj_R == 400.0
        assert r.ppc_adj_psia == 700.0
        assert r.epsilon_R == 0.0


class TestTypicalSourGas:
    """Standard check: 5% H2S, 5% CO2, Tpc=400, ppc=700."""
    def test_epsilon(self):
        r = wichert_aziz_correction(0.05, 0.05, 400.0, 700.0)
        # A=0.10, B=0.05 -> eps = 120*(0.10^0.9-0.10^1.6)+15*(0.05^0.5-0.05^4)
        # 0.10^0.9 = 0.126; 0.10^1.6 = 0.025 -> 0.101*120 = 12.1
        # 0.05^0.5 = 0.224; 0.05^4 = 6.25e-6 -> 0.2235*15 = 3.35
        # eps ~ 15.5 R
        assert r.epsilon_R == pytest.approx(15.5, rel=0.10)

    def test_Tpc_shifted_down(self):
        r = wichert_aziz_correction(0.05, 0.05, 400.0, 700.0)
        assert r.Tpc_adj_R < 400.0


class TestValidation:
    def test_h2s_plus_co2(self):
        with pytest.raises(ValueError, match="y_H2S \\+ y_CO2"):
            wichert_aziz_correction(0.6, 0.5, 400.0, 700.0)
    def test_Tpc_zero(self):
        with pytest.raises(ValueError, match="Tpc_R must be > 0"):
            wichert_aziz_correction(0.05, 0.05, 0.0, 700.0)
