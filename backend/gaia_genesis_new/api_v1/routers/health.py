from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text # Import text for executing raw SQL

from backend.database import get_db, SessionLocal # Assuming SessionLocal is available for direct use if needed
from backend.gaia_genesis_new.config import settings
from backend.gaia_genesis_new.logger import logger
import platform # For system information

router = APIRouter()

class HealthCheckResponse(schemas.BaseModel): # Assuming schemas is imported or defined elsewhere
    status: str
    database_status: str
    app_version: str = "0.1.0" # Example version, could be dynamic
    python_version: str
    platform: str
    # Potentially add more checks like Alembic revision, etc.

@router.get("/health", response_model=HealthCheckResponse) # Use your Pydantic model
def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        # Try to execute a simple query
        db.execute(text("SELECT 1"))
        logger.info("Database health check: Connection successful.")
    except Exception as e:
        db_status = "disconnected"
        logger.error(f"Database health check: Connection failed. Error: {e}")
        # Optionally, re-raise or handle more gracefully if needed,
        # but for a health check, just reporting status is often enough.

    return HealthCheckResponse(
        status="ok",
        database_status=db_status,
        # app_version=settings.APP_VERSION, # If you add APP_VERSION to your settings
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        platform=f"{platform.system()} {platform.release()}"
    )

# Need to import sys for python_version and schemas for HealthCheckResponse
import sys
from backend.gaia_genesis_new.api_v1 import schemas # Adjust import path as necessary
