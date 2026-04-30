from fastapi import APIRouter, Depends, HTTPException, Body, status
from pydantic import BaseModel, EmailStr
from ...auth.auth_manager import hash_password, verify_password, create_access_token
from ...core.database_manager import DatabaseManager

router = APIRouter()


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register(user_in: UserRegister):
    db = DatabaseManager.get_instance()
    hashed = hash_password(user_in.password)
    user = db.create_db_user(
        username=user_in.username, email=user_in.email, hashed_password=hashed
    )
    if not user:
        raise HTTPException(status_code=400, detail="User already exists")
    return {"message": "User created successfully"}


@router.post("/login")
async def login(user_in: UserLogin):
    db = DatabaseManager.get_instance()
    user = db.get_db_user_by_username(user_in.username)
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}
