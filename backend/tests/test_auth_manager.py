import pytest
from fastapi import HTTPException, status
import datetime
import time  # For testing token expiry
import logging  # It's good practice to have logging available

# Corrected imports
from gaia_genesis.core.auth_manager import AuthManager

# from gaia_genesis.core.database_manager import ( # Unused
#     DatabaseManager,
# )  # For type hints if needed, or mocking
# from gaia_genesis.core.database_models import User as DBUser  # Unused

logger = logging.getLogger(__name__)

# This module tests AuthManager.
# It uses fixtures from conftest.py:
# - `test_db_manager`: A DatabaseManager connected to the test DB.
# - `test_auth_manager`: An AuthManager instance using `test_db_manager`.
# - `db_session`: A SQLAlchemy session for direct DB checks if needed.
# - `clear_users_table`: Ensures the users table is empty before each test.


# --- Test User Creation and Retrieval ---
def test_create_user_successful(test_auth_manager: AuthManager, clear_users_table):
    """Test successful user creation."""
    username = "auth_test_user"
    email = "auth_test@example.com"
    password = "strongpassword123"

    created_user = test_auth_manager.create_user(
        username, email, password, "Auth Test User", "user"
    )
    assert created_user is not None
    assert created_user["username"] == username
    assert created_user["email"] == email
    assert "id" in created_user
    assert created_user["role"] == "user"
    assert created_user["is_active"] is True

    db_user_obj = test_auth_manager.get_user_by_username(username)
    assert db_user_obj is not None
    assert db_user_obj.email == email
    assert test_auth_manager.verify_password(password, db_user_obj.hashed_password)


def test_create_user_duplicate_username(
    test_auth_manager: AuthManager, clear_users_table
):
    """Test creating a user with a duplicate username fails."""
    username = "duplicate_uname"
    test_auth_manager.create_user(username, "email1@example.com", "pass1")

    failed_creation = test_auth_manager.create_user(
        username, "email2@example.com", "pass2"
    )
    assert failed_creation is None


def test_create_user_duplicate_email(test_auth_manager: AuthManager, clear_users_table):
    """Test creating a user with a duplicate email fails."""
    email = "duplicate_email@example.com"
    test_auth_manager.create_user("userA", email, "pass1")

    failed_creation = test_auth_manager.create_user("userB", email, "pass2")
    assert failed_creation is None


# --- Test User Authentication ---
def test_authenticate_user_successful(
    test_auth_manager: AuthManager, clear_users_table
):
    """Test successful user authentication."""
    username = "auth_user_login"
    password = "login_pass! সুরক্ষিত"
    test_auth_manager.create_user(username, f"{username}@example.com", password)

    authenticated_user = test_auth_manager.authenticate_user(username, password)
    assert authenticated_user is not None
    assert authenticated_user["username"] == username
    assert "password" not in authenticated_user
    assert "hashed_password" not in authenticated_user


def test_authenticate_user_wrong_password(
    test_auth_manager: AuthManager, clear_users_table
):
    """Test authentication with wrong password fails."""
    username = "auth_user_wrong_pass"
    password = "correct_password"
    test_auth_manager.create_user(username, f"{username}@example.com", password)

    assert test_auth_manager.authenticate_user(username, "wrong_password_here") is None


def test_authenticate_non_existent_user(
    test_auth_manager: AuthManager, clear_users_table
):
    """Test authentication for a user that does not exist fails."""
    assert test_auth_manager.authenticate_user("ghost_user", "any_pass") is None


def test_authenticate_inactive_user(test_auth_manager: AuthManager, clear_users_table):
    """Test authentication for an inactive user fails."""
    username = "inactive_user_test"
    password = "pa$$word"
    test_auth_manager.create_user(
        username, f"{username}@example.com", password, is_active=False
    )

    assert test_auth_manager.authenticate_user(username, password) is None


