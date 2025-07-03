from fastapi import FastAPI, UploadFile, File, HTTPException, Path, Depends, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Tuple, Optional
from pydantic import BaseModel, EmailStr
import logging
import os # For environment variables
from dotenv import load_dotenv # For .env file

from gaia_genesis.reservoir_engineering.data_management import DataUploader
from gaia_genesis.reservoir_engineering.database import DatabaseManager
from gaia_genesis.reservoir_engineering.api import AuthManager
import pandas as pd

# Load environment variables from .env file
load_dotenv()

# Setup logging
# LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper() # Example for log level from env
# logging.basicConfig(level=LOG_LEVEL)
logging.basicConfig(level=logging.INFO) # Keeping it simple for now
logger = logging.getLogger(__name__)


app = FastAPI(
    title="PetroLúmen Backend API",
    description="API for reservoir engineering tasks. Authentication implemented. Configuration via .env.",
    version="0.2.1" # Version updated
)

# --- Configuration from Environment Variables ---
DEFAULT_DB_URL = "sqlite:///./default_reservoir_data.db"
DEFAULT_SECRET_KEY = "a_default_super_secret_key_please_change_for_prod_if_env_is_not_set" # SENSITIVE_VALUE_DO_NOT_LOG
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)
SECRET_KEY = os.getenv("SECRET_KEY", DEFAULT_SECRET_KEY) # SENSITIVE_VALUE_DO_NOT_LOG
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES)))

if SECRET_KEY == DEFAULT_SECRET_KEY:
    logger.warning("SECURITY WARNING: Using default JWT SECRET_KEY. Set a strong SECRET_KEY in your .env file for production.")
if DATABASE_URL == DEFAULT_DB_URL:
    logger.info(f"Using default DATABASE_URL: {DEFAULT_DB_URL}. Configure DATABASE_URL in .env for other databases.")


# --- Initialize Managers with configuration ---
db_manager = DatabaseManager(db_url=DATABASE_URL)
# Ensure DB is connected and tables are created on startup
if not db_manager.connect():
    logger.critical(f"FATAL: Could not connect to the database at {DATABASE_URL} on startup. Exiting.")
    exit(1)
if not db_manager.create_tables():
    logger.warning("Could not create database tables on startup (this might be okay if they already exist or if there's a permissions issue).")

