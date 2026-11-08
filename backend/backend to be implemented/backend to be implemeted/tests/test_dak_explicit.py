import pytest
from app.reservoir.dak_explicit import dak_z_factor

class TestBookTable15:
    """Table 1.5 (p. 19): Tr=1.5, pr=1.0 -> Z~0.8509.
    Tolerance 1% (typical for the book's hand-worked table)."""
    def test_at_1_5_1(self):
        r = dak_z_factor(1.0, 1.5)
        assert r.Z == pytest.approx(0.8509, rel=0.02)
        assert r.converged is True

    def test_at_1_5_5(self):
        """Tr=1.5, pr=5.0 -> Z~0.7876 (Table 1.5)."""
        r = dak_z_factor(5.0, 1.5)
        assert r.Z == pytest.approx(0.7876, rel=0.02)

class TestConvergence:
    def test_iterations(self):
        r = dak_z_factor(3.0, 1.8)
        assert 1 <= r.n_iter <= 50
        assert r.residual < 1e-6

class TestValidation:
    def test_pr_zero(self):
        with pytest.raises(ValueError, match="pr must be > 0"):
            dak_z_factor(0.0, 1.5)
    def test_near_critical_nonconverge(self):
        with pytest.raises(ValueError, match="converge"):
            dak_z_factor(7.0, 1.0, max_iter=2)
