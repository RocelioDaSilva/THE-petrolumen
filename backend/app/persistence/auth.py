"""AuthManager — user registration/authentication and token validation.

Absorbed from the legacy ``core/auth_manager.py``; the dependency stack was
replaced with :mod:`.security` (stdlib PBKDF2 + HS256).
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from .database import DatabaseManager
from .security import create_access_token, decode_token, hash_password, verify_password

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


class AuthManager:
    def __init__(self, db_manager: DatabaseManager, secret_key: str, expires_minutes: int = 30):
        if not secret_key:
            raise ValueError("A secret key is required for AuthManager.")
        self.db = db_manager
        self.secret_key = secret_key
        self.expires_minutes = expires_minutes

    @staticmethod
    def _public(user: Any) -> dict[str, Any]:
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
        }

    def register(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str | None = None,
        role: str = "user",
    ) -> dict[str, Any] | None:
        if self.db.get_user_by_username(username) or self.db.get_user_by_email(email):
            return None
        user = self.db.create_user(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
        )
        return self._public(user) if user else None

    def authenticate(self, username: str, password: str) -> dict[str, Any] | None:
        user = self.db.get_user_by_username(username)
        if user is None or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return self._public(user)

    def issue_token(self, username: str) -> str:
        return create_access_token(
            subject=username,
            secret_key=self.secret_key,
            expires_minutes=self.expires_minutes,
        )

    def get_current_user(self, token: str) -> dict[str, Any]:
        try:
            payload = decode_token(token, self.secret_key)
        except ValueError as exc:
            raise _UNAUTHORIZED from exc
        username = payload.get("sub")
        if not username:
            raise _UNAUTHORIZED
        user = self.db.get_user_by_username(username)
        if user is None or not user.is_active:
            raise _UNAUTHORIZED
        return self._public(user)

    def list_users(self) -> list[dict[str, Any]]:
        return [self._public(u) for u in self.db.list_users()]

    def delete_user(self, username: str) -> bool:
        return self.db.delete_user(username)
