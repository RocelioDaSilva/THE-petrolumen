import pytest
from app.reservoir.gas_mb_we import gas_mb_we


class TestExample34:
    """Book Ex. 3.4 (pp. 87-88): G=10180 MM SCF, We=960,400 cu ft,
    Sw=0.67, Sgr=0.33. Note: book prints We in cu ft already
    (960,400) after converting 15,200 bbl * 1.03 * 5.615 = 88,000 bbl
    equivalent; book's units in the algebra are cu ft. Tolerance 2%."""
    def _run(self):
        return gas_mb_we(
            Vb_cuft=415.3e6, phi=0.172, Swi=0.25,
            Bgi=0.005262, Bgf=0.005700,
            Gp_scf=935.4e6, Wp_bbl=15200.0, Bw=1.03,
            Vb_invaded_cuft=13.04e6,
        )

    def test_G(self):
        r = self._run()
        assert r.G_scf / 1e9 == pytest.approx(10.18, rel=0.02)

    def test_Sgr(self):
        r = self._run()
        assert r.Sgr_invaded == pytest.approx(0.33, abs=0.03)


class TestValidation:
    def test_Bgf_le_Bgi(self):
        with pytest.raises(ValueError, match="Bgf must exceed"):
            gas_mb_we(1e8, 0.20, 0.25, 0.005, 0.004, 1e7, 0.0, 1.0, 1e7)
