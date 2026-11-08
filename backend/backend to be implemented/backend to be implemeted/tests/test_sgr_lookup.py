import pytest
from app.reservoir.sgr_lookup import lookup_sgr, list_rocks


class TestDirectHit:
    def test_unconsolidated(self):
        r = lookup_sgr("unconsolidated sand")
        assert r.Sgr_pct == pytest.approx(16.0, abs=0.1)
        assert r.used_table_average is False

    def test_canyon_reef(self):
        r = lookup_sgr("Canyon Reef")
        assert r.Sgr_pct == pytest.approx(50.0, abs=0.1)

    def test_range_midpoint(self):
        r = lookup_sgr("nellie bly")
        # 30-36 -> midpoint 33
        assert r.Sgr_pct == pytest.approx(33.0, abs=0.1)


class TestFallback:
    def test_unknown(self):
        r = lookup_sgr("some new rock")
        assert r.used_table_average is True
        assert r.Sgr_pct == pytest.approx(30.0, abs=0.1)


class TestValidation:
    def test_empty(self):
        with pytest.raises(ValueError, match="rock_name"):
            lookup_sgr("")


class TestList:
    def test_count(self):
        rocks = list_rocks()
        assert len(rocks) == 13
