import pytest
from app.reservoir.rate_allocation import (
    RateAllocBlock, multilateral_rate_allocation_error,
)


def _blk(kh_ratio: float) -> RateAllocBlock:
    return RateAllocBlock(
        k_md=100.0, h_ft=10.0 * kh_ratio, S=0.0, mu_cp=1.0,
        B_bbl_stb=1.2, r_e_ft=660.0, r_w_ft=0.333, p_avg_psia=4000.0,
    )


class TestUniformBlocks:
    def test_uniform(self):
        r = multilateral_rate_allocation_error(
            Q_stb_d=1000.0, blocks=[_blk(1.0), _blk(1.0)],
        )
        assert r.dp_kh_error_psi == pytest.approx(0.0, abs=1e-9)
        assert r.classification == "acceptable"


class TestHighContrast:
    def test_contrast(self):
        r = multilateral_rate_allocation_error(
            Q_stb_d=1000.0, blocks=[_blk(1.0), _blk(10.0)],
        )
        assert r.q_alloc_stb_d[0] == pytest.approx(1000.0 / 11.0)
        assert r.q_alloc_stb_d[1] == pytest.approx(10000.0 / 11.0)
        assert len(set(round(p, 1) for p in r.p_w_psia)) == 2
        assert r.classification in ("suspect", "reject")


class TestValidation:
    def test_one_block(self):
        with pytest.raises(ValueError, match="at least 2"):
            multilateral_rate_allocation_error(
                Q_stb_d=1000.0, blocks=[_blk(1.0)],
            )
    def test_negative_Q(self):
        with pytest.raises(ValueError, match="Q_stb_d must be > 0"):
            multilateral_rate_allocation_error(
                Q_stb_d=-1.0, blocks=[_blk(1.0), _blk(2.0)],
            )


class TestDeterminism:
    def test_repeatable(self):
        a = multilateral_rate_allocation_error(
            1000.0, [_blk(1.0), _blk(5.0)],
        )
        b = multilateral_rate_allocation_error(
            1000.0, [_blk(1.0), _blk(5.0)],
        )
        assert a.dp_kh_error_psi == b.dp_kh_error_psi
        assert a.classification == b.classification
