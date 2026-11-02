from typing import Dict, Any, Optional, List
import datetime
from datetime import timezone
import logging
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import HTTPException, status

# Import DatabaseManager and User model from the new core location
from .database_manager import DatabaseManager
from .database_models import (
    User as DBUser,
)  # Alias to DBUser to match original usage if needed

logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"  # Define algorithm, could be from settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthManager:
    def __init__(
        self,
        db_manager: DatabaseManager,
        secret_key: str,  # Make secret_key required
        access_token_expire_minutes: int = 30,
    ):
        if not secret_key:  # Basic check
            logger.critical(
                "AuthManager initialized WITHOUT a secret key. THIS IS INSECURE."
            )
            raise ValueError("A secret key is required for AuthManager.")
        self.db_manager = db_manager
        self.secret_key = secret_key
        self.access_token_expire_minutes = access_token_expire_minutes
        logger.info(
            f"AuthManager initialized. Token Expiry: {access_token_expire_minutes} minutes."
        )

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def create_access_token(
        self, data: Dict[str, Any], expires_delta: Optional[datetime.timedelta] = None
    ) -> str:
        to_encode = data.copy()
        now = datetime.datetime.now(timezone.utc)
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + datetime.timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "iat": now})
        try:
            encoded_jwt = jwt.encode(
                to_encode, self.secret_key, algorithm=JWT_ALGORITHM
            )
            return encoded_jwt
        except JWTError as e:
            logger.error(f"Error encoding JWT: {e}")
            # It's generally better to raise a specific internal error or log and return None/False
            # rather than HTTPException from a non-endpoint class.
            # For now, keeping similar to original structure.
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create access token due to an internal error.",
            )

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        role: str = "user",
        is_active: bool = True,
    ) -> Optional[Dict[str, Any]]:
        existing_user_by_username = self.db_manager.get_db_user_by_username(username)
        if existing_user_by_username:
            logger.warning(
                f"User creation failed: Username '{username}' already exists."
            )
            return None

        existing_user_by_email = self.db_manager.get_db_user_by_email(email)
        if existing_user_by_email:
            logger.warning(f"User creation failed: Email '{email}' already exists.")
            return None

        hashed_password = self.get_password_hash(password)
        db_user = self.db_manager.create_db_user(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            is_active=is_active,
        )

        if not db_user:
            logger.error(f"User creation failed for '{username}' at database level.")
            return None

        logger.info(f"User '{username}' created successfully.")
        return {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "full_name": db_user.full_name,
            "role": db_user.role,
            "is_active": db_user.is_active,
        }

    def get_user_by_username(self, username: str) -> Optional[DBUser]:
        """Internal method to get DBUser object, including hashed_password."""
        return self.db_manager.get_db_user_by_username(username)

    def authenticate_user(
        self, username: str, password: str
    ) -> Optional[Dict[str, Any]]:
        db_user = self.get_user_by_username(username)
        if not db_user:
            logger.warning(f"Authentication failed: User '{username}' not found.")
            return None
        if not db_user.is_active:
            logger.warning(f"Authentication failed: User '{username}' is inactive.")
            return None
        if not self.verify_password(password, db_user.hashed_password):
            logger.warning(
                f"Authentication failed: Incorrect password for user '{username}'."
            )
            return None

        logger.info(f"User '{username}' authenticated successfully.")
        return {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "full_name": db_user.full_name,
            "role": db_user.role,
            "is_active": db_user.is_active,
        }

    def get_current_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        expired_token_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
        inactive_user_exception = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,  # Or 403 Forbidden
            detail="Inactive user",
        )

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[JWT_ALGORITHM])
            username: Optional[str] = payload.get("sub")
            if username is None:
                logger.warning("Token decoding failed: 'sub' (username) field missing.")
                raise credentials_exception

            # Explicitly check 'exp' claim
            expire_timestamp = payload.get("exp")
            if expire_timestamp and datetime.datetime.now(
                timezone.utc
            ) > datetime.datetime.fromtimestamp(expire_timestamp, tz=timezone.utc):
                logger.warning(
                    f"Token for user '{username}' has expired (manual check)."
                )
                raise expired_token_exception

        except ExpiredSignatureError:  # Handled by jwt.decode
            logger.warning(
                "Token decoding failed due to signature expiry (jose.exceptions.ExpiredSignatureError)."
            )
            raise expired_token_exception
        except JWTError as e:  # Other JWT errors
            logger.warning(f"Token decoding failed due to JWTError: {e}")
            raise credentials_exception

        db_user = self.get_user_by_username(username)
        if db_user is None:
            logger.warning(f"User '{username}' from token not found in DB.")
            raise credentials_exception
        if not db_user.is_active:
            logger.warning(f"User '{username}' from token is inactive.")
            raise inactive_user_exception

        return {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "full_name": db_user.full_name,
            "role": db_user.role,
            "is_active": db_user.is_active,
        }

    def get_user_details(self, username: str) -> Optional[Dict[str, Any]]:
        db_user = self.get_user_by_username(username)
        if not db_user:
            return None
        return {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "full_name": db_user.full_name,
            "role": db_user.role,
            "is_active": db_user.is_active,
        }

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        db_users = self.db_manager.get_all_db_users(skip=skip, limit=limit)
        return [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
            }
            for user in db_users
        ]

    def update_user_details(
        self, username: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if "password" in updates or "hashed_password" in updates:
            logger.error("Password updates must be handled by a dedicated function.")
            raise ValueError("Password updates not allowed through this method.")

        updated_db_user = self.db_manager.update_db_user(username, updates)
        if not updated_db_user:
            return None
        return {
            "id": updated_db_user.id,
            "username": updated_db_user.username,
            "email": updated_db_user.email,
            "full_name": updated_db_user.full_name,
            "role": updated_db_user.role,
            "is_active": updated_db_user.is_active,
        }

    def delete_user(self, username: str) -> bool:
        return self.db_manager.delete_db_user(username)
