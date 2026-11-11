from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from .auth import AuthManager
from .database import DatabaseManager
from .dependencies import get_auth_manager, get_current_user, get_database_manager
from .schemas import (
    SavedSimulationCreate,
    SavedSimulationOut,
    SavedSimulationSummary,
    Token,
    UserCreate,
    UserLogin,
    UserOut,
)

router = APIRouter(tags=["Persistence"])


@router.post(
    "/auth/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    payload: UserCreate,
    auth: AuthManager = Depends(get_auth_manager),
) -> UserOut:
    user = auth.register(
        username=payload.username,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role="user",
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already registered.",
        )
    return UserOut(**user)


@router.post("/auth/token", response_model=Token)
def issue_token(
    payload: UserLogin,
    auth: AuthManager = Depends(get_auth_manager),
) -> Token:
    user = auth.authenticate(payload.username, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(
        access_token=auth.issue_token(payload.username),
    )


@router.get("/auth/me", response_model=UserOut)
def read_current_user(
    user: dict[str, Any] = Depends(get_current_user),
) -> UserOut:
    return UserOut(**user)


@router.post(
    "/saved-simulations",
    response_model=SavedSimulationOut,
    status_code=status.HTTP_201_CREATED,
)
def save_simulation(
    payload: SavedSimulationCreate,
    user: dict[str, Any] = Depends(get_current_user),
    database: DatabaseManager = Depends(get_database_manager),
) -> SavedSimulationOut:
    _ensure_json_safe(payload.input_data, "input_data")
    _ensure_json_safe(payload.result_data, "result_data")
    saved = database.save_simulation(
        owner_id=user["id"],
        name=payload.name,
        simulation_type=payload.simulation_type,
        input_data=payload.input_data,
        result_data=payload.result_data,
    )
    return SavedSimulationOut(**saved)


@router.get("/saved-simulations", response_model=list[SavedSimulationSummary])
def list_saved_simulations(
    user: dict[str, Any] = Depends(get_current_user),
    database: DatabaseManager = Depends(get_database_manager),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[SavedSimulationSummary]:
    records = database.list_saved_simulations(
        owner_id=user["id"], limit=limit, offset=offset
    )
    return [SavedSimulationSummary(**record) for record in records]


@router.get(
    "/saved-simulations/{simulation_id}",
    response_model=SavedSimulationOut,
)
def get_saved_simulation(
    simulation_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    database: DatabaseManager = Depends(get_database_manager),
) -> SavedSimulationOut:
    record = database.get_saved_simulation(simulation_id, owner_id=user["id"])
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved simulation not found.",
        )
    return SavedSimulationOut(**record)


@router.delete(
    "/saved-simulations/{simulation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_saved_simulation(
    simulation_id: int,
    user: dict[str, Any] = Depends(get_current_user),
    database: DatabaseManager = Depends(get_database_manager),
) -> Response:
    if not database.delete_saved_simulation(simulation_id, owner_id=user["id"]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved simulation not found.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _ensure_json_safe(value: dict[str, Any], field: str) -> None:
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field} must contain finite JSON values.",
        ) from error