# --- Test Token Creation and Validation ---
def test_create_and_validate_access_token(
    test_auth_manager: AuthManager, clear_users_table
):
    """Test JWT creation and validation."""
    username = "token_user"
    password = "token_password_123"
    user_data = test_auth_manager.create_user(
        username, f"{username}@example.com", password
    )
    assert user_data is not None

    token_data = {"sub": username, "custom_field": "test_value"}
    access_token = test_auth_manager.create_access_token(data=token_data)
    assert isinstance(access_token, str)

    current_user_from_token = test_auth_manager.get_current_user_from_token(
        access_token
    )
    assert current_user_from_token is not None
    assert current_user_from_token["username"] == username


def test_token_validation_expired(test_auth_manager: AuthManager, clear_users_table):
    """Test that an expired token fails validation."""
    username = "expired_token_user"
    test_auth_manager.create_user(username, f"{username}@example.com", "pass")

    expired_token = test_auth_manager.create_access_token(
        data={"sub": username},
        expires_delta=datetime.timedelta(seconds=1),  # Use datetime.timedelta
    )
    time.sleep(1.2)  # Ensure token is expired

    with pytest.raises(HTTPException) as exc_info:
        test_auth_manager.get_current_user_from_token(expired_token)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    # Detail message might vary slightly based on exact exception handling in AuthManager
    assert (
        "Token has expired" in exc_info.value.detail
        or "Signature has expired" in exc_info.value.detail
    )


def test_token_validation_invalid_signature(
    test_auth_manager: AuthManager, clear_users_table
):
    """Test that a token with an invalid signature (e.g., wrong secret key) fails."""
    username = "sig_user"
    test_auth_manager.create_user(username, f"{username}@example.com", "pass")

    hacker_auth_manager = AuthManager(
        db_manager=test_auth_manager.db_manager,
        secret_key="completely_different_secret_key",
    )
    rogue_token = hacker_auth_manager.create_access_token(data={"sub": username})

    with pytest.raises(HTTPException) as exc_info:
        test_auth_manager.get_current_user_from_token(rogue_token)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in exc_info.value.detail


def test_token_validation_inactive_user(
    test_auth_manager: AuthManager, clear_users_table
):
    """Test that a token for an inactive user fails validation."""
    username = "token_inactive_user"
    password = "securePassword"
    test_auth_manager.create_user(
        username, f"{username}@example.com", password, is_active=False
    )

    access_token = test_auth_manager.create_access_token(data={"sub": username})

    with pytest.raises(HTTPException) as exc_info:
        test_auth_manager.get_current_user_from_token(access_token)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST  # Or 403 Forbidden
    assert exc_info.value.detail == "Inactive user"


# --- Test User Management (CRUD through AuthManager) ---
def test_get_all_users(test_auth_manager: AuthManager, clear_users_table):
    """Test retrieving all users."""
    test_auth_manager.create_user("crud_user1", "crud1@example.com", "pass")
    test_auth_manager.create_user("crud_user2", "crud2@example.com", "pass")

    users = test_auth_manager.get_all_users()
    assert (
        len(users) >= 2
    )  # Could be more if other tests don't clean up perfectly or if test_db is shared
    usernames = [u["username"] for u in users]
    assert "crud_user1" in usernames
    assert "crud_user2" in usernames
    for user_dict in users:
        assert "hashed_password" not in user_dict


def test_update_user_details(test_auth_manager: AuthManager, clear_users_table):
    """Test updating user details."""
    username = "update_me_auth"
    test_auth_manager.create_user(
        username, "original@update.com", "pass", "Original Name", "user"
    )

    updates = {
        "email": "updated@update.com",
        "full_name": "Updated Name Here",
        "role": "editor",
        "is_active": False,
    }
    updated_user = test_auth_manager.update_user_details(username, updates)
    assert updated_user is not None
    assert updated_user["email"] == updates["email"]
    assert updated_user["full_name"] == updates["full_name"]
    assert updated_user["role"] == updates["role"]
    assert updated_user["is_active"] == updates["is_active"]

    db_user_obj = test_auth_manager.get_user_by_username(username)
    assert db_user_obj is not None
    assert db_user_obj.email == updates["email"]
    assert db_user_obj.role == updates["role"]
    assert db_user_obj.is_active == updates["is_active"]

    with pytest.raises(
        ValueError, match="Password updates not allowed through this method"
    ):
        test_auth_manager.update_user_details(username, {"password": "newpass123"})

    with pytest.raises(
        ValueError, match="Password updates not allowed through this method"
    ):
        test_auth_manager.update_user_details(username, {"hashed_password": "newhash"})


