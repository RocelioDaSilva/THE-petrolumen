from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr
import logging
import uuid

# This will be initialized in main.py
auth_manager = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserResponse(UserBase):
    id: uuid.UUID
    role: str
    is_active: bool

async def get_current_active_user(
    token: str = Depends(oauth2_scheme),
) -> Dict[str, Any]:
    """Dependency to get current active user from token."""
    if auth_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service not initialized",
        )

    user = auth_manager.get_current_user_from_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    return UserResponse(**user)

async def get_current_active_admin_user(
    current_user: UserResponse = Depends(get_current_active_user),
) -> UserResponse:
    """Dependency to ensure the current user is an admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted: Requires admin privileges.",
        )
    return current_user
