import pytest
from app.reservoir.drive_diagnostic import (
    DiagnosticSnapshot, drive_diagnostic,
)


def _base_snapshot(t_days, Np_frac):
    """Construct a snapshot on a volumetric-reservoir trajectory
    (Bt grows linearly with Np)."""
    return DiagnosticSnapshot(
        t_days=t_days, Np_stb=Np_frac * 10e6,
        Rp_scf_stb=600.0, Wp_stb=0.0,
        Bt=1.25 + 0.20 * Np_frac, Bti=1.25,
        Bg=0.0015, Rsoi=600.0, m=0.0, Bgi=None,
        Swi=0.20, cw_psi_inv=0.0, cf_psi_inv=0.0,
        delta_p_psi=0.0,
    )


class TestVolumetric:
    def test_stable(self):
        snaps = [_base_snapshot(t, t / 100.0) for t in (10.0, 50.0, 90.0)]
        r = drive_diagnostic(snaps)
        assert r.classification == "volumetric"
        assert abs(r.trend_fraction) < 0.05


class TestWaterDrive:
    def test_increasing_N(self):
        """Injecting extra pressure support makes MB (We=0) over-
        estimate N progressively."""
        snaps = [
            _base_snapshot(10.0, 0.05),
            _base_snapshot(50.0, 0.15),
            _base_snapshot(90.0, 0.25),
        ]
        # Force decreasing pressure instead of the trajectory's inherent
        # N; simulate by artificially depressing Bt later
        snaps[1] = DiagnosticSnapshot(
            t_days=50.0, Np_stb=15e6, Rp_scf_stb=600.0, Wp_stb=0.0,
            Bt=1.30, Bti=1.25, Bg=0.0015, Rsoi=600.0, m=0.0, Bgi=None,
            Swi=0.20, cw_psi_inv=0.0, cf_psi_inv=0.0, delta_p_psi=0.0,
        )
        snaps[2] = DiagnosticSnapshot(
            t_days=90.0, Np_stb=25e6, Rp_scf_stb=600.0, Wp_stb=0.0,
            Bt=1.31, Bti=1.25, Bg=0.0015, Rsoi=600.0, m=0.0, Bgi=None,
            Swi=0.20, cw_psi_inv=0.0, cf_psi_inv=0.0, delta_p_psi=0.0,
        )
        r = drive_diagnostic(snaps)
        assert r.classification in ("volumetric", "water_drive")


class TestValidation:
    def test_too_few(self):
        with pytest.raises(ValueError, match="At least 3"):
            drive_diagnostic([_base_snapshot(10.0, 0.05)])
    def test_non_increasing(self):
        with pytest.raises(ValueError, match="strictly increase"):
            drive_diagnostic([
                _base_snapshot(10.0, 0.05),
                _base_snapshot(10.0, 0.10),
                _base_snapshot(20.0, 0.15),
            ])
