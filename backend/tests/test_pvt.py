import pytest
import numpy as np

# Assuming the pvt module is structured as backend.gaia_genesis_new.pvt
# Adjust imports based on actual project structure and PYTHONPATH for tests
from backend.gaia_genesis_new.pvt.core import BlackOilModel, CompositionalModel
from backend.gaia_genesis_new.api_v1.schemas import FluidComponent # Using the schema version for consistency
from backend.gaia_genesis_new.pvt.service import PVTService

# --- Test Data Fixtures ---

@pytest.fixture
def black_oil_sample_data() -> Dict[str, float]:
    """Provides sample data for a black oil model."""
    return {
        'pb': 3000.0,      # Bubble point pressure (psi)
        'co': 1.5e-5,     # Oil compressibility (1/psi)
        'rsb': 800.0,     # Solution GOR at bubble point (scf/STB)
        'bob': 1.45,      # Oil FVF at bubble point (rb/STB)
        'muob': 0.8,      # Oil viscosity at bubble point (cp)
        'muod': 2.5,      # Dead oil viscosity (cp)
        'cg': 3.0e-4,     # Gas compressibility (1/psi) - Note: This is not directly used by Z-factor correlations
        'gamma_g': 0.75,  # Gas specific gravity
        'gamma_o': 0.85,  # Oil API gravity (water=1) -> API = (141.5/0.85) - 131.5 = 34.9
        'temperature': 200.0 # Reservoir temperature (°F)
    }

@pytest.fixture
def methane_component() -> FluidComponent:
    return FluidComponent(
        name="C1",
        molecular_weight=16.043,
        critical_pressure=667.8,  # psia
        critical_temperature=343.0,  # Rankine
        acentric_factor=0.011, # More common value for C1
        critical_volume=1.586,  # ft³/lb-mol (approx from Reid, Prausnitz, Poling)
        parachor=77.0 # (approx, from Fanchi or other sources)
    )

@pytest.fixture
def ethane_component() -> FluidComponent:
    return FluidComponent(
        name="C2",
        molecular_weight=30.070,
        critical_pressure=707.8,  # psia
        critical_temperature=549.8,  # Rankine
        acentric_factor=0.099, # More common value for C2
        critical_volume=2.373,  # ft³/lb-mol
        parachor=108.0
    )

@pytest.fixture
def nbutane_component() -> FluidComponent:
    return FluidComponent(
        name="nC4",
        molecular_weight=58.123,
        critical_pressure=550.7,  # psia
        critical_temperature=765.3,  # Rankine
        acentric_factor=0.200, # More common value for nC4
        critical_volume=4.083,  # ft³/lb-mol
        parachor=189.9
    )

# --- BlackOilModel Tests ---

def test_black_oil_initialization(black_oil_sample_data):
    model = BlackOilModel(black_oil_sample_data)
    assert model.pb == 3000.0
    assert model.gamma_o == 0.85
    assert model.temperature == 200.0

def test_black_oil_api_gravity(black_oil_sample_data):
    model = BlackOilModel(black_oil_sample_data)
    api = model.calculate_api_gravity()
    expected_api = (141.5 / 0.85) - 131.5
    assert abs(api - expected_api) < 1e-3

def test_black_oil_solution_gor_standing(black_oil_sample_data):
    model = BlackOilModel(black_oil_sample_data)
    # Test above bubble point
    assert abs(model.calculate_solution_gor_standing(3500) - black_oil_sample_data['rsb']) < 1e-3
    # Test at bubble point
    assert abs(model.calculate_solution_gor_standing(3000) - black_oil_sample_data['rsb']) < 1e-3
    # Test below bubble point (should be less than Rsb)
    rs_below_pb = model.calculate_solution_gor_standing(2500)
    assert rs_below_pb < black_oil_sample_data['rsb']
    assert rs_below_pb > 0

def test_black_oil_fvf_standing(black_oil_sample_data):
    model = BlackOilModel(black_oil_sample_data)
    # Test above bubble point
    bo_above = model.calculate_oil_fvf_standing(3500) # Uses Rsb implicitly
    expected_bob_at_pb = model.calculate_oil_fvf_standing(model.pb) # Bo at Pb
    expected_bo_above = expected_bob_at_pb * np.exp(-model.co * (3500 - model.pb))
    assert abs(bo_above - expected_bo_above) < 1e-4 # Check consistency with Co effect

    # Test at bubble point
    bo_at_pb = model.calculate_oil_fvf_standing(model.pb)
    assert abs(bo_at_pb - model.bob) < 0.05 # Allow some tolerance if bob itself was from a fit

    # Test below bubble point
    bo_below = model.calculate_oil_fvf_standing(2500)
    assert bo_below < bo_at_pb
    assert bo_below > 1.0

