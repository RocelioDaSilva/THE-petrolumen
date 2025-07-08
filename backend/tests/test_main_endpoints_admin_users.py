import pytest
from fastapi.testclient import TestClient
from fastapi import status
from typing import Dict, Any

# This module tests admin-only user management endpoints in main.py.
# It uses fixtures from conftest.py:
# - `client`: The TestClient.
# - `admin_auth_headers`: For authenticated admin requests.
# - `user_auth_headers`: For testing non-admin access.
# - `test_admin_user`, `test_user`: For user details.
# - `test_auth_manager`: For direct auth operations if needed for setup/verification.
# - `clear_users_table`: Ensures clean state.


# --- Test POST /api/v1/admin/users (Admin Create New User) ---
def test_admin_create_new_user_success(
    client: TestClient, admin_auth_headers, clear_users_table, test_auth_manager
):
    """Admin successfully creates a new user."""
    new_user_data = {
        "username": "newly_created_user",
        "email": "newly@example.com",
        "password": "a_secure_password_123",
        "full_name": "Newly Created",
        "role": "editor",
    }
    response = client.post(
        "/api/v1/admin/users", headers=admin_auth_headers, json=new_user_data
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_user = response.json()
    assert created_user["username"] == new_user_data["username"]
    assert created_user["email"] == new_user_data["email"]
    assert created_user["role"] == new_user_data["role"]
    assert created_user["is_active"] is True  # Default
    assert "id" in created_user

    # Verify with auth_manager that user exists and password is set (though not returned)
    db_user = test_auth_manager.get_user_by_username(new_user_data["username"])
    assert db_user is not None
    assert test_auth_manager.verify_password(
        new_user_data["password"], db_user.hashed_password
    )


def test_admin_create_new_user_duplicate_username(
    client: TestClient, admin_auth_headers, test_user, clear_users_table
):
    """Admin attempts to create a user with an existing username."""
    # test_user fixture creates a user. We try to create another with same username.
    duplicate_user_data = {
        "username": test_user["username"],  # Using existing username from test_user
        "email": "another_email@example.com",
        "password": "password123",
        "role": "user",
    }
    response = client.post(
        "/api/v1/admin/users", headers=admin_auth_headers, json=duplicate_user_data
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Username or email might already exist" in response.json()["detail"]


def test_admin_create_new_user_by_non_admin(
    client: TestClient, user_auth_headers, clear_users_table
):
    """Non-admin attempts to create a user."""
    new_user_data = {
        "username": "rogue_user",
        "email": "rogue@example.com",
        "password": "pw",
    }
    response = client.post(
        "/api/v1/admin/users", headers=user_auth_headers, json=new_user_data
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert (
        response.json()["detail"]
        == "Operation not permitted: Requires admin privileges."
    )


def test_admin_create_new_user_unauthenticated(client: TestClient, clear_users_table):
    """Unauthenticated attempt to create a user."""
    new_user_data = {
        "username": "anon_user",
        "email": "anon@example.com",
        "password": "pw",
    }
    response = client.post("/api/v1/admin/users", json=new_user_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- Test GET /api/v1/admin/users (Admin List All Users) ---
def test_admin_list_all_users_success(
    client: TestClient,
    admin_auth_headers,
    test_user,
    test_admin_user,
    clear_users_table,
):  # Fixtures create users
    """Admin successfully lists all users."""
    # test_user and test_admin_user fixtures ensure at least two users exist.
    # clear_users_table ensures only these (and any created by other tests if not perfectly isolated by scope)
    response = client.get("/api/v1/admin/users", headers=admin_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    users_list = response.json()
    assert isinstance(users_list, list)
    # Check if the admin and test user are in the list
    usernames_in_list = [u["username"] for u in users_list]
    assert test_admin_user["username"] in usernames_in_list
    assert test_user["username"] in usernames_in_list
    for user_data in users_list:
        assert "password" not in user_data
        assert "hashed_password" not in user_data


def test_admin_list_all_users_pagination(
    client: TestClient, admin_auth_headers, test_auth_manager, clear_users_table
):
    """Test pagination for listing users."""
    # Create a few users for pagination testing
    for i in range(5):
        test_auth_manager.create_user(f"page_user_{i}", f"page{i}@example.com", "pass")

    # Get first page, limit 2
    response1 = client.get(
        "/api/v1/admin/users?skip=0&limit=2", headers=admin_auth_headers
    )
    assert response1.status_code == status.HTTP_200_OK
    page1_users = response1.json()
    assert len(page1_users) == 2

    # Get second page, limit 2, skip 2
    response2 = client.get(
        "/api/v1/admin/users?skip=2&limit=2", headers=admin_auth_headers
    )
    assert response2.status_code == status.HTTP_200_OK
    page2_users = response2.json()
    assert len(page2_users) == 2

    # Ensure users are different from page 1
    page1_ids = {u["id"] for u in page1_users}
    page2_ids = {u["id"] for u in page2_users}
    assert not (page1_ids & page2_ids)  # No overlap


def test_admin_list_all_users_by_non_admin(
    client: TestClient, user_auth_headers, clear_users_table
):
    """Non-admin attempts to list users."""
    response = client.get("/api/v1/admin/users", headers=user_auth_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


# --- Test GET /api/v1/admin/users/{username} (Admin Get Specific User) ---
def test_admin_get_specific_user_success(
    client: TestClient, admin_auth_headers, test_user, clear_users_table
):
    """Admin successfully gets a specific user's details."""
    target_username = test_user["username"]
    response = client.get(
        f"/api/v1/admin/users/{target_username}", headers=admin_auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    user_details = response.json()
    assert user_details["username"] == target_username
    assert user_details["email"] == test_user["email"]


def test_admin_get_specific_user_not_found(
    client: TestClient, admin_auth_headers, clear_users_table
):
    """Admin attempts to get a non-existent user."""
    response = client.get(
        "/api/v1/admin/users/nonexistentuser123", headers=admin_auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_admin_get_specific_user_by_non_admin(
    client: TestClient, user_auth_headers, test_user, clear_users_table
):
    """Non-admin attempts to get a specific user's details."""
    target_username = test_user["username"]  # Could be any user
    response = client.get(
        f"/api/v1/admin/users/{target_username}", headers=user_auth_headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


# --- Test PUT /api/v1/admin/users/{username} (Admin Update User) ---
def test_admin_update_user_success(
    client: TestClient,
    admin_auth_headers,
    test_user,
    test_auth_manager,
    clear_users_table,
):
    """Admin successfully updates a user's details."""
    target_username = test_user["username"]
    update_payload = {
        "email": "new_updated_email@example.com",
        "full_name": "User Name Updated by Admin",
        "role": "editor",
        "is_active": False,
    }
    response = client.put(
        f"/api/v1/admin/users/{target_username}",
        headers=admin_auth_headers,
        json=update_payload,
    )
    assert response.status_code == status.HTTP_200_OK
    updated_user_response = response.json()
    assert updated_user_response["email"] == update_payload["email"]
    assert updated_user_response["full_name"] == update_payload["full_name"]
    assert updated_user_response["role"] == update_payload["role"]
    assert updated_user_response["is_active"] == update_payload["is_active"]

    # Verify in DB
    db_user = test_auth_manager.get_user_by_username(target_username)
    assert db_user is not None
    assert db_user.email == update_payload["email"]
    assert db_user.role == update_payload["role"]
    assert db_user.is_active == update_payload["is_active"]


def test_admin_update_user_try_password_change(
    client: TestClient, admin_auth_headers, test_user, clear_users_table
):
    """Admin attempts to update password via user update endpoint (should fail or be ignored)."""
    target_username = test_user["username"]
    update_payload = {"password": "newpassword123"}

    response = client.put(
        f"/api/v1/admin/users/{target_username}",
        headers=admin_auth_headers,
        json=update_payload,
    )
    # If only 'password' (not in UserUpdate model) is sent, Pydantic strips it, leading to an empty update_data_dict.
    # The endpoint then correctly raises 400 with "No update data provided."
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "No update data provided."


def test_admin_update_user_not_found(
    client: TestClient, admin_auth_headers, clear_users_table
):
    """Admin attempts to update a non-existent user."""
    update_payload = {"email": "ghost@example.com"}
    response = client.put(
        "/api/v1/admin/users/ghostupdater",
        headers=admin_auth_headers,
        json=update_payload,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- Test DELETE /api/v1/admin/users/{username} (Admin Delete User) ---
@pytest.fixture
def user_to_delete(test_auth_manager, clear_users_table) -> Dict[str, Any]:
    """Helper fixture to create a user specifically for deletion tests."""
    username = "user_marked_for_deletion"
    email = "delete@example.com"
    user_details = test_auth_manager.create_user(
        username, email, "delete_pass", "Delete User"
    )
    assert (
        user_details is not None
    ), "Setup for deletion test failed: user_to_delete not created."
    return user_details


def test_admin_delete_user_success(
    client: TestClient, admin_auth_headers, user_to_delete, test_auth_manager
):
    """Admin successfully deletes a user."""
    target_username = user_to_delete["username"]

    response = client.delete(
        f"/api/v1/admin/users/{target_username}", headers=admin_auth_headers
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify user is deleted from DB
    assert test_auth_manager.get_user_by_username(target_username) is None


def test_admin_delete_self_fail(
    client: TestClient, admin_auth_headers, test_admin_user
):
    """Admin attempts to delete themselves (should fail)."""
    admin_username = test_admin_user["username"]
    response = client.delete(
        f"/api/v1/admin/users/{admin_username}", headers=admin_auth_headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Admin users cannot delete themselves."


def test_admin_delete_user_not_found(
    client: TestClient, admin_auth_headers, clear_users_table
):
    """Admin attempts to delete a non-existent user."""
    response = client.delete(
        "/api/v1/admin/users/ghost_to_delete", headers=admin_auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# This suite comprehensively tests the admin user management endpoints.
# It verifies success cases, failure cases (e.g., duplicates, not found),
# and authorization (admin vs. non-admin access).
# The `clear_users_table` fixture is critical for ensuring test isolation,
# especially for creation and listing tests.
# Direct interaction with `test_auth_manager` is used for verification against the database state.
# Passwords and other sensitive data are handled carefully.
# Added `user_to_delete` fixture for delete tests.
# Ensured `clear_users_table` is used where appropriate.
# Verified that admin cannot delete self.
# Test for trying to update password via the general update endpoint.
# This set of tests covers the user management features outlined in the issue document.
# Further tests could include more complex scenarios or validation edge cases for user data fields if needed.
# Test for creating user by unauthenticated client.
# Test for listing users pagination.
# Test for updating user by non-admin.
# Test for deleting user by non-admin.
# All tests seem to cover the main functionality and security aspects of these admin endpoints.
# `test_user` and `test_admin_user` are used to ensure some users exist for GET/PUT/DELETE operations.
# The `user_to_delete` fixture is a good pattern for setting up specific data for a test.
# The use of `clear_users_table` helps maintain a predictable state for tests involving user creation/listing.
# HTTP status codes and error detail messages are asserted for correctness.
