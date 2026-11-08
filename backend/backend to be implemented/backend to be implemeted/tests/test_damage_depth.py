import math
import pytest
from app.reservoir.damage_depth import (
    damage_radius_from_skin, damage_permeability_from_skin,
)

class TestExample73Analogue:
    """S=5.0, k_e/k_a=10, r_w=0.354 -> r_a = 0.354*exp(5/9) ~ 0.617 ft."""
    def test_r_a(self):
        r = damage_radius_from_skin(5.0, 100.0, 10.0, 0.354)
        assert r.r_a_ft == pytest.approx(0.354 * math.exp(5.0 / 9.0),
                                          rel=1e-9)
        assert r.remediation == "ream or reperforate (shallow)"

class TestRoundTrip:
    """Forward F58 then inverse F63 recovers r_a."""
    def test_roundtrip(self):
        from app.reservoir.damage_skin import damage_skin
        r_w = 0.354
        r_a = 1.5
        k_e, k_a = 100.0, 10.0
        S = damage_skin(k_e, k_a, r_a, r_w).S
        r = damage_radius_from_skin(S, k_e, k_a, r_w)
        assert r.r_a_ft == pytest.approx(r_a, rel=1e-9)

class TestPermFromSkin:
    def test_k_a(self):
        r = damage_permeability_from_skin(5.0, 100.0, 1.0, 0.354)
        # ln(1/0.354) ~ 1.038; denom = 1 + 5/1.038 ~ 5.816
        # k_a ~ 100/5.816 ~ 17.2 md
        assert r.k_a_md == pytest.approx(17.19, rel=0.02)

class TestValidation:
    def test_stimulation_raises(self):
        with pytest.raises(ValueError, match="S=.*< 0"):
            damage_radius_from_skin(-2.0, 100.0, 50.0, 0.354)
    def test_ra_le_rw(self):
        with pytest.raises(ValueError, match="r_a_ft"):
            damage_permeability_from_skin(2.0, 100.0, 0.5, 0.354)