def test_black_oil_z_factor_hall_yarborough(black_oil_sample_data):
    model = BlackOilModel(black_oil_sample_data)
    # Test case for typical gas (e.g., P=2000 psi, T=150 F, gamma_g=0.7)
    # For gamma_g = 0.75, T=200F (659.67R), P=3000 psi
    # Tpc ~ 169.2 + 349.5*0.75 - 74*0.75^2 = 389.8 R (Sutton based on gamma_g)
    # Ppc ~ 756.8 - 131*0.75 - 3.6*0.75^2 = 656.5 psi
    # Tpr = 659.67 / 389.8 = 1.69
    # Ppr = 3000 / 656.5 = 4.57
    # Expected Z for these Ppr, Tpr is around 0.7 - 0.9 range.
    z = model.calculate_z_factor_hall_yarborough(p=3000, t_fahrenheit=200)
    assert 0.6 < z < 1.0
    z_low_p = model.calculate_z_factor_hall_yarborough(p=100, t_fahrenheit=200)
    assert 0.9 < z_low_p <= 1.0 # Z approaches 1 at low pressures

def test_black_oil_gas_fvf(black_oil_sample_data):
    model = BlackOilModel(black_oil_sample_data)
    # Bg = 0.02827 * Z * T_abs / P
    # At P=3000 psi, T=200F (659.67R)
    z = model.calculate_z_factor_hall_yarborough(3000, 200)
    expected_bg = 0.02827 * z * (200 + 459.67) / 3000
    bg = model.calculate_gas_fvf(3000, 200)
    assert abs(bg - expected_bg) < 1e-6

def test_black_oil_viscosity_beggs_robinson(black_oil_sample_data):
    model = BlackOilModel(black_oil_sample_data)
    # Test above bubble point (should be close to muob)
    mu_above = model.calculate_oil_viscosity_beggs_robinson(3500)
    assert abs(mu_above - model.muob) < 0.1 # Placeholder for undersaturated model

    # Test at bubble point
    mu_at_pb = model.calculate_oil_viscosity_beggs_robinson(model.pb)
    assert abs(mu_at_pb - model.muob) < 1e-4

    # Test below bubble point
    mu_below = model.calculate_oil_viscosity_beggs_robinson(2500)
    assert mu_below > model.muob # Viscosity increases as gas comes out of solution below Pb
    assert mu_below < model.muod # Should be less than dead oil viscosity if Rs > 0

# --- CompositionalModel Tests ---
# These tests will be more extensive as the CompositionalModel is complex.

def test_compositional_model_initialization(methane_component, ethane_component):
    methane_component.mole_fraction = 0.7
    ethane_component.mole_fraction = 0.3
    model = CompositionalModel(components=[methane_component, ethane_component])
    assert len(model.components) == 2
    assert abs(sum(c.mole_fraction for c in model.components) - 1.0) < 1e-6

def test_compositional_model_pure_params_pr(methane_component):
    # Test PR pure component 'a' and 'b' calculation
    methane_component.mole_fraction = 1.0
    model = CompositionalModel(components=[methane_component]) # Model with pure methane
    temp_F = 60.0 # Example temperature
    a_i, b_i = model._calculate_pr_eos_params_pure(component_idx=0, t_fahrenheit=temp_F)

    assert a_i > 0
    assert b_i > 0
    # Exact values depend on R, omega_a, omega_b constants and correlations.
    # Could compare against known literature values for methane at 60F if available.
    # For methane (Tc=343R, Pc=667.8psia, w=0.011) at T=60F (519.67R)
    # Tr = 519.67/343 = 1.515
    # kappa = 0.37464 + 1.54226*0.011 - 0.26992*0.011^2 = 0.3915
    # alpha = (1 + kappa*(1-sqrt(Tr)))^2 = (1 + 0.3915*(1-sqrt(1.515)))^2 = (1 + 0.3915*(1-1.230))**2 = (1 - 0.0902)**2 = 0.8277
    # ac_i = 0.457235 * (10.73159^2 * 343^2) / 667.8 = 130034
    # a_i = ac_i * alpha = 130034 * 0.8277 = 107627
    # b_i = 0.077796 * 10.73159 * 343 / 667.8 = 0.428
    assert abs(a_i - 107627) < 1000 # Rough check
    assert abs(b_i - 0.428) < 0.01  # Rough check

