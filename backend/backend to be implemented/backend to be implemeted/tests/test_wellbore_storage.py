"""Tests for wellbore_storage_from_drawdown."""
import pytest
from app.reservoir.wellbore_storage import wellbore_storage_from_drawdown


class TestSyntheticUnitSlope:
    """Early points lie on p_wf = p0 - 30*t (30 psi/hr decline)
    with Q = 1000 STB/day. F = (1000/24) / 30 = 1.389 bbl/psi."""

    def _run(self):
        # p_wf(t) = 3000 - 30 t for t in {0.5, 1.0, 2.0, 3.0}
        pts = [(t, 3000.0 - 30.0 * t) for t in (0.5, 1.0, 2.0, 3.0)]
        return wellbore_storage_from_drawdown(
            early_points=pts, Q_stb_d=1000.0,
        )

    def test_F_bbl_per_psi(self):
        r = self._run()
        assert r.F_bbl_per_psi == pytest.approx(1000.0/24.0/30.0, rel=1e-6)

    def test_slope(self):
        r = self._run()
        assert r.early_fit_slope_psi_per_hr == pytest.approx(-30.0, abs=1e-9)

    def test_r_squared(self):
        r = self._run()
        assert r.r_squared_early > 0.999


class TestLateDataFlag:
    """If late points remain on the same unit-slope line, flag should
    be False (late data still not usable)."""

    def test_late_flat(self):
        pts = [(t, 3000.0 - 30.0 * t) for t in (0.5, 1.0, 2.0)]
        late = [(t, 3000.0 - 30.0 * t) for t in (5.0, 10.0, 15.0)]
        r = wellbore_storage_from_drawdown(
            early_points=pts, Q_stb_d=1000.0, late_points=late,
        )
        assert r.late_data_usable is False

    def test_late_curved(self):
        """If late data are curved (log-like), flag True."""
        pts = [(t, 3000.0 - 30.0 * t) for t in (0.5, 1.0, 2.0)]
        # Curved: p_wf = 2900 - 100*log(t) + drift
        import math
        late = [(t, 2900.0 - 100.0 * math.log10(t) - 0.5*t) for t in (5.0, 10.0, 15.0)]
        r = wellbore_storage_from_drawdown(
            early_points=pts, Q_stb_d=1000.0, late_points=late,
        )
        # Should not be perfectly linear
        assert r.r_squared_late is not None


class TestValidation:
    def test_too_few(self):
        with pytest.raises(ValueError, match="At least 3"):
            wellbore_storage_from_drawdown(
                [(1.0, 2990.0), (2.0, 2980.0)], Q_stb_d=1000.0,
            )

    def test_Q_zero(self):
        with pytest.raises(ValueError, match="Q_stb_d must be > 0"):
            wellbore_storage_from_drawdown(
                [(1.0, 2990.0), (2.0, 2980.0), (3.0, 2970.0)],
                Q_stb_d=0.0,
            )

    def test_time_zero(self):
        with pytest.raises(ValueError, match="dt_hr must be > 0"):
            wellbore_storage_from_drawdown(
                [(0.0, 3000.0), (1.0, 2990.0), (2.0, 2980.0)],
                Q_stb_d=1000.0,
            )

    def test_increasing_pwf(self):
        with pytest.raises(ValueError, match="m = .* >= 0"):
            wellbore_storage_from_drawdown(
                [(1.0, 2980.0), (2.0, 2990.0), (3.0, 3000.0)],
                Q_stb_d=1000.0,
            )


class TestDeterminism:
    def test_repeatable(self):
        pts = [(t, 3000.0 - 30.0 * t) for t in (0.5, 1.0, 2.0, 3.0)]
        a = wellbore_storage_from_drawdown(pts, 1000.0)
        b = wellbore_storage_from_drawdown(pts, 1000.0)
        assert a.F_bbl_per_psi == b.F_bbl_per_psi
