"""Pydantic request/response models for the auth endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(
        ...,
        min_length=5,
        max_length=120,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = None


class UserLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


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


class SavedSimulationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=120)
    simulation_type: str = Field(..., min_length=1, max_length=80)
    input_data: dict[str, Any]
    result_data: dict[str, Any]


class SavedSimulationSummary(BaseModel):
    id: int
    name: str
    simulation_type: str
    created_at: datetime


class SavedSimulationOut(SavedSimulationSummary):
    input_data: dict[str, Any]
    result_data: dict[str, Any]