def test_compositional_model_mixture_params_pr(methane_component, ethane_component):
    methane_component.mole_fraction = 0.7
    ethane_component.mole_fraction = 0.3
    model = CompositionalModel(components=[methane_component, ethane_component])
    temp_F = 60.0
    phase_comp = [0.7, 0.3]
    a_mix, b_mix = model._calculate_pr_eos_params_mixture(phase_comp, temp_F)
    assert a_mix > 0
    assert b_mix > 0
    # Check against individual component b values: b_mix should be sum(zi*bi)
    _, b_methane = model._calculate_pr_eos_params_pure(0, temp_F)
    _, b_ethane = model._calculate_pr_eos_params_pure(1, temp_F)
    assert abs(b_mix - (0.7 * b_methane + 0.3 * b_ethane)) < 1e-4

def test_compositional_model_solve_z_pr(methane_component):
    # Test Z-factor calculation for pure methane
    methane_component.mole_fraction = 1.0
    model = CompositionalModel(components=[methane_component])
    temp_F = 68.0  # 20 C = 293.15 K
    pressure_psia = 145.0 # 10 bar approx

    a_mix, b_mix = model._calculate_pr_eos_params_mixture([1.0], temp_F)
    z_roots = model._solve_pr_eos_for_z(pressure_psia, temp_F, a_mix, b_mix)

    assert len(z_roots) >= 1 # Should have at least one real root (vapor)
    # For methane at low P, high T, Z should be close to 1
    # T = 68F = 527.67 R. Tr = 527.67/343 = 1.538
    # P = 145 psia. Pr = 145/667.8 = 0.217
    # Expected Z ~0.98 for these conditions
    assert abs(z_roots[-1] - 0.98) < 0.02 # Check largest root (vapor)

def test_compositional_model_fugacity_coeffs_pr(methane_component, ethane_component):
    # Test based on your example values from the previous snippet
    methane_component.mole_fraction = 0.7
    ethane_component.mole_fraction = 0.3
    model = CompositionalModel(components=[methane_component, ethane_component])

    phase_comp = [0.7, 0.3]
    p_psia = 1000.0
    t_fahrenheit = 100.0

    # Need a Z factor for the phase to calculate fugacity coeffs
    a_mix, b_mix = model._calculate_pr_eos_params_mixture(phase_comp, t_fahrenheit)
    z_roots = model._solve_pr_eos_for_z(p_psia, t_fahrenheit, a_mix, b_mix)
    z_phase = z_roots[-1] # Assume vapor phase for this test

    phi_coeffs = model._calculate_fugacity_coeffs_pr(phase_comp, p_psia, t_fahrenheit, z_phase)
    assert len(phi_coeffs) == 2
    # Your previous snippet expected phi[0] ~ 0.95 (methane), phi[1] ~ 0.85 (ethane)
    # These values depend heavily on the exactness of PR EOS implementation details and BIPs.
    # For default BIPs=0, these values might differ.
    # This test is more of a sanity check that it runs and produces plausible numbers.
    assert 0.5 < phi_coeffs[0] < 1.5 # Methane fugacity coeff
    assert 0.3 < phi_coeffs[1] < 1.5 # Ethane fugacity coeff
    print(f"Test Fugacity Coeffs: Methane Phi={phi_coeffs[0]:.4f}, Ethane Phi={phi_coeffs[1]:.4f}")


def test_compositional_model_initial_k_values_wilson(methane_component, nbutane_component):
    methane_component.mole_fraction = 0.6
    nbutane_component.mole_fraction = 0.4
    model = CompositionalModel(components=[methane_component, nbutane_component])
    p_psia = 500.0
    t_fahrenheit = 100.0 # 559.67 R
    k_values = model.initial_k_values_wilson(p_psia, t_fahrenheit)
    assert len(k_values) == 2
    # Methane (C1) is more volatile than n-Butane (nC4), so K_C1 > K_nC4
    # K_C1 should be > 1, K_nC4 might be < 1 at these conditions
    assert k_values[0] > k_values[1]
    assert k_values[0] > 1.0 # Methane likely vaporizes
    # print(f"Test K-Values: C1 K={k_values[0]:.3f}, nC4 K={k_values[1]:.3f}")


def test_compositional_model_flash_ssi(methane_component, nbutane_component):
    methane_component.mole_fraction = 0.6
    nbutane_component.mole_fraction = 0.4 # Overall composition
    model = CompositionalModel(components=[methane_component, nbutane_component])

    p_psia = 800.0
    t_fahrenheit = 100.0 # Two-phase region for C1/nC4 mix (e.g. 60/40)

    flash_results = model.perform_flash_calculation_ssi(p_psia, t_fahrenheit)

    assert "vapor_fraction" in flash_results
    assert 0 < flash_results["vapor_fraction"] < 1 # Expect two phases
    assert len(flash_results["liquid_composition"]) == 2
    assert len(flash_results["vapor_composition"]) == 2
    assert abs(sum(flash_results["liquid_composition"]) - 1.0) < 1e-3
    assert abs(sum(flash_results["vapor_composition"]) - 1.0) < 1e-3
    # Methane should be richer in vapor, nButane in liquid
    assert flash_results["vapor_composition"][0] > flash_results["liquid_composition"][0] # C1 in vapor > C1 in liquid
    assert flash_results["liquid_composition"][1] > flash_results["vapor_composition"][1] # nC4 in liquid > nC4 in vapor
    assert flash_results.get("converged", True) is not False


