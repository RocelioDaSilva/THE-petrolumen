# import pytest # Unused
from fastapi.testclient import TestClient
from fastapi import status

# This module tests authenticated endpoints in main.py.
# It uses fixtures from conftest.py:
# - `client`: The TestClient for making requests.
# - `test_user`, `test_admin_user`: To get user details.
# - `user_auth_headers`, `admin_auth_headers`: For authenticated requests.
# - `test_user_password`, `test_admin_password`: For login attempts.
# - `clear_users_table`: Ensures clean state for user creation/login tests.


# --- Test Authentication Flow (/api/v1/auth/token) ---
def test_login_for_access_token_success(
    client: TestClient, test_user, test_user_password, clear_users_table
):
    """Test successful login and token retrieval."""
    # test_user fixture (which uses test_auth_manager) creates the user in the test DB.
    login_data = {"username": test_user["username"], "password": test_user_password}
    response = client.post("/api/v1/auth/token", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_login_for_access_token_wrong_password(
    client: TestClient, test_user, clear_users_table
):
    """Test login with wrong password."""
    login_data = {
        "username": test_user["username"],
        "password": "thisIsTheWrongPassword",
    }
    response = client.post("/api/v1/auth/token", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Incorrect username or password"


def test_login_for_access_token_non_existent_user(
    client: TestClient, clear_users_table
):
    """Test login for a user that does not exist."""
    login_data = {"username": "nosuchuser@example.com", "password": "anypassword"}
    response = client.post("/api/v1/auth/token", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_for_access_token_inactive_user(
    client: TestClient, test_auth_manager, test_user_password, clear_users_table
):
    """Test login for an inactive user."""
    inactive_username = "inactive_login@example.com"
    # Create an inactive user directly using auth_manager for this specific test case
    test_auth_manager.create_user(
        username=inactive_username,
        email=inactive_username,
        password=test_user_password,
        is_active=False,
    )
    login_data = {"username": inactive_username, "password": test_user_password}
    response = client.post("/api/v1/auth/token", data=login_data)
    # The authenticate_user method in AuthManager should return None for inactive users,
    # leading to a 401 from the /token endpoint.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert (
        response.json()["detail"] == "Incorrect username or password"
    )  # Or a more specific "User is inactive" if authenticate_user provides that distinction to the endpoint


# --- Test /api/v1/users/me ---
def test_read_users_me_success(client: TestClient, user_auth_headers, test_user):
    """Test successfully fetching current user's details."""
    response = client.get("/api/v1/users/me", headers=user_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    user_me_data = response.json()
    assert user_me_data["username"] == test_user["username"]
    assert user_me_data["email"] == test_user["email"]
    assert user_me_data["role"] == test_user["role"]
    assert user_me_data["is_active"] == test_user["is_active"]
    assert "password" not in user_me_data
    assert "hashed_password" not in user_me_data


def test_read_users_me_unauthenticated(client: TestClient):
    """Test fetching /users/me without authentication."""
    response = client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"


def test_read_users_me_inactive_user_with_valid_token(
    client: TestClient, test_auth_manager, test_user_password
):  # SENSITIVE_VALUE_DO_NOT_LOG (test_user_password)
    """
    Test /users/me with a valid token for a user who has since been made inactive.
    get_current_active_user dependency should catch this.
    """
    username = "now_inactive@example.com"
    user = test_auth_manager.create_user(
        username, username, test_user_password, is_active=True
    )
    assert user is not None

    # Get a token while user is active
    token_response = client.post(
        "/api/v1/auth/token",
        data={"username": username, "password": test_user_password},
    )
    assert token_response.status_code == status.HTTP_200_OK
    active_token = token_response.json()["access_token"]

    # Make user inactive in DB
    test_auth_manager.update_user_details(username, {"is_active": False})

    # Attempt to use the token
    response = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {active_token}"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    # Based on current AuthManager.get_current_user_from_token and main.get_current_active_user,
    # an inactive user found via token should raise HTTP 400 "Inactive user" from get_current_user_from_token,
    # which get_current_active_user re-raises or FastAPI handles.
    # Let's check the actual exception raised by auth_manager.get_current_user_from_token: it's HTTP_400_BAD_REQUEST "Inactive user".
    # The dependency get_current_active_user uses UserResponse(**user), if user.get("disabled") (now user.is_active is False), it should be caught.
    # The current get_current_user_from_token in AuthManager raises:
    # HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    # So, the endpoint should return 400.
    # However, the dependency `get_current_active_user` calls `auth_manager.get_current_user_from_token`.
    # If that token is for an inactive user, `get_current_user_from_token` raises HTTP 400.
    # Let's verify this behavior.
    # The `get_current_active_user` itself doesn't have a separate "disabled" check anymore,
    # as `auth_manager.get_current_user_from_token` handles the `is_active` check.
    assert (
        response.json()["detail"] == "Inactive user"
    )  # This comes from AuthManager through the dependency


# This module covers endpoints that require valid authentication but are not admin-specific.
# - /api/v1/auth/token: Tested for success, wrong password, non-existent user, inactive user.
# - /api/v1/users/me: Tested for success, unauthenticated access, and access with a token for a subsequently inactivated user.
# The `clear_users_table` fixture is used for login tests to ensure a clean state.
# For `/users/me` tests, `user_auth_headers` provides a token from a known active user.
# Test for inactive user login for /token endpoint was refined.
# Test for /users/me with a token for a user who became inactive was added and verified against AuthManager logic.
# Sensitive values (passwords, tokens) are marked.
# Ensure `test_user_password` is consistently used.
# The inactive user test for `/api/v1/auth/token` should yield 401 because `authenticate_user` returns `None` for inactive users.
# The inactive user test for `/api/v1/users/me` (using a token obtained when active) should yield 400 because `get_current_user_from_token` detects inactivity. This is correct.
# Final check on status codes and details for consistency with `AuthManager` and `main.py` logic.
# The detail "Inactive user" for the /users/me inactive test is correct as per AuthManager's get_current_user_from_token.
# The detail "Incorrect username or password" for /token login with inactive user is also correct as authenticate_user returns None.
# Added `clear_users_table` to relevant tests to ensure isolation.
# Corrected assertion for inactive user login at /token endpoint (should be 401).
# Verified the detail message for inactive user at /users/me (should be "Inactive user" with status 400, which is what AuthManager raises).
# If `get_current_active_user` in `main.py` had an additional check on `is_active` after `UserResponse(**user)`,
# it might also raise, but `auth_manager.get_current_user_from_token` already does.
# The current `get_current_active_user` returns `UserResponse(**user)`. If `user` comes from `auth_manager.get_current_user_from_token`
# and that method already raised an exception for an inactive user, then `get_current_active_user` won't even get to the `UserResponse` part.
# So the exception from `auth_manager.get_current_user_from_token` is what the client sees.
# This seems correct and consistent.
# Test `test_read_users_me_inactive_user_with_valid_token` confirmed to expect HTTP 400 "Inactive user".
# Corrected the status code in `test_read_users_me_inactive_user_with_valid_token` to 400, as that's what `get_current_user_from_token` raises.
# This was a subtle point: the dependency injector calls `get_current_user_from_token`, which raises, so the endpoint sees that exception.
# If `get_current_user_from_token` returned the user dict and then `get_current_active_user` did another check, the status might differ.
# But current `AuthManager` is designed to raise directly.
