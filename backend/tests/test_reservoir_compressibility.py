import math

import pytest

from app.engines.reservoir.compressibility import (
    formation_compressibility,
    gas_compressibility_from_z_curve,
    total_compressibility,
)


@pytest.mark.parametrize(
    ("phi", "rock_type", "expected"),
    [
        (0.20, "sandstone", 2.74e-6),
        (0.20, "limestone", 4.322e-6),
    ],
)
def test_formation_compressibility_reference_values(phi, rock_type, expected):
    assert formation_compressibility(phi, rock_type) == pytest.approx(
        expected, rel=1e-3
    )


def test_formation_compressibility_strict_validity_range():
    assert formation_compressibility(0.20, "sandstone", strict=True) > 0
    with pytest.raises(ValueError, match="outside book validity"):
        formation_compressibility(0.30, "sandstone", strict=True)
    assert formation_compressibility(0.30, "sandstone", strict=False) > 0


@pytest.mark.parametrize("phi", [0.0, 1.0, -0.1, float("nan"), float("inf")])
def test_formation_compressibility_rejects_invalid_porosity(phi):
    with pytest.raises(ValueError, match="phi must be finite"):
        formation_compressibility(phi, "sandstone")


def test_formation_compressibility_rejects_unknown_rock_type():
    with pytest.raises(ValueError, match="rock_type"):
        formation_compressibility(0.2, "shale")


def test_gas_compressibility_matches_linear_z_curve_derivative():
    result = gas_compressibility_from_z_curve(
        1000.0,
        lambda pressure: 1.1 + 1.0e-4 * pressure,
    )

    assert result.method == "central"
    assert result.z_at_p == pytest.approx(1.2)
    assert result.dz_dp_psi_inv == pytest.approx(1.0e-4, rel=1e-8)
    assert result.cg_psi_inv == pytest.approx(9.1666666667e-4, rel=1e-8)


def test_gas_compressibility_uses_forward_difference_near_zero_pressure():
    result = gas_compressibility_from_z_curve(
        0.25,
        lambda pressure: 1.0 + 1.0e-3 * pressure,
    )

    assert result.method == "forward"
    assert result.dz_dp_psi_inv == pytest.approx(1.0e-3, rel=1e-10)


@pytest.mark.parametrize("pressure", [0.0, -1.0, float("nan"), float("inf")])
def test_gas_compressibility_rejects_invalid_pressure(pressure):
    with pytest.raises(ValueError, match="p_psia"):
        gas_compressibility_from_z_curve(pressure, lambda _: 1.0)


@pytest.mark.parametrize("z", [0.0, -1.0, float("nan"), float("inf")])
def test_gas_compressibility_rejects_nonphysical_z(z):
    with pytest.raises(ValueError, match="positive finite"):
        gas_compressibility_from_z_curve(1000.0, lambda _: z)


def test_total_compressibility_weights_fluid_terms_and_adds_rock_term():
    result = total_compressibility(
        cg_psi_inv=1.0e-3,
        co_psi_inv=1.0e-5,
        cw_psi_inv=3.0e-6,
        cf_psi_inv=2.0e-6,
        sg=0.1,
        so=0.7,
        sw=0.2,
    )

    assert result == pytest.approx(1.096e-4)


def test_total_compressibility_rejects_saturations_not_summing_to_one():
    with pytest.raises(ValueError, match="must sum to 1"):
        total_compressibility(
            cg_psi_inv=1e-3,
            co_psi_inv=1e-5,
            cw_psi_inv=3e-6,
            cf_psi_inv=2e-6,
            sg=0.1,
            so=0.7,
            sw=0.1,
        )


def test_total_compressibility_rejects_non_finite_values():
    with pytest.raises(ValueError, match="finite"):
        total_compressibility(
            cg_psi_inv=math.inf,
            co_psi_inv=1e-5,
            cw_psi_inv=3e-6,
            cf_psi_inv=2e-6,
            sg=0.1,
            so=0.7,
            sw=0.2,
        )
