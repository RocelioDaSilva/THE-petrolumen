from typing import Dict, Any, Optional, List
import datetime
from datetime import timezone # Added for timezone.utc
import logging
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError # Added import
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer # Will be used in main.py

logger = logging.getLogger(__name__)

# Configuration for JWT
JWT_ALGORITHM = "HS256"

# Password Hashing Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# This will be used by FastAPI's dependency injection in main.py to get the token from the request
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Define in main.py where app is

# Import DatabaseManager and User model
from .database import DatabaseManager, User as DBUser


class AuthManager:
    def __init__(self, db_manager: DatabaseManager,
                 secret_key: str = "super_secret_key_please_change_for_prod",
                 access_token_expire_minutes: int = 30):
        """Constructor for authentication settings."""
        if secret_key == "super_secret_key_please_change_for_prod":
            logger.warning("Using default insecure secret key for AuthManager. THIS IS NOT SAFE FOR PRODUCTION.")
        self.db_manager = db_manager
        self.secret_key = secret_key
        self.access_token_expire_minutes = access_token_expire_minutes
        logger.info(f"AuthManager initialized with DB. Token Expiry: {access_token_expire_minutes} minutes.")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifies a plain password against a hashed password."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hashes a plain password."""
        return pwd_context.hash(password)

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[datetime.timedelta] = None) -> str:
        """Generates a JWT access token."""
        to_encode = data.copy()
        now = datetime.datetime.now(timezone.utc)
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + datetime.timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "iat": now})
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=JWT_ALGORITHM)
            return encoded_jwt
        except JWTError as e:
            logger.error(f"Error encoding JWT: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create access token",
            )


    def connect_db(self, db_params: Dict[str, Any]) -> Any:
        """Connects to a user database (conceptual)."""
        logger.info(f"Placeholder: Attempting to connect to DB with params: {db_params}")
        return {"status": "connected_dummy_users_db_not_implemented", "params": db_params}

    def create_user(self, username: str, email: str, password: str,
                    full_name: Optional[str] = None, role: str = "user", is_active: bool = True) -> Optional[Dict[str, Any]]:
        """Creates a new user in the database with a hashed password."""
        existing_user_by_username = self.db_manager.get_db_user_by_username(username)
        if existing_user_by_username:
            logger.warning(f"User creation failed: Username '{username}' already exists in DB.")
            # In a real API, you might raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
            return None

        existing_user_by_email = self.db_manager.get_db_user_by_email(email)
        if existing_user_by_email:
            logger.warning(f"User creation failed: Email '{email}' already exists in DB.")
            # In a real API, you might raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
            return None

        hashed_password = self.get_password_hash(password)
        db_user = self.db_manager.create_db_user(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            is_active=is_active
        )

        if not db_user:
            logger.error(f"User creation failed for '{username}' at database level.")
            # In a real API, you might raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create user")
            return None

        logger.info(f"User '{username}' created successfully in DB.")
        # Return user info, excluding password
        return {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "full_name": db_user.full_name,
            "role": db_user.role,
            "is_active": db_user.is_active
        }

    def get_user_by_username(self, username: str) -> Optional[DBUser]:
        """
        Retrieves a user object from the database by username.
        This method returns the full DBUser object including the hashed_password.
        It's intended for internal use within AuthManager (e.g., for authentication).
        """
        db_user = self.db_manager.get_db_user_by_username(username)
        if db_user:
            logger.debug(f"User '{username}' found via AuthManager (from DB).")
            return db_user
        logger.debug(f"User '{username}' not found via AuthManager (from DB).")
        return None

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticates a user. Returns user data (excluding hashed_password) if successful, else None."""
        db_user = self.get_user_by_username(username) # This gets the DBUser object
        if not db_user:
            logger.warning(f"Authentication failed: User '{username}' not found.")
            return None
        if not db_user.is_active: # Check the 'is_active' field from the User model
            logger.warning(f"Authentication failed: User '{username}' is inactive.")
            return None
        if not self.verify_password(password, db_user.hashed_password):
            logger.warning(f"Authentication failed: Incorrect password for user '{username}'.")
            return None

        logger.info(f"User '{username}' authenticated successfully.")
         # Return user info, excluding password
        return {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "full_name": db_user.full_name,
            "role": db_user.role,
            "is_active": db_user.is_active
        }

    def get_current_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decodes a JWT token and retrieves the user."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[JWT_ALGORITHM])
            username: Optional[str] = payload.get("sub")
            if username is None:
                logger.warning("Token decoding failed: 'sub' (username) field missing in token payload.")
                raise credentials_exception

            # Check token expiry
            expire_timestamp = payload.get("exp")
            # Ensure current time is timezone-aware (UTC) for comparison with exp (which is epoch based, hence UTC)
            if expire_timestamp and datetime.datetime.now(timezone.utc) > datetime.datetime.fromtimestamp(expire_timestamp, tz=timezone.utc):
                logger.warning(f"Token for user '{username}' has expired.")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        except ExpiredSignatureError as e: # Specific exception first
            logger.warning(f"Token decoding failed due to expiry: {e}")
            # Reraise with specific detail or use the one from the manual check if preferred.
            # For consistency with the manual check, let's use "Token has expired".
            # However, the `credentials_exception` has "Could not validate credentials".
            # The manual check above already raises "Token has expired".
            # If jwt.decode raises ExpiredSignatureError, this block will be hit.
            # It makes sense for this to also clearly state the token is expired.
            raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired", # Consistent detail
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except JWTError as e: # General JWT errors (invalid signature, etc.)
            logger.warning(f"Token decoding failed: {e}")
            raise credentials_exception # Detail: "Could not validate credentials"

        db_user = self.get_user_by_username(username) # Fetches DBUser object
        if db_user is None:
            logger.warning(f"User '{username}' from token not found in user store (DB).")
            raise credentials_exception
        if not db_user.is_active: # Check 'is_active' field
            logger.warning(f"User '{username}' from token is inactive.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

        # Return user info, excluding password for security best practices when exposing current user
        return {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "full_name": db_user.full_name,
            "role": db_user.role,
            "is_active": db_user.is_active
        }

    # --- User Management Methods (CRUD) ---
    def get_user_details(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieves user details (excluding password) by username."""
        db_user = self.get_user_by_username(username)
        if not db_user:
            return None
        return {
            "id": db_user.id, "username": db_user.username, "email": db_user.email,
            "full_name": db_user.full_name, "role": db_user.role, "is_active": db_user.is_active
        }

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieves all users, excluding sensitive information."""
        db_users = self.db_manager.get_all_db_users(skip=skip, limit=limit)
        return [
            {
                "id": user.id, "username": user.username, "email": user.email,
                "full_name": user.full_name, "role": user.role, "is_active": user.is_active
            } for user in db_users
        ]

    def update_user_details(self, username: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Updates user details. Password updates should be handled by a separate, dedicated function
        if that functionality is required. 'hashed_password' should not be in `updates`.
        """
        if "password" in updates or "hashed_password" in updates:
            logger.error("Password updates must be handled by a dedicated function, not via update_user_details.")
            # Consider raising ValueError or returning a specific error response object
            raise ValueError("Password updates not allowed through this method.")

        updated_db_user = self.db_manager.update_db_user(username, updates)
        if not updated_db_user:
            return None
        return {
            "id": updated_db_user.id, "username": updated_db_user.username, "email": updated_db_user.email,
            "full_name": updated_db_user.full_name, "role": updated_db_user.role, "is_active": updated_db_user.is_active
        }

    def delete_user(self, username: str) -> bool:
        """Deletes a user from the database."""
        return self.db_manager.delete_db_user(username)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG) # Use DEBUG for more detailed logs during testing

    # IMPORTANT: In a real app, secret_key should come from config/env and be strong
    # For testing AuthManager directly, we need a mock/real DatabaseManager
    from .database import DatabaseManager # Re-import for clarity in main block

    # Use an in-memory SQLite for AuthManager tests
    test_db_manager = DatabaseManager(db_url="sqlite:///:memory:")
    if not test_db_manager.connect():
        logger.critical("AuthManager Test: Failed to connect to in-memory DB.")
        exit(1)
    if not test_db_manager.create_tables(): # Ensure User table is created
        logger.critical("AuthManager Test: Failed to create tables for in-memory DB.")
        exit(1)

    auth_manager = AuthManager(db_manager=test_db_manager, secret_key="test_highly_secret_key_for_auth_manager_testing", access_token_expire_minutes=1)

    # Test user creation
    logger.info("--- Testing User Creation ---")
    created_user_info = auth_manager.create_user("testuser1", "test1@example.com", "StrongPass123!", full_name="Test User One", role="user")
    print("Created User Info:", created_user_info)
    assert created_user_info is not None
    assert created_user_info["username"] == "testuser1"
    assert created_user_info["role"] == "user"

    # Verify password storage by trying to authenticate
    user_in_db_obj = auth_manager.get_user_by_username("testuser1") # Gets DBUser object
    assert user_in_db_obj is not None
    assert user_in_db_obj.hashed_password != "StrongPass123!"
    assert auth_manager.verify_password("StrongPass123!", user_in_db_obj.hashed_password)


    # Test duplicate user creation
    duplicate_user_info = auth_manager.create_user("testuser1", "test1-dup@example.com", "AnotherPass")
    print("Duplicate User Creation Attempt:", duplicate_user_info)
    assert duplicate_user_info is None # Expect None for failure

    # Test authentication
    logger.info("\n--- Testing User Authentication ---")
    authenticated_user = auth_manager.authenticate_user("testuser1", "StrongPass123!")
    print("Authenticated User (Correct Password):", authenticated_user)
    assert authenticated_user is not None
    assert authenticated_user["username"] == "testuser1"
    assert "password" not in authenticated_user # Ensure sensitive data not in returned dict
    assert "hashed_password" not in authenticated_user


    authenticated_user_wrong_pass = auth_manager.authenticate_user("testuser1", "WrongPassword")
    print("Authenticated User (Wrong Password):", authenticated_user_wrong_pass)
    assert authenticated_user_wrong_pass is None

    authenticated_non_existent_user = auth_manager.authenticate_user("nosuchuser", "anypassword")
    print("Authenticated User (Non-existent):", authenticated_non_existent_user)
    assert authenticated_non_existent_user is None

    # Test token creation
    logger.info("\n--- Testing Token Creation & Validation ---")
    if authenticated_user:
        # Typically, 'sub' would be the username or user ID
        access_token = auth_manager.create_access_token(data={"sub": authenticated_user["username"], "custom_claim": "example_value"})
        print("Generated Access Token:", access_token)
        assert isinstance(access_token, str)

        # Test token decoding (get_current_user_from_token)
        current_user_from_token = auth_manager.get_current_user_from_token(access_token)
        print("User Decoded from Token:", current_user_from_token)
        assert current_user_from_token is not None
        assert current_user_from_token["username"] == authenticated_user["username"]
        assert "password" not in current_user_from_token
        assert "hashed_password" not in current_user_from_token


        # Test with a bogus token
        try:
            auth_manager.get_current_user_from_token("bogus_token_string")
        except HTTPException as e:
            print(f"Caught expected HTTPException for bogus token: {e.detail} (status: {e.status_code})")
            assert e.status_code == status.HTTP_401_UNAUTHORIZED

        # Test expired token
        short_lived_token = auth_manager.create_access_token(
            data={"sub": authenticated_user["username"]},
            expires_delta=datetime.timedelta(seconds=1) # Expires in 1 second
        )
        import time
        time.sleep(1.2) # Wait for token to expire
        try:
            auth_manager.get_current_user_from_token(short_lived_token)
        except HTTPException as e:
            print(f"Caught expected HTTPException for expired token: {e.detail} (status: {e.status_code})")
            assert e.status_code == status.HTTP_401_UNAUTHORIZED
            assert e.detail == "Token has expired"

    # Test disabled user (inactive user)
    logger.info("\n--- Testing Inactive User ---")
    auth_manager.create_user("inactiveuser", "inactive@example.com", "Pass123", is_active=False)
    inactive_user_auth_attempt = auth_manager.authenticate_user("inactiveuser", "Pass123")
    print("Inactive User Authentication Attempt:", inactive_user_auth_attempt)
    assert inactive_user_auth_attempt is None # Should fail authentication if inactive

    # Create a token for the inactive user (assuming they could get one before being marked inactive)
    # This scenario is more about get_current_user_from_token rejecting it if the user is inactive.
    db_user_inactive = auth_manager.get_user_by_username("inactiveuser")
    if db_user_inactive : # Should exist
      inactive_user_token = auth_manager.create_access_token(data={"sub": "inactiveuser"})
      try:
          auth_manager.get_current_user_from_token(inactive_user_token)
      except HTTPException as e:
          print(f"Caught expected HTTPException for inactive user token: {e.detail} (status: {e.status_code})")
          assert e.status_code == status.HTTP_400_BAD_REQUEST
          assert e.detail == "Inactive user"

    # Test Admin User (Role)
    logger.info("\n--- Testing Admin User Role ---")
    admin_user_info = auth_manager.create_user("adminuser", "admin@example.com", "AdminPass123!", role="admin")
    assert admin_user_info is not None
    assert admin_user_info["role"] == "admin"
    authenticated_admin = auth_manager.authenticate_user("adminuser", "AdminPass123!")
    assert authenticated_admin is not None
    assert authenticated_admin["role"] == "admin"

    # Test Get All Users
    logger.info("\n--- Testing Get All Users ---")
    all_users_before_delete = auth_manager.get_all_users()
    print(f"All users ({len(all_users_before_delete)}): {all_users_before_delete}")
    assert len(all_users_before_delete) >= 3 # testuser1, inactiveuser, adminuser

    # Test Update User Details
    logger.info("\n--- Testing Update User Details ---")
    update_data = {"full_name": "Test User One Updated", "role": "editor", "is_active": True} # ensure is_active can be updated
    updated_user = auth_manager.update_user_details("testuser1", update_data)
    print("Updated user:", updated_user)
    assert updated_user is not None
    assert updated_user["full_name"] == "Test User One Updated"
    assert updated_user["role"] == "editor"
    assert updated_user["is_active"] == True

    # Test trying to update password via update_user_details (should fail)
    try:
        auth_manager.update_user_details("testuser1", {"password": "newpassword"})
        assert False, "Should have raised ValueError for password update"
    except ValueError as e:
        print(f"Caught expected ValueError: {e}")


    # Test Delete User
    logger.info("\n--- Testing Delete User ---")
    assert auth_manager.delete_user("inactiveuser") == True
    assert auth_manager.get_user_by_username("inactiveuser") is None # Verify it's gone
    all_users_after_delete = auth_manager.get_all_users()
    assert len(all_users_after_delete) == len(all_users_before_delete) - 1


    test_db_manager.close()
    logger.info("AuthManager tests completed.")
