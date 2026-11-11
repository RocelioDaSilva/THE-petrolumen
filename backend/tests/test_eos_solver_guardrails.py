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


def test_srk_z_factor_solves_cubic_equation():
    solver = _solver(eos_type="SRK")

    z_factor = solver.calculate_z_factor(5_000_000.0, 250.0, {"methane": 1.0})

    tc = 190.56
    pc = 4_599_000.0
    omega = 0.011
    gas_constant = 8.3145
    m = 0.480 + 1.574 * omega - 0.176 * omega**2
    alpha = (1 + m * (1 - (250.0 / tc) ** 0.5)) ** 2
    a = 0.42747 * gas_constant**2 * tc**2 / pc * alpha
    b = 0.08664 * gas_constant * tc / pc
    A = a * 5_000_000.0 / (gas_constant * 250.0) ** 2
    B = b * 5_000_000.0 / (gas_constant * 250.0)
    residual = z_factor**3 - z_factor**2 + (A - B - B**2) * z_factor - A * B

    assert z_factor > 0
    assert residual == pytest.approx(0.0, abs=1e-10)


def test_flash_calculation_solves_two_phase_mass_balance():
    solver = _solver()
    solver.add_component(
        "propane",
        {
            "critical_pressure": 4_248_000.0,
            "critical_temperature": 369.83,
            "acentric_factor": 0.152,
        },
    )

    result = solver.flash_calculation(
        5_000_000.0,
        250.0,
        {"methane": 0.5, "propane": 0.5},
        initial_K=[2.0, 0.5],
    )

    assert result["phase"] == "two_phase"
    assert result["vapor_fraction"] == pytest.approx(0.5)
    liquid = result["liquid_composition"]
    vapor = result["vapor_composition"]
    assert liquid == pytest.approx({"methane": 1 / 3, "propane": 2 / 3})
    assert vapor == pytest.approx({"methane": 2 / 3, "propane": 1 / 3})
    for component, overall in {"methane": 0.5, "propane": 0.5}.items():
        recovered = (
            (1 - result["vapor_fraction"]) * liquid[component]
            + result["vapor_fraction"] * vapor[component]
        )
        assert recovered == pytest.approx(overall)


def test_flash_calculation_detects_single_phase_states():
    solver = _solver()

    liquid_result = solver.flash_calculation(
        5_000_000.0, 250.0, {"methane": 1.0}, initial_K=[0.5]
    )
    vapor_result = solver.flash_calculation(
        5_000_000.0, 250.0, {"methane": 1.0}, initial_K=[2.0]
    )

    assert liquid_result["phase"] == "liquid"
    assert liquid_result["vapor_fraction"] == 0
    assert liquid_result["vapor_composition"] is None
    assert vapor_result["phase"] == "vapor"
    assert vapor_result["vapor_fraction"] == 1
    assert vapor_result["liquid_composition"] is None


def test_flash_calculation_rejects_invalid_k_values():
    solver = _solver()
    with pytest.raises(ValueError, match="K-values must be finite, positive"):
        solver.flash_calculation(
            5_000_000.0, 250.0, {"methane": 1.0}, initial_K=[0.0]
        )
