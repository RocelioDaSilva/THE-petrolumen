import pytest
from app.reservoir.hurst_influx import hurst_cumulative_influx


class TestBasic:
    def test_positive(self):
        r = hurst_cumulative_influx(
            100.0, 0.01, 3000.0,
            [(0.0, 3000.0), (100.0, 2900.0), (200.0, 2850.0)],
        )
        assert r.we_cumulative_bbl > 0.0
        assert len(r.we_at_points_bbl) == 3


class TestValidation:
    def test_at_le_one(self):
        # at = 0.01 * 100 = 1 -> raise
        with pytest.raises(ValueError, match="a\\*t"):
            hurst_cumulative_influx(
                100.0, 0.01, 3000.0,
                [(0.0, 3000.0), (100.0, 2900.0)],
            )
    def test_non_increasing(self):
        with pytest.raises(ValueError, match="strictly increase"):
            hurst_cumulative_influx(
                100.0, 1.0, 3000.0,
                [(100.0, 3000.0), (100.0, 2900.0)],
            )