auth_manager = AuthManager(secret_key=SECRET_KEY, access_token_expire_minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
data_uploader = DataUploader(db_manager=db_manager)

# OAuth2 Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# --- Pydantic Models for API ---
class Token(BaseModel):
    access_token: str
    token_type: str

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    is_admin: bool
    disabled: bool

class WellMetadata(BaseModel): # For creating wells along with data
    field_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# --- API Helper Functions ---
def dataframe_to_json_serializable(df: pd.DataFrame | None) -> Any:
    """Converts DataFrame to JSON serializable format, handling NaNs."""
    if df is None:
        return pd.DataFrame().to_dict(orient='records') # Return empty list for None df
    return df.where(pd.notnull(df), None).to_dict(orient='records')

async def get_current_active_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Dependency to get current active user from token."""
    user = auth_manager.get_current_user_from_token(token)
    if not user: # Should be handled by get_current_user_from_token raising HTTPException
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    if user.get("disabled"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return UserResponse(**user) # Validate against Pydantic model


# --- API Endpoints ---

@app.get("/", tags=["General"])
async def root() -> Dict[str, str]:
    """Root endpoint providing a welcome message."""
    return {"message": "Welcome to the PetroLúmen Backend API. Authentication is active."}

@app.get("/health", tags=["General"])
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    # TODO: Could be expanded to check DB connection status
    return {"status": "ok"}

# --- Authentication Endpoints ---
@app.post("/api/v1/auth/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token login, get an access token for future requests."""
    user = auth_manager.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_manager.create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/v1/auth/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
async def create_new_user(user_in: UserCreate):
    """Create a new user."""
    # Check if user already exists (optional, as AuthManager handles it but good for early feedback)
    existing_user = auth_manager.get_user(user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    created_user = auth_manager.create_user(
        username=user_in.username,
        email=user_in.email,
        password=user_in.password, # AuthManager will hash it
        full_name=user_in.full_name
    )
    if "error" in created_user: # Should not happen if check above is done, but defensive
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=created_user["error"])
    return UserResponse(**created_user)


@app.get("/api/v1/users/me", response_model=UserResponse, tags=["Users"])
async def read_users_me(current_user: UserResponse = Depends(get_current_active_user)):
    """Fetch the current logged in user."""
    return current_user

# --- Well Data Management Endpoints (Now Protected) ---
@app.post("/api/v1/wells/{well_name}/data", tags=["Well Data Management"])
async def upload_well_data(
    well_name: str = Path(..., title="The name of the well", min_length=1),
    files: List[UploadFile] = File(..., description="List of CSV files to upload for the well"),
    metadata: Optional[WellMetadata] = None, # Optional metadata via query or form-data in future
    current_user: UserResponse = Depends(get_current_active_user) # Protect endpoint
) -> JSONResponse:
    """
    Uploads CSV data files for a specific well. Data is stored in the database.
    Requires authentication.
    """
    logger.info(f"User '{current_user.username}' attempting to upload data for well '{well_name}'.")
    if not files:
        raise HTTPException(status_code=400, detail="No files were provided.")

    csv_files_content: List[Tuple[str, str]] = []
    for file_upload in files: # Renamed 'file' to 'file_upload' to avoid conflict
        if file_upload.content_type != "text/csv":
            raise HTTPException(status_code=400, detail=f"File '{file_upload.filename}' is not a CSV. Found: {file_upload.content_type}")
        try:
            content_bytes = await file_upload.read()
            content_str = content_bytes.decode('utf-8')
            csv_files_content.append((file_upload.filename, content_str))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading file {file_upload.filename}: {str(e)}")
        finally:
            await file_upload.close()

    # Pass metadata to data_uploader
    field_name = metadata.field_name if metadata else None
    latitude = metadata.latitude if metadata else None
    longitude = metadata.longitude if metadata else None

    success, message, well_id = data_uploader.load_well_data(
        well_name, csv_files_content,
        field_name=field_name, latitude=latitude, longitude=longitude
    )

    if not success:
        # Consider status codes more carefully based on message
        raise HTTPException(status_code=400, detail=message)

    # Fetch a preview of the just loaded data if successful
    data_preview_df = None
    if well_id:
        # This is a bit redundant as load_well_data doesn't return the df directly anymore
        # For a true preview, we'd query. For now, this part is simplified.
        # Let's get the preview from the DB to be accurate
        temp_preview_df = data_uploader.get_data_preview(well_name, n_rows=5)
        if temp_preview_df is not None and not temp_preview_df.empty:
             data_preview_df = temp_preview_df

    return JSONResponse(content={
        "message": message,
        "well_name": well_name,
        "well_id": well_id,
        "files_processed": [f.filename for f in files],
        "data_preview_first_5_rows": dataframe_to_json_serializable(data_preview_df)
    })

@app.get("/api/v1/wells/{well_name}/preview", tags=["Well Data Management"])
async def get_well_data_preview(
    well_name: str = Path(..., title="The name of the well", min_length=1),
    n_rows: int = 5,
    current_user: UserResponse = Depends(get_current_active_user) # Protect endpoint
) -> JSONResponse:
    """Retrieves a preview (first N rows) of the data for a specific well from the database."""
    logger.info(f"User '{current_user.username}' requesting preview for well '{well_name}'.")
    preview_df = data_uploader.get_data_preview(well_name, n_rows)
    if preview_df is None: # Well not found
        raise HTTPException(status_code=404, detail=f"Well '{well_name}' not found.")
    if preview_df.empty and data_uploader.db_manager.get_well_by_name(well_name) is not None: # Well exists but no data
        pass # Return empty preview is fine

    return JSONResponse(content={
        "well_name": well_name,
        "preview": dataframe_to_json_serializable(preview_df)
    })

@app.get("/api/v1/wells/{well_name}/statistics", tags=["Well Data Management"])
async def get_well_data_statistics(
    well_name: str = Path(..., title="The name of the well", min_length=1),
    current_user: UserResponse = Depends(get_current_active_user) # Protect endpoint
) -> JSONResponse:
    """Retrieves descriptive statistics for the data of a specific well from the database."""
    logger.info(f"User '{current_user.username}' requesting statistics for well '{well_name}'.")
    stats = data_uploader.get_well_statistics(well_name)
    if stats is None: # Well not found
        raise HTTPException(status_code=404, detail=f"Well '{well_name}' not found.")
    # If stats exist but show 0 rows (well exists, no data), it's still a valid response
    return JSONResponse(content={
        "well_name": well_name,
        "statistics": stats
    })

@app.get("/api/v1/wells", tags=["Well Data Management"])
async def list_wells_with_data(
    current_user: UserResponse = Depends(get_current_active_user) # Protect endpoint
) -> JSONResponse:
    """Lists all wells from the database."""
    logger.info(f"User '{current_user.username}' listing all wells.")
    wells = data_uploader.list_loaded_wells() # This now returns list of dicts from DB
    return JSONResponse(content={"wells": wells})


# Admin endpoint - example of role-based access (conceptual, AuthManager doesn't enforce roles yet on this endpoint)
@app.delete("/api/v1/admin/wells/{well_name}", tags=["Admin"])
async def admin_delete_well(
    well_name: str = Path(..., title="The name of the well to delete"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """ ADMIN Endpoint: Deletes a well and its associated data. Requires admin privileges (conceptual)."""
    logger.info(f"User '{current_user.username}' attempting to delete well '{well_name}'.")
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted: Requires admin privileges.")

    well = data_uploader.db_manager.get_well_by_name(well_name)
    if not well:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Well '{well_name}' not found.")

    session = data_uploader.db_manager.get_session()
    try:
        # SQLAlchemy's cascade delete should handle ProductionData due to relationship config
        session.delete(well)
        session.commit()
        logger.info(f"Admin user '{current_user.username}' successfully deleted well '{well_name}' (ID: {well.id}).")
        return JSONResponse(content={"message": f"Well '{well_name}' and its data deleted successfully."})
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting well '{well_name}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not delete well '{well_name}'.")
    finally:
        session.close()

# Removed /api/v1/admin/clear_all_well_data as deleting all data from a real DB is too destructive for a generic endpoint.
# Specific deletion logic (like per-well above) is preferred.

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server for development...")
    # Create a default admin user for testing if not exists
    # This is for dev convenience; in prod, user creation would be more controlled.
    try:
        admin_user = auth_manager.get_user("admin")
        if not admin_user:
            auth_manager.create_user("admin", "admin@example.com", "adminpassword", is_admin=True, full_name="Admin User")
            logger.info("Created default admin user (admin/adminpassword) for development.")
        else:
            logger.info("Default admin user 'admin' already exists.")
    except Exception as e:
        logger.error(f"Could not create default admin user: {e}")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
