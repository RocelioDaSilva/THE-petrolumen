from __future__ import annotations

import logging
from threading import Lock
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import SQLAlchemyError

from .auth import AuthManager
from .database import DatabaseManager
from .settings import get_settings

logger = logging.getLogger(__name__)
_database_initialization_lock = Lock()
_bearer_scheme = HTTPBearer(auto_error=False)


def get_database_manager(request: Request) -> DatabaseManager:
    manager = getattr(request.app.state, "database_manager", None)
    if manager is not None:
        return manager

    with _database_initialization_lock:
        manager = getattr(request.app.state, "database_manager", None)
        if manager is not None:
            return manager

        settings = get_settings()
        manager = DatabaseManager(settings.database_url)
        if not manager.connect():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Persistence database is unavailable.",
            )
        try:
            manager.create_all()
        except SQLAlchemyError:
            manager.close()
            logger.exception("Could not initialize the persistence database.")
            raise

        request.app.state.database_manager = manager
        return manager


def get_auth_manager(
    database: DatabaseManager = Depends(get_database_manager),
) -> AuthManager:
    settings = get_settings()
    if not settings.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Authentication is unavailable; configure "
                "PETROLUMEN_SECRET_KEY with at least 32 characters."
            ),
        )
    if settings.access_token_expire_minutes <= 0:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PETROLUMEN_ACCESS_TOKEN_EXPIRE_MINUTES must be positive.",
        )
    return AuthManager(
        database,
        settings.secret_key,
        settings.access_token_expire_minutes,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    auth: AuthManager = Depends(get_auth_manager),
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth.get_current_user(credentials.credentials)
