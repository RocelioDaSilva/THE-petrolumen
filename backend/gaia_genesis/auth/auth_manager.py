import bcrypt, jwt, os, datetime
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..core.database_manager import DatabaseManager
from ..models import User

# Configuration from environment variables
SECRET = os.getenv("SECRET_KEY", "fallback-dev-secret")
ALGORITHM = "HS256"
EXPIRY = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480))

security = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode(
        "utf-8"
    )


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str) -> str:
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=EXPIRY
    )
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    payload = decode_token(credentials.credentials)
    db_manager = DatabaseManager.get_instance()
    user = db_manager.get_user_by_id(payload["sub"])
    if user is None:
        raise HTTPException(401, "User not found")
    return user