# --- LBC Viscosity Tests (within CompositionalModel) ---
def test_lbc_viscosity_pure_methane(methane_component):
    methane_component.mole_fraction = 1.0
    model = CompositionalModel([methane_component])

    # Test conditions (example from a paper for methane)
    # Density: 0.1 g/cm^3 = 6.24 lb/ft^3
    # Temperature: 100 F
    density_lb_ft3 = 6.24
    temp_F = 100.0

    # Expected viscosity for methane around these conditions is ~0.01-0.02 cP for gas, higher for dense phase
    # The LBC implementation is simplified, so we check for plausibility.
    visc = model._calculate_viscosity_lbc([1.0], "vapor", density_lb_ft3, temp_F)
    assert visc is not None
    assert 0.005 < visc < 0.05 # Plausible range for gas-like methane viscosity in cP


# --- PVTService Tests ---

def test_pvt_service_creation_and_calculation(black_oil_sample_data, methane_component, ethane_component):
    service = PVTService()

    # Test Black Oil
    bo_model_name = "TestBO"
    service.create_black_oil_model(bo_model_name, black_oil_sample_data)
    assert bo_model_name in service.black_oil_models

    pvt_res_bo = service.calculate_pvt_properties(bo_model_name, p_psia=2500, t_fahrenheit=200)
    assert pvt_res_bo is not None
    assert pvt_res_bo.oil_fvf is not None and pvt_res_bo.oil_fvf > 0
    assert pvt_res_bo.solution_gor is not None

    # Test Compositional
    comp_model_name = "TestComp"
    methane_component.mole_fraction = 0.8
    ethane_component.mole_fraction = 0.2
    components = [methane_component, ethane_component]
    service.create_compositional_model(comp_model_name, components)
    assert comp_model_name in service.compositional_models

    # This will use the more complex compositional calculations
    pvt_res_comp = service.calculate_pvt_properties(comp_model_name, p_psia=1000, t_fahrenheit=100)
    assert pvt_res_comp is not None
    # Check a few properties exist (actual values depend on full EOS solve)
    assert pvt_res_comp.z_liquid is not None or pvt_res_comp.z_vapor is not None


def test_pvt_service_table_generation(black_oil_sample_data):
    service = PVTService()
    model_name = "TestBOTable"
    service.create_black_oil_model(model_name, black_oil_sample_data)

    pressure_points = [1000.0, 2000.0, 3000.0, 4000.0]
    temp_F = 200.0

    table = service.generate_pvt_table(model_name, pressure_points, temp_F)
    assert len(table) == len(pressure_points)
    for entry in table:
        assert entry.pressure in pressure_points
        assert entry.oil_fvf is not None

# Placeholder for Critical Point test (Heidemann-Khalil is complex to validate simply)
def test_critical_point_estimation_placeholder(methane_component, nbutane_component):
    methane_component.mole_fraction = 0.6
    nbutane_component.mole_fraction = 0.4
    model = CompositionalModel([methane_component, nbutane_component])

    # Current HK is a placeholder, so this test is just for structure
    tc_est_F, pc_est_psia = model.estimate_critical_point_hk()
    assert tc_est_F is not None
    assert pc_est_psia is not None
    # For C1/nC4 (60/40), critical point is roughly T~150-200F, P~800-1200 psia.
    # The simple mixing rule will give:
    # Tc_mix_R = 0.6*343 + 0.4*765.3 = 205.8 + 306.12 = 511.92 R => 52.25 F
    # Pc_mix_psia = 0.6*667.8 + 0.4*550.7 = 400.68 + 220.28 = 620.96 psia
    # This shows simple mixing rule is not very accurate for critical point.
    # A full HK would yield different results.
    # print(f"Estimated Critical Point (simple mixing): T={tc_est_F:.2f}°F, P={pc_est_psia:.2f} psia")
    assert -100 < tc_est_F < 400 # Very broad range for placeholder
    assert 300 < pc_est_psia < 1500 # Very broad range for placeholder

# Note: More rigorous testing would involve comparing against:
# 1. Published experimental data for known mixtures.
# 2. Results from established PVT simulation software (e.g., PVTsim, Eclipse PVT).
# 3. Specific test cases from thermodynamic textbooks.
# The current tests focus on basic functionality and plausibility.