def test_delete_user(test_auth_manager: AuthManager, clear_users_table):
    """Test deleting a user."""
    username_to_delete = "delete_target_auth"
    test_auth_manager.create_user(username_to_delete, "delete@auth.com", "pass")

    assert test_auth_manager.delete_user(username_to_delete) is True
    assert test_auth_manager.get_user_by_username(username_to_delete) is None

    assert test_auth_manager.delete_user("nosuchuser_auth_delete") is False


# --- Test AuthManager Initialization ---
def test_auth_manager_init_no_secret_key(test_db_manager):
    """Test AuthManager initialization fails without a secret key."""
    with pytest.raises(ValueError, match="A secret key is required for AuthManager"):
        AuthManager(db_manager=test_db_manager, secret_key="")
    with pytest.raises(ValueError, match="A secret key is required for AuthManager"):
        AuthManager(db_manager=test_db_manager, secret_key=None)


# --- More granular token validation tests ---
def test_token_validation_missing_sub_claim(test_auth_manager: AuthManager, clear_users_table):
    """Test that a token missing the 'sub' claim fails validation."""
    # Create a token with no 'sub' (username)
    # Note: This requires knowing the internal structure of create_access_token or using a different way
    # to craft such a token if create_access_token always enforces 'sub'.
    # For this test, let's assume we can craft a payload that create_access_token would use.
    # The create_access_token method itself doesn't require 'sub' in its input `data` dict,
    # but the `get_current_user_from_token` expects 'sub' in the decoded payload.

    # We will create a token with some other data, but not 'sub'
    # This token will be for a non-existent user effectively, but the key is 'sub' missing.
    malformed_token_payload = {"user_id": 123, "custom_info": "some_val"}

    # Use the same AuthManager instance to create the token to ensure the same secret key and algo are used.
    # The `create_access_token` method adds 'exp' and 'iat'.
    malformed_access_token = test_auth_manager.create_access_token(data=malformed_token_payload)

    with pytest.raises(HTTPException) as exc_info:
        test_auth_manager.get_current_user_from_token(malformed_access_token)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in exc_info.value.detail # This is the generic message for various JWT issues including missing sub
    # A more specific check could be added if the error message for missing 'sub' was distinct.


def test_create_user_db_failure_simulation(
    test_auth_manager: AuthManager, clear_users_table, mocker
):
    """Test create_user when db_manager.create_db_user returns None (simulating DB error)."""
    username = "db_fail_user"
    email = "dbfail@example.com"
    password = "password123"

    # Mock db_manager.create_db_user to return None
    mocker.patch.object(test_auth_manager.db_manager, 'create_db_user', return_value=None)

    created_user = test_auth_manager.create_user(username, email, password)

    assert created_user is None
    # Verify that get_db_user_by_username and get_db_user_by_email were called before create_db_user
    # This requires more complex mocking if we want to ensure the checks for existing user happened.
    # For now, just checking the outcome of create_user is sufficient.
    test_auth_manager.db_manager.create_db_user.assert_called_once()


# (Optional/Low Priority) Test for jwt.encode error in create_access_token
# This would require mocking jose.jwt.encode which can be complex.
# def test_create_access_token_jwt_encode_error(test_auth_manager: AuthManager, mocker):
#     """Test create_access_token when jose.jwt.encode raises JWTError."""
#     mocker.patch('jose.jwt.encode', side_effect=JWTError("Simulated encoding error"))
#     with pytest.raises(HTTPException) as exc_info:
#         test_auth_manager.create_access_token(data={"sub": "testuser"})
#     assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
#     assert "Could not create access token" in exc_info.value.detail
