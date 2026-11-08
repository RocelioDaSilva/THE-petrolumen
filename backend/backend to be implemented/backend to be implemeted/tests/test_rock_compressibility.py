"""Tests for backend/app/reservoir/rock_compressibility.py.

Book reference: Craft, Hawkins, Terry (1991), Applied Petroleum Reservoir
Engineering, 2nd ed., Ch. 1, Sec. 4.2, pp. 10-11, Eqs. (1.2) and (1.3).
"""

import math
import pytest

from app.reservoir.rock_compressibility import formation_compressibility


class TestSandstoneGolden:
    """Golden test of Eq. (1.2) at phi = 0.20 (book p. 10)."""

    def test_phi_020(self):
        cf = formation_compressibility(0.20, "sandstone")
        expected = 97.3200e-6 / math.pow(1.0 + 55.8721 * 0.20, 1.42859)
        assert cf == pytest.approx(expected, rel=1e-6)
        # Numeric reference: ~2.740e-6 psi^-1 (cf. book p. 11 range)
        assert cf == pytest.approx(2.740e-6, rel=1e-3)


class TestLimestoneGolden:
    """Golden test of Eq. (1.3) at phi = 0.20 (book p. 11)."""

    def test_phi_020(self):
        cf = formation_compressibility(0.20, "limestone")
        expected = 0.853531 / math.pow(1.0 + 2.47664e6 * 0.20, 0.92990)
        assert cf == pytest.approx(expected, rel=1e-6)
        # Numeric reference: ~4.322e-6 psi^-1
        assert cf == pytest.approx(4.322e-6, rel=1e-3)


class TestRange:
    """Sanity: outputs are positive and decrease with increasing phi."""

    @pytest.mark.parametrize("phi", [0.02, 0.05, 0.10, 0.15, 0.20, 0.23])
    def test_sandstone_positive(self, phi):
        assert formation_compressibility(phi, "sandstone") > 0.0

    @pytest.mark.parametrize("phi", [0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.33])
    def test_limestone_positive(self, phi):
        assert formation_compressibility(phi, "limestone") > 0.0

    def test_sandstone_monotonic_decreasing(self):
        values = [formation_compressibility(p, "sandstone")
                  for p in (0.03, 0.10, 0.20)]
        assert values[0] > values[1] > values[2]

    def test_limestone_monotonic_decreasing(self):
        values = [formation_compressibility(p, "limestone")
                  for p in (0.03, 0.10, 0.20)]
        assert values[0] > values[1] > values[2]


class TestValidation:
    def test_phi_zero(self):
        with pytest.raises(ValueError, match="phi must be in"):
            formation_compressibility(0.0, "sandstone")

    def test_phi_one(self):
        with pytest.raises(ValueError, match="phi must be in"):
            formation_compressibility(1.0, "sandstone")

    def test_phi_negative(self):
        with pytest.raises(ValueError, match="phi must be in"):
            formation_compressibility(-0.1, "sandstone")

    def test_phi_nan(self):
        with pytest.raises(ValueError, match="phi must be in"):
            formation_compressibility(float("nan"), "sandstone")

    def test_phi_inf(self):
        with pytest.raises(ValueError, match="phi must be in"):
            formation_compressibility(float("inf"), "sandstone")

    def test_rock_type_invalid(self):
        with pytest.raises(ValueError, match="rock_type must be"):
            formation_compressibility(0.20, "gneiss")  # type: ignore[arg-type]

    def test_strict_sandstone_out_of_range(self):
        with pytest.raises(ValueError, match="outside book validity"):
            formation_compressibility(0.25, "sandstone", strict=True)

    def test_strict_limestone_out_of_range(self):
        with pytest.raises(ValueError, match="outside book validity"):
            formation_compressibility(0.35, "limestone", strict=True)

    def test_strict_sandstone_in_range_ok(self):
        cf = formation_compressibility(0.15, "sandstone", strict=True)
        assert cf > 0.0

    def test_strict_limestone_in_range_ok(self):
        cf = formation_compressibility(0.30, "limestone", strict=True)
        assert cf > 0.0


class TestDeterminism:
    def test_repeatable_sandstone(self):
        a = formation_compressibility(0.20, "sandstone")
        b = formation_compressibility(0.20, "sandstone")
        assert a == b

    def test_repeatable_limestone(self):
        a = formation_compressibility(0.20, "limestone")
        b = formation_compressibility(0.20, "limestone")
        assert a == b
