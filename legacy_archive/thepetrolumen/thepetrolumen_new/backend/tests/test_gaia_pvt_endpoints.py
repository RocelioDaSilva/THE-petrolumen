# import pytest # Unused
from fastapi.testclient import TestClient
from fastapi import status

# Assuming UserResponse is defined in main or a shared model location accessible for import
# For testing, we might need to adjust imports if main.UserResponse is not directly importable
# For now, let's assume it can be imported or we mock/redefine a simple one for type hinting if needed.
# from backend.main import UserResponse # If UserResponse is needed for type hints and is importable

# Fixtures used: client, user_auth_headers (from conftest.py)

# --- Test PVT Calculation Endpoints ---


# Helper function to make requests, can be expanded
def post_pvt_calculation(
    client: TestClient, endpoint_suffix: str, data: dict, headers: dict
):
    return client.post(f"/api/v1/gaia/pvt{endpoint_suffix}", json=data, headers=headers)


# 1. Z-Factor Tests
def test_calculate_z_factor_success(client: TestClient, user_auth_headers: dict):
    request_data = {"pressure": 2000, "temperature": 150, "gas_specific_gravity": 0.7}
    response = post_pvt_calculation(
        client, "/calculate_z_factor", request_data, user_auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert "z_factor" in json_response
    assert isinstance(json_response["z_factor"], float)
    # Add a check for a plausible z_factor range if known for these inputs
    assert 0.5 < json_response["z_factor"] < 1.5


def test_calculate_z_factor_missing_field(client: TestClient, user_auth_headers: dict):
    request_data = {
        "pressure": 2000,
        "temperature": 150,
    }  # Missing gas_specific_gravity
    response = post_pvt_calculation(
        client, "/calculate_z_factor", request_data, user_auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_calculate_z_factor_unauthenticated(client: TestClient):
    request_data = {"pressure": 2000, "temperature": 150, "gas_specific_gravity": 0.7}
    response = post_pvt_calculation(
        client, "/calculate_z_factor", request_data, {}
    )  # No auth headers
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# 2. Formation Volume Factor (FVF) Tests
def test_calculate_fvf_oil_success(client: TestClient, user_auth_headers: dict):
    request_data = {
        "pressure": 3000,
        "temperature": 180,
        "fluid_type": "oil",
        "api_gravity": 35,
        "gas_specific_gravity": 0.75,
    }
    response = post_pvt_calculation(
        client, "/calculate_formation_volume_factor", request_data, user_auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert "fvf" in json_response
    assert isinstance(json_response["fvf"], float)
    assert 1.0 < json_response["fvf"] < 2.5  # Plausible Bo range


def test_calculate_fvf_gas_success(client: TestClient, user_auth_headers: dict):
    request_data = {
        "pressure": 2000,
        "temperature": 150,
        "fluid_type": "gas",
        "gas_specific_gravity": 0.65,
    }
    response = post_pvt_calculation(
        client, "/calculate_formation_volume_factor", request_data, user_auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert "fvf" in json_response
    assert isinstance(json_response["fvf"], float)
    assert (
        0.001 < json_response["fvf"] < 0.05
    )  # Plausible Bg range (e.g., ft3/scf or res bbl/scf)


def test_calculate_fvf_oil_missing_api(client: TestClient, user_auth_headers: dict):
    request_data = {  # Missing api_gravity for oil
        "pressure": 3000,
        "temperature": 180,
        "fluid_type": "oil",
        "gas_specific_gravity": 0.75,
    }
    response = post_pvt_calculation(
        client, "/calculate_formation_volume_factor", request_data, user_auth_headers
    )
    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    )  # Custom validation in endpoint
    assert "api_gravity is required for fluid_type 'oil'" in response.json()["detail"]


def test_calculate_fvf_invalid_fluid_type(client: TestClient, user_auth_headers: dict):
    request_data = {
        "pressure": 3000,
        "temperature": 180,
        "fluid_type": "steam",  # Invalid
        "gas_specific_gravity": 0.75,
    }
    response = post_pvt_calculation(
        client, "/calculate_formation_volume_factor", request_data, user_auth_headers
    )
    assert (
        response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    )  # Pydantic validation for enum


# 3. Viscosity Tests
def test_calculate_viscosity_oil_success(client: TestClient, user_auth_headers: dict):
    request_data = {
        "pressure": 2500,
        "temperature": 160,
        "fluid_type": "oil",
        "api_gravity": 40,
        "gas_specific_gravity": 0.7,
    }
    response = post_pvt_calculation(
        client, "/calculate_viscosity", request_data, user_auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert "viscosity" in json_response
    assert isinstance(json_response["viscosity"], float)
    assert 0.1 < json_response["viscosity"] < 100  # Plausible oil viscosity range in cP


def test_calculate_viscosity_gas_success(client: TestClient, user_auth_headers: dict):
    request_data = {
        "pressure": 1500,
        "temperature": 120,
        "fluid_type": "gas",
        "gas_specific_gravity": 0.6,
    }
    response = post_pvt_calculation(
        client, "/calculate_viscosity", request_data, user_auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert "viscosity" in json_response
    assert isinstance(json_response["viscosity"], float)
    assert (
        0.005 < json_response["viscosity"] < 0.05
    )  # Plausible gas viscosity range in cP


# 4. Solution Gas-Oil Ratio (Rs) Tests
def test_calculate_solution_gas_ratio_success(
    client: TestClient, user_auth_headers: dict
):
    request_data = {
        "pressure": 2000,
        "temperature": 175,
        "api_gravity": 30,
        "gas_specific_gravity": 0.8,
    }
    response = post_pvt_calculation(
        client, "/calculate_solution_gas_ratio", request_data, user_auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert "rs" in json_response
    assert isinstance(json_response["rs"], float)
    assert 100 < json_response["rs"] < 2000  # Plausible Rs range in scf/STB


def test_calculate_solution_gas_ratio_missing_field(
    client: TestClient, user_auth_headers: dict
):
    request_data = {  # Missing api_gravity
        "pressure": 2000,
        "temperature": 175,
        "gas_specific_gravity": 0.8,
    }
    response = post_pvt_calculation(
        client, "/calculate_solution_gas_ratio", request_data, user_auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# --- Tests for Invalid Numerical Inputs (expecting 500 due to generic exception handling) ---
@pytest.mark.parametrize(
    "invalid_data, error_detail_substring",
    [
        ({"pressure": -100, "temperature": 150, "gas_specific_gravity": 0.7}, "Error calculating Z-Factor"),
        ({"pressure": 2000, "temperature": -500, "gas_specific_gravity": 0.7}, "Error calculating Z-Factor"), # Below abs zero
        ({"pressure": 2000, "temperature": 150, "gas_specific_gravity": -0.1}, "Error calculating Z-Factor"),
    ]
)
def test_calculate_z_factor_invalid_numerical_input(
    client: TestClient, user_auth_headers: dict, invalid_data: dict, error_detail_substring: str
):
    response = post_pvt_calculation(
        client, "/calculate_z_factor", invalid_data, user_auth_headers
    )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert error_detail_substring in response.json()["detail"]


@pytest.mark.parametrize(
    "invalid_data, error_detail_substring",
    [
        ({"pressure": -100, "temperature": 180, "fluid_type": "oil", "api_gravity": 35, "gas_specific_gravity": 0.75}, "Error calculating FVF"),
        ({"pressure": 3000, "temperature": 180, "fluid_type": "oil", "api_gravity": -20, "gas_specific_gravity": 0.75}, "Error calculating FVF"),
        ({"pressure": 2000, "temperature": 150, "fluid_type": "gas", "gas_specific_gravity": -0.1}, "Error calculating FVF"),
    ]
)
def test_calculate_fvf_invalid_numerical_input(
    client: TestClient, user_auth_headers: dict, invalid_data: dict, error_detail_substring: str
):
    response = post_pvt_calculation(
        client, "/calculate_formation_volume_factor", invalid_data, user_auth_headers
    )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert error_detail_substring in response.json()["detail"]


@pytest.mark.parametrize(
    "invalid_data, error_detail_substring",
    [
        ({"pressure": -100, "temperature": 160, "fluid_type": "oil", "api_gravity": 40, "gas_specific_gravity": 0.7}, "Error calculating viscosity"),
        ({"pressure": 2500, "temperature": -600, "fluid_type": "oil", "api_gravity": 40, "gas_specific_gravity": 0.7}, "Error calculating viscosity"),
        ({"pressure": 1500, "temperature": 120, "fluid_type": "gas", "gas_specific_gravity": -0.2}, "Error calculating viscosity"),
    ]
)
def test_calculate_viscosity_invalid_numerical_input(
    client: TestClient, user_auth_headers: dict, invalid_data: dict, error_detail_substring: str
):
    response = post_pvt_calculation(
        client, "/calculate_viscosity", invalid_data, user_auth_headers
    )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert error_detail_substring in response.json()["detail"]


@pytest.mark.parametrize(
    "invalid_data, error_detail_substring",
    [
        ({"pressure": -100, "temperature": 175, "api_gravity": 30, "gas_specific_gravity": 0.8}, "Error calculating Solution Gas-Oil Ratio"),
        ({"pressure": 2000, "temperature": 175, "api_gravity": -30, "gas_specific_gravity": 0.8}, "Error calculating Solution Gas-Oil Ratio"),
        ({"pressure": 2000, "temperature": 175, "api_gravity": 30, "gas_specific_gravity": -0.8}, "Error calculating Solution Gas-Oil Ratio"),
    ]
)
def test_calculate_solution_gas_ratio_invalid_numerical_input(
    client: TestClient, user_auth_headers: dict, invalid_data: dict, error_detail_substring: str
):
    response = post_pvt_calculation(
        client, "/calculate_solution_gas_ratio", invalid_data, user_auth_headers
    )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert error_detail_substring in response.json()["detail"]


# --- Unauthenticated Access Tests for other PVT endpoints ---
def test_calculate_fvf_unauthenticated(client: TestClient):
    request_data = {"pressure": 3000, "temperature": 180, "fluid_type": "oil", "api_gravity": 35, "gas_specific_gravity": 0.75}
    response = post_pvt_calculation(client, "/calculate_formation_volume_factor", request_data, {})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_calculate_viscosity_unauthenticated(client: TestClient):
    request_data = {"pressure": 2500, "temperature": 160, "fluid_type": "oil", "api_gravity": 40, "gas_specific_gravity": 0.7}
    response = post_pvt_calculation(client, "/calculate_viscosity", request_data, {})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_calculate_solution_gas_ratio_unauthenticated(client: TestClient):
    request_data = {"pressure": 2000, "temperature": 175, "api_gravity": 30, "gas_specific_gravity": 0.8}
    response = post_pvt_calculation(client, "/calculate_solution_gas_ratio", request_data, {})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# General structure for more tests:
# - Test edge cases for numerical inputs if internal correlations are sensitive (partially added above)
# - Test different combinations of optional parameters.
# - If PVTProperties raised specific exceptions that endpoints should map to HTTP errors, test those.
#   (Currently, endpoints have a generic `except Exception as e`, leading to 500 for ValueErrors from PVTProperties)
#   A future improvement would be for endpoints to catch ValueError from PVTProperties and return 400/422.
