"""Pydantic request/response models for the auth endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = None
    role: str = "user"


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: str | None = None
    role: str
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
