import pytest

from app.engines.pvt.eos_solver import EosSolver


def _solver(eos_type: str = "PR") -> EosSolver:
    solver = EosSolver(eos_type=eos_type)
    solver.add_component(
        "methane",
        {
            "critical_pressure": 4_599_000.0,
            "critical_temperature": 190.56,
            "acentric_factor": 0.011,
        },
    )
    return solver


def test_srk_z_factor_fails_loudly_until_implemented_and_validated():
    solver = _solver(eos_type="SRK")

    with pytest.raises(
        NotImplementedError,
        match="Soave-Redlich-Kwong equation of state is not implemented or validated",
    ):
        solver.calculate_z_factor(5_000_000.0, 250.0, {"methane": 1.0})


def test_flash_calculation_fails_loudly_until_validated():
    solver = _solver()

    with pytest.raises(
        NotImplementedError,
        match="Isothermal flash calculations are not implemented or validated",
    ):
        solver.flash_calculation(5_000_000.0, 250.0, {"methane": 1.0})
