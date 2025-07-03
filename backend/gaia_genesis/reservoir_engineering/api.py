from typing import Dict, Any, Optional
import datetime
import logging
from jose import JWTError, jwt
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

class AuthManager:
    def __init__(self, secret_key: str SENSITIVE_VALUE_DO_NOT_LOG = "super_secret_key_please_change_for_prod",
                 access_token_expire_minutes: int = 30):
        """Constructor for authentication settings."""
        if secret_key == "super_secret_key_please_change_for_prod":
            logger.warning("Using default insecure secret key for AuthManager. THIS IS NOT SAFE FOR PRODUCTION.")
        self.secret_key = secret_key # SENSITIVE_VALUE_DO_NOT_LOG
        self.access_token_expire_minutes = access_token_expire_minutes
        # In-memory user store for now. In a real app, this would be a database.
        self._users_db: Dict[str, Dict[str, Any]] = {}
        logger.info(f"AuthManager initialized. Token Expiry: {access_token_expire_minutes} minutes.")

    def verify_password(self, plain_password: str SENSITIVE_VALUE_DO_NOT_LOG, hashed_password: str SENSITIVE_VALUE_DO_NOT_LOG) -> bool:
        """Verifies a plain password against a hashed password."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str SENSITIVE_VALUE_DO_NOT_LOG) -> str:
        """Hashes a plain password."""
        return pwd_context.hash(password)

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[datetime.timedelta] = None) -> str:
        """Generates a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.datetime.utcnow() + expires_delta
        else:
            expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "iat": datetime.datetime.utcnow()})
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

    def create_user(self, username: str, email: str, password: str SENSITIVE_VALUE_DO_NOT_LOG,
                    full_name: Optional[str] = None, is_admin: bool = False, disabled: bool = False) -> Dict[str, Any]:
        """Creates a new user in the in-memory store with a hashed password."""
        if username in self._users_db:
            logger.warning(f"User creation failed: Username '{username}' already exists.")
            # In a real API, you'd raise HTTPException here or return a specific error response
            return {"error": "Username already exists"}

        hashed_password = self.get_password_hash(password)
        user_data = {
            "username": username,
            "email": email,
            "full_name": full_name or "",
            "hashed_password": hashed_password,
            "is_admin": is_admin,
            "disabled": disabled
        }
        self._users_db[username] = user_data
        logger.info(f"User '{username}' created successfully.")
        # Return user info, excluding password
        return {k: v for k, v in user_data.items() if k != "hashed_password"}

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieves a user from the in-memory store. Returns the full user dict including hashed_password."""
        user = self._users_db.get(username)
        if user:
            logger.debug(f"User '{username}' found in AuthManager's user store.")
            return user # Returns the dict with hashed_password
        logger.debug(f"User '{username}' not found in AuthManager's user store.")
        return None

    def authenticate_user(self, username: str, password: str SENSITIVE_VALUE_DO_NOT_LOG) -> Optional[Dict[str, Any]]:
        """Authenticates a user. Returns user data (excluding hashed_password) if successful, else None."""
        user = self.get_user(username) # This gets the user dict with hashed_password
        if not user:
            logger.warning(f"Authentication failed: User '{username}' not found.")
            return None
        if user.get("disabled", False):
            logger.warning(f"Authentication failed: User '{username}' is disabled.")
            return None
        if not self.verify_password(password, user["hashed_password"]):
            logger.warning(f"Authentication failed: Incorrect password for user '{username}'.")
            return None

        logger.info(f"User '{username}' authenticated successfully.")
         # Return user info, excluding password
        return {k: v for k, v in user.items() if k != "hashed_password"}

    def get_current_user_from_token(self, token: str SENSITIVE_VALUE_DO_NOT_LOG) -> Optional[Dict[str, Any]]:
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
            if expire_timestamp and datetime.datetime.utcnow() > datetime.datetime.fromtimestamp(expire_timestamp):
                logger.warning(f"Token for user '{username}' has expired.")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        except JWTError as e:
            logger.warning(f"Token decoding failed: {e}")
            raise credentials_exception

        user = self.get_user(username) # Fetches user with hashed_password
        if user is None:
            logger.warning(f"User '{username}' from token not found in user store.")
            raise credentials_exception
        if user.get("disabled", False):
            logger.warning(f"User '{username}' from token is disabled.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

        # Return user info, excluding password for security best practices when exposing current user
        return {k: v for k, v in user.items() if k != "hashed_password"}


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG) # Use DEBUG for more detailed logs during testing

    # IMPORTANT: In a real app, secret_key should come from config/env and be strong
    auth_manager = AuthManager(secret_key="test_highly_secret_key_for_auth_manager_testing", access_token_expire_minutes=1)

    # Test user creation
    logger.info("--- Testing User Creation ---")
    created_user_info = auth_manager.create_user("testuser1", "test1@example.com", "StrongPass123!", full_name="Test User One")
    print("Created User Info:", created_user_info)
    assert created_user_info["username"] == "testuser1"

    # Verify password storage (internal check, not typically exposed)
    user_in_db = auth_manager.get_user("testuser1")
    assert user_in_db is not None
    assert "hashed_password" in user_in_db
    assert user_in_db["hashed_password"] != "StrongPass123!" # Ensure it's hashed
    assert auth_manager.verify_password("StrongPass123!", user_in_db["hashed_password"])

    # Test duplicate user creation
    duplicate_user_info = auth_manager.create_user("testuser1", "test1-dup@example.com", "AnotherPass")
    print("Duplicate User Creation Attempt:", duplicate_user_info)
    assert "error" in duplicate_user_info

    # Test authentication
    logger.info("\n--- Testing User Authentication ---")
    authenticated_user = auth_manager.authenticate_user("testuser1", "StrongPass123!")
    print("Authenticated User (Correct Password):", authenticated_user)
    assert authenticated_user is not None
    assert authenticated_user["username"] == "testuser1"
    assert "hashed_password" not in authenticated_user # Ensure sensitive data not in returned dict

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

    # Test disabled user
    logger.info("\n--- Testing Disabled User ---")
    auth_manager.create_user("disableduser", "disabled@example.com", "Pass123", disabled=True)
    disabled_user_auth_attempt = auth_manager.authenticate_user("disableduser", "Pass123")
    print("Disabled User Authentication Attempt:", disabled_user_auth_attempt)
    assert disabled_user_auth_attempt is None # Should fail authentication if disabled

    # Create a token for the disabled user (assuming they could get one before being disabled)
    # For test purposes, directly create a token for a user marked as disabled in DB
    # This scenario is more about get_current_user_from_token rejecting it.
    user_obj_disabled = auth_manager.get_user("disableduser")
    if user_obj_disabled: # Should exist
      disabled_user_token = auth_manager.create_access_token(data={"sub": "disableduser"})
      try:
          auth_manager.get_current_user_from_token(disabled_user_token)
      except HTTPException as e:
          print(f"Caught expected HTTPException for disabled user token: {e.detail} (status: {e.status_code})")
          assert e.status_code == status.HTTP_400_BAD_REQUEST
          assert e.detail == "Inactive user"

    logger.info("AuthManager tests completed.")
