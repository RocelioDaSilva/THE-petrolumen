from fastapi import FastAPI, UploadFile, File, HTTPException, Path, Depends, status, Body
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Tuple, Optional
from pydantic import BaseModel, EmailStr
import logging
import os # For environment variables
from dotenv import load_dotenv # For .env file

# Updated imports to point to the new 'core' modules for data/auth management
# and directly to reservoir_engineering.py for tools.
from backend.gaia_genesis.core.data_uploader import DataUploader
from backend.gaia_genesis.core.database_manager import DatabaseManager
from backend.gaia_genesis.core.auth_manager import AuthManager
# Assuming these classes are directly available in the top-level reservoir_engineering.py now
from backend.gaia_genesis.reservoir_engineering import (
    AdvancedDeclineAnalysis,
    # ReservoirSimulator, # This class might have more complex dependencies not yet resolved
    PVTProperties # PVTProperties is in reservoir_engineering.py
)
# For ReservoirSimulator and AIPrediction, need to confirm their new locations or if they are self-contained
# For now, let's assume they might be in their own files at the top level of gaia_genesis
from backend.gaia_genesis.flow_simulation import FlowSimulation as ReservoirSimulator # Class is FlowSimulation, alias for minimal changes
# from backend.gaia_genesis.prediction import AIPrediction # AIPrediction class is in a subdirectory not copied. Commenting out.


import pandas as pd
import numpy as np # Added import

# Load environment variables from .env file
# This should be one of the first things to ensure .env is loaded before settings are initialized
load_dotenv()

from .config import settings # Import the settings instance

# Setup logging using LOG_LEVEL from settings
# Note: basicConfig should only be called once. If other modules also call it, it might not reconfigure.
# It's better to configure logging based on settings early.
logging.basicConfig(level=settings.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.APP_NAME,
    description="API for reservoir engineering tasks. Authentication implemented. Configuration via Pydantic BaseSettings.",
    version=settings.APP_VERSION
)

# --- Configuration now comes from settings object ---
# The old os.getenv calls and default value definitions are removed.
# Warnings for default keys can be handled by checking settings.SECRET_KEY against a known insecure default,
# or by simply ensuring a strong default in config.py and requiring .env override for production.
if settings.SECRET_KEY == "a_very_secret_key_that_must_be_changed_in_production_and_is_very_long_and_random_123!@#": # Check against the default in config.py
    logger.warning("SECURITY WARNING: Using default JWT SECRET_KEY. Set a strong SECRET_KEY in your .env file or environment for production.")
if settings.DATABASE_URL == "sqlite:///./default_app_data.db": # Check against the default in config.py
    logger.info(f"Using default DATABASE_URL: {settings.DATABASE_URL}. Configure DATABASE_URL for other databases.")


# --- Initialize Managers with configuration from settings ---
db_manager = DatabaseManager(db_url=settings.DATABASE_URL)
# Ensure DB is connected and tables are created on startup
if not db_manager.connect():
    logger.critical(f"FATAL: Could not connect to the database at {settings.DATABASE_URL} on startup. Exiting.")
    exit(1)
if not db_manager.create_tables(): # This will now also create the User table
    logger.warning("Could not create database tables on startup (this might be okay if they already exist or if there's a permissions issue).")

auth_manager = AuthManager(
    db_manager=db_manager,
    secret_key=settings.SECRET_KEY,
    access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    # JWT_ALGORITHM is used internally by AuthManager, ensure it matches settings.JWT_ALGORITHM if AuthManager is modified to take it.
    # For now, AuthManager has its own JWT_ALGORITHM constant. This could be synced.
)
data_uploader = DataUploader(db_manager=db_manager)

# OAuth2 Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# --- Initialize Reservoir Engineering Tools ---
dca_analyzer = AdvancedDeclineAnalysis()
# The FlowSimulation class from backend/gaia_genesis/flow_simulation.py expects arguments like nx, ny, nz for its constructor.
# The original instantiation `ReservoirSimulator()` suggests it had a default constructor or was a different class.
# For now, to prevent startup error, we will initialize it with some default grid,
# but this will need proper configuration later.
try:
    res_simulator = ReservoirSimulator(nx=10, ny=10, nz=1, dx=100, dy=100, dz=10) # Example default values
    logger.info("Initialized ReservoirSimulator (FlowSimulation) with default parameters.")
except Exception as e:
    logger.error(f"Failed to initialize ReservoirSimulator (FlowSimulation): {e}. Simulation endpoints may not work.")
    res_simulator = None # Set to None if initialization fails

# ai_predictor = AIPrediction() # Commented out as AIPrediction class is not available
ai_predictor = None # Set to None
logger.warning("AIPrediction functionality is disabled as the class could not be imported due to missing subdirectories.")

# Use AI_MODELS_DIR from settings
os.makedirs(settings.AI_MODELS_DIR, exist_ok=True)

# --- Import Custom Routers ---
# Import for PVT calculations from gaia_genesis
try:
    from backend.gaia_genesis.api_v1.endpoints import pvt_calculations as gaia_pvt_router
    app.include_router(gaia_pvt_router.router, prefix="/api/v1/gaia/pvt", tags=["Gaia - PVT Calculations"])
    logger.info("Successfully included Gaia PVT calculations router.")
except ImportError as e:
    logger.error(f"Could not import Gaia PVT calculations router: {e}. Ensure 'backend.gaia_genesis.api_v1.endpoints.pvt_calculations' is correct and discoverable.")
except Exception as e:
    logger.error(f"An unexpected error occurred while including Gaia PVT router: {e}")


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
    role: Optional[str] = "user" # Default role on creation

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    # is_admin: bool # Deprecated, use role
    # disabled: bool # Deprecated, use is_active

class WellMetadata(BaseModel): # For creating wells along with data
    field_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

# --- Decline Curve Analysis Models ---
class DCARequestData(BaseModel):
    time: List[float] # In months or days, consistent units
    rate: List[float] # Production rates corresponding to time data

class DCAParams(BaseModel):
    qi: float
    Di: float
    b: Optional[float] = None # For hyperbolic
    type: str

class DCAResponse(BaseModel):
    fitted_models: Dict[str, DCAParams]
    best_model: Optional[str] = None
    error: Optional[str] = None

class DCAPredictionRequest(BaseModel):
    model_name: str # Which model to use for prediction if not best_model
    months_to_predict: int
    # Optionally include parameters if not relying on previously fitted ones stored in an instance
    # params: Optional[DCAParams] = None

class DCAPredictionResponse(BaseModel):
    time_months: List[float]
    predicted_rate: List[float]
    model_used: str

# --- Flow Simulation Models ---
class SimGridRequest(BaseModel):
    nx: int
    dx: float
    area: float = 100.0

class SimFluidPropsRequest(BaseModel):
    viscosity: float
    compressibility: float
    fvf: float # Formation Volume Factor

class SimRockPropsRequest(BaseModel):
    # Allow either a single value for homogeneous or a list for heterogeneous
    permeability: Any # float or List[float]
    porosity: Any   # float or List[float]

class SimInitialConditionsRequest(BaseModel):
    initial_pressure: Any # float or List[float]

class SimBoundaryConditionsRequest(BaseModel):
    type_left: str # 'pressure' or 'flux'
    value_left: float
    type_right: str # 'pressure' or 'flux'
    value_right: float

class SimWellRequest(BaseModel):
    name: str
    location_index: int # 0-based index
    well_type: str = "producer" # "producer" or "injector"
    control_type: str = "bhp"   # "bhp" or "rate"
    control_value: float        # BHP value or rate value (STB/day, negative for producer)
    rw: float = 0.25            # wellbore radius in ft
    skin: float = 0.0           # skin factor

class SimRunParamsRequest(BaseModel):
    end_time: float # days
    dt: float       # days, time step size

class SimPressureResponse(BaseModel):
    time_steps: List[float]
    pressure_at_block: Dict[int, List[float]] # Key is block index
    status: str

class SimWellRateResponse(BaseModel):
    time_steps: List[float]
    rates: Dict[str, List[float]] # Key is well name
    status: str

# --- AI Prediction Models ---
class AIPredictionDataRequest(BaseModel):
    # Using a list of dicts for flexibility, similar to how DataFrames are often sent via JSON
    # Each dict is a record/row.
    records: List[Dict[str, Any]]
    target_column: str
    feature_columns: List[str]
    # model_type: Optional[str] = "linear_regression" # Could be used to select specific model type to train/use

class AITrainResponse(BaseModel):
    message: str
    trained_models: List[str] # List of names of models trained
    # Could include performance metrics here for each model if desired
    # performance: Optional[Dict[str, Dict[str, float]]] = None
    error: Optional[str] = None

class AIPredictRequest(BaseModel):
    records: List[Dict[str, Any]] # Data to make predictions on (only features needed)
    feature_columns: List[str] # To ensure correct feature order/selection
    # model_name: Optional[str] = None # If specific model prediction is desired

class AIPredictResponse(BaseModel):
    predictions: Dict[str, List[float]] # Key: model_name, Value: list of predictions
    error: Optional[str] = None

class AISaveModelRequest(BaseModel):
    model_name: str
    path: str # Path where model should be saved on server

class AILoadModelRequest(BaseModel):
    model_name: str # Name to assign to loaded model
    path: str # Path from where model should be loaded on server


# --- API Helper Functions ---
def dataframe_to_json_serializable(df: pd.DataFrame | None) -> Any:
    """Converts DataFrame to JSON serializable format, handling NaNs."""
    if df is None:
        return pd.DataFrame().to_dict(orient='records') # Return empty list for None df
    return df.where(pd.notnull(df), None).to_dict(orient='records')

async def get_current_active_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Dependency to get current active user from token."""
    user = auth_manager.get_current_user_from_token(token)
    # get_current_user_from_token already raises HTTPException for invalid/expired tokens or inactive users
    if not user:
        # This case should ideally not be reached if get_current_user_from_token is robust
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials (unexpected)")
    return UserResponse(**user) # Validate against Pydantic model

async def get_current_active_admin_user(current_user: UserResponse = Depends(get_current_active_user)) -> UserResponse:
    """Dependency to ensure the current user is an admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted: Requires admin privileges."
        )
    return current_user


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

# User creation is now an admin-only operation.
# Public user registration would require a different endpoint without admin dependency.
@app.post("/api/v1/admin/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Admin", "Users"])
async def admin_create_new_user(user_in: UserCreate, current_admin_user: UserResponse = Depends(get_current_active_admin_user) ):
    """
    ADMIN Endpoint: Create a new user.
    Allows specifying username, email, password, full_name, and role.
    """
    logger.info(f"Admin user '{current_admin_user.username}' attempting to create new user '{user_in.username}'.")
    # AuthManager.create_user handles hashing password and DB interaction.
    # It also checks for duplicate username/email and returns None if creation fails.
    created_user_dict = auth_manager.create_user(
        username=user_in.username,
        email=user_in.email,
        password=user_in.password,
        full_name=user_in.full_name,
        role=user_in.role
    )
    if not created_user_dict:
        # This could be due to duplicate username/email, or other DB errors.
        # AuthManager logs specifics. We return a generic error here.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not create user '{user_in.username}'. Username or email might already exist, or data is invalid."
        )
    return UserResponse(**created_user_dict)


@app.get("/api/v1/users/me", response_model=UserResponse, tags=["Users"])
async def read_users_me(current_user: UserResponse = Depends(get_current_active_user)):
    """Fetch the current logged in user's details."""
    return current_user

# --- Admin User Management Endpoints ---
@app.get("/api/v1/admin/users", response_model=List[UserResponse], tags=["Admin", "Users"], dependencies=[Depends(get_current_active_admin_user)])
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: UserResponse = Depends(get_current_active_admin_user) # Dependency for logging/audit if needed beyond auth
):
    """ADMIN Endpoint: List all users with pagination."""
    logger.info(f"Admin user '{admin_user.username}' listing all users (skip={skip}, limit={limit}).")
    users = auth_manager.get_all_users(skip=skip, limit=limit)
    return [UserResponse(**user) for user in users]

@app.get("/api/v1/admin/users/{username}", response_model=UserResponse, tags=["Admin", "Users"])
async def get_user_by_admin(
    username: str = Path(..., title="The username of the user to retrieve"),
    admin_user: UserResponse = Depends(get_current_active_admin_user)
):
    """ADMIN Endpoint: Get a specific user's details by username."""
    logger.info(f"Admin user '{admin_user.username}' retrieving details for user '{username}'.")
    user = auth_manager.get_user_details(username) # Uses the new method in AuthManager
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{username}' not found.")
    return UserResponse(**user)

@app.put("/api/v1/admin/users/{username}", response_model=UserResponse, tags=["Admin", "Users"])
async def update_user_by_admin(
    username: str = Path(..., title="The username of the user to update"),
    user_update_data: UserUpdate = Body(...), # FastAPI uses Body for PUT request data
    admin_user: UserResponse = Depends(get_current_active_admin_user)
):
    """
    ADMIN Endpoint: Update a user's details (email, full_name, role, is_active).
    Password changes are not supported via this endpoint.
    """
    logger.info(f"Admin user '{admin_user.username}' attempting to update user '{username}'.")

    # Convert Pydantic model to dict, excluding unset values to avoid overwriting with None
    update_data_dict = user_update_data.model_dump(exclude_unset=True)

    if not update_data_dict:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")

    try:
        updated_user = auth_manager.update_user_details(username, update_data_dict)
    except ValueError as e: # Catch specific error for password update attempts from AuthManager
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not updated_user:
        # This could be because user not found, or DB update failed for other reasons.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{username}' not found or update failed.")
    return UserResponse(**updated_user)


@app.delete("/api/v1/admin/users/{username}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin", "Users"])
async def delete_user_by_admin(
    username: str = Path(..., title="The username of the user to delete"),
    admin_user: UserResponse = Depends(get_current_active_admin_user)
):
    """ADMIN Endpoint: Delete a user by username."""
    logger.info(f"Admin user '{admin_user.username}' attempting to delete user '{username}'.")
    if username == admin_user.username: # Prevent admin from deleting themselves
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin users cannot delete themselves.")

    if not auth_manager.delete_user(username):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{username}' not found or could not be deleted.")
    # No content returned for 204
    return None


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
@app.delete("/api/v1/admin/wells/{well_name}", tags=["Admin", "Well Data Management"])
async def admin_delete_well(
    well_name: str = Path(..., title="The name of the well to delete"),
    admin_user: UserResponse = Depends(get_current_active_admin_user) # Use admin dependency
):
    """ ADMIN Endpoint: Deletes a well and its associated data. Requires admin privileges."""
    logger.info(f"Admin user '{admin_user.username}' attempting to delete well '{well_name}'.")
    # The get_current_active_admin_user dependency already ensures the user is an admin.

    well = data_uploader.db_manager.get_well_by_name(well_name)
    if not well:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Well '{well_name}' not found.")

    session = data_uploader.db_manager.get_session()
    try:
        # SQLAlchemy's cascade delete should handle ProductionData due to relationship config
        session.delete(well)
        session.commit()
        logger.info(f"Admin user '{admin_user.username}' successfully deleted well '{well_name}' (ID: {well.id}).") # Corrected here
        return JSONResponse(content={"message": f"Well '{well_name}' and its data deleted successfully."})
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting well '{well_name}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not delete well '{well_name}'.")
    finally:
        session.close()

# Removed /api/v1/admin/clear_all_well_data as deleting all data from a real DB is too destructive for a generic endpoint.
# Specific deletion logic (like per-well above) is preferred.

# --- Decline Curve Analysis Endpoints ---
@app.post("/api/v1/reservoir/dca/fit", response_model=DCAResponse, tags=["Reservoir Engineering"])
async def fit_decline_models(
    data: DCARequestData,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Fits decline curve models (Exponential, Hyperbolic, Harmonic) to provided time and rate data.
    """
    try:
        time_array = np.array(data.time)
        rate_array = np.array(data.rate)

        # Use a new dca_analyzer instance per request or manage state carefully if global
        dca_instance = AdvancedDeclineAnalysis()
        fitted_models_info = dca_instance.fit_models(time_array, rate_array)

        if "error" in fitted_models_info:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=fitted_models_info["error"])

        # Convert output params to fit DCAParams model
        response_models = {}
        for name, params_dict in dca_instance.models.items():
            response_models[name] = DCAParams(**params_dict)

        return DCAResponse(fitted_models=response_models, best_model=dca_instance.best_model_name)
    except ValueError as ve:
        logger.error(f"ValueError in DCA fit: {ve}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Unexpected error in DCA fit endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during DCA model fitting.")

# Note: For prediction, the current AdvancedDeclineAnalysis class stores state (fitted models).
# This is suitable if the dca_analyzer instance is per-request or per-user-session.
# If dca_analyzer is global, it's not thread-safe for concurrent users fitting different data.
# For this iteration, we'll assume a new instance is used or state is managed appropriately.
# A stateless approach would require passing model parameters for prediction.

@app.post("/api/v1/reservoir/dca/predict", response_model=DCAPredictionResponse, tags=["Reservoir Engineering"])
async def predict_decline(
    request: DCAPredictionRequest, # This would need to include model params if dca_analyzer is stateless
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Predicts future production rates using a previously fitted model (stateful for now).
    This endpoint expects that `fit_decline_models` was called on the same `dca_analyzer` instance.
    A better stateless design would take model parameters as input.
    """
    # This uses the global dca_analyzer. This is NOT thread-safe for concurrent users if state is involved.
    # For a démo, this might be fine, but for production, this state needs to be managed (e.g., per user session, or pass params)
    if not dca_analyzer.best_model_name or request.model_name not in dca_analyzer.params:
         # Try to use best_model if model_name is not specified or invalid, or if a specific one is requested.
        if not dca_analyzer.best_model_name and request.model_name not in dca_analyzer.params:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Model '{request.model_name}' not fitted or no best model available. Fit models first.")
        # If a specific model is requested and not found, but a best model exists, we could opt to use best_model.
        # For now, require the requested model to be explicitly available or rely on previously set best_model.
        # This part of logic needs refinement for a robust API.
        # Let's assume for now we use the `request.model_name` if provided and valid, else best_model.

    # Temporary simplified logic: Use the best_model_name from the global instance if request.model_name is not set or invalid
    # This is problematic because dca_analyzer is global.
    # A better approach: the client sends the model parameters it wants to use for prediction.
    # Or, the fit endpoint returns a session ID/model ID that predict can use.
    # For now, let's make a new instance and assume params are somehow passed (not implemented in this version)
    # This endpoint is more of a placeholder for how one might structure it.

    # Re-fitting on dummy data just to use the predict_future structure (BAD for real use)
    # This highlights the stateful issue with the current dca_analyzer.
    # To make this work without major refactor of dca_analyzer for statelessness:
    # We'd need to ensure dca_analyzer has been fitted appropriately before this call.
    # This is not ideal for a public API.

    # Let's assume the global dca_analyzer has been fitted by a previous call to /fit
    # And we want to predict using a specific model from that fit or the best one.

    original_best_model = dca_analyzer.best_model_name
    if request.model_name and request.model_name in dca_analyzer.params:
        dca_analyzer.best_model_name = request.model_name # Temporarily set for prediction
    elif not dca_analyzer.best_model_name: # No model specified and no best model from previous fit
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No model available for prediction. Fit models first.")

    try:
        predictions_df = dca_analyzer.predict_future(request.months_to_predict)
        dca_analyzer.best_model_name = original_best_model # Reset if changed

        if predictions_df.empty:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Prediction resulted in empty data. Check model parameters or input.")

        return DCAPredictionResponse(
            time_months=predictions_df['Time_Months'].tolist(),
            predicted_rate=predictions_df['Predicted_Rate'].tolist(),
            model_used=dca_analyzer.best_model_name # This will be the model used for prediction
        )
    except Exception as e:
        dca_analyzer.best_model_name = original_best_model # Reset if changed
        logger.exception(f"Error during DCA prediction: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error during prediction: {str(e)}")

# --- Flow Simulation Endpoints ---
# For flow simulation, the global `res_simulator` instance will store state.
# This is NOT thread-safe for concurrent users modifying the same simulation setup.
# In a real app, simulation state would need to be managed per user/session or per simulation ID.

@app.post("/api/v1/reservoir/flowsim/setup/grid", tags=["Reservoir Engineering"])
async def setup_simulation_grid(grid_data: SimGridRequest, current_user: UserResponse = Depends(get_current_active_user)):
    try:
        res_simulator.setup_1d_grid(grid_data.nx, grid_data.dx, grid_data.area)
        return {"message": f"1D grid setup: nx={grid_data.nx}, dx={grid_data.dx}, area={grid_data.area}"}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

@app.post("/api/v1/reservoir/flowsim/setup/fluid", tags=["Reservoir Engineering"])
async def setup_simulation_fluid_properties(props: SimFluidPropsRequest, current_user: UserResponse = Depends(get_current_active_user)):
    res_simulator.set_fluid_properties(props.viscosity, props.compressibility, props.fvf)
    return {"message": "Fluid properties set."}

@app.post("/api/v1/reservoir/flowsim/setup/rock", tags=["Reservoir Engineering"])
async def setup_simulation_rock_properties(props: SimRockPropsRequest, current_user: UserResponse = Depends(get_current_active_user)):
    try:
        res_simulator.set_rock_properties(props.permeability, props.porosity)
        return {"message": "Rock properties set."}
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@app.post("/api/v1/reservoir/flowsim/setup/initial", tags=["Reservoir Engineering"])
async def setup_simulation_initial_conditions(cond: SimInitialConditionsRequest, current_user: UserResponse = Depends(get_current_active_user)):
    try:
        res_simulator.set_initial_conditions(cond.initial_pressure)
        return {"message": "Initial conditions set."}
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@app.post("/api/v1/reservoir/flowsim/setup/boundary", tags=["Reservoir Engineering"])
async def setup_simulation_boundary_conditions(bc: SimBoundaryConditionsRequest, current_user: UserResponse = Depends(get_current_active_user)):
    try:
        res_simulator.set_boundary_conditions(bc.type_left, bc.value_left, bc.type_right, bc.value_right)
        return {"message": "Boundary conditions set."}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

@app.post("/api/v1/reservoir/flowsim/setup/well", tags=["Reservoir Engineering"])
async def add_simulation_well(well_data: SimWellRequest, current_user: UserResponse = Depends(get_current_active_user)):
    try:
        res_simulator.add_well(
            name=well_data.name, location_index=well_data.location_index, well_type=well_data.well_type,
            control_type=well_data.control_type, control_value=well_data.control_value,
            rw=well_data.rw, skin=well_data.skin
        )
        return {"message": f"Well '{well_data.name}' added."}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

@app.post("/api/v1/reservoir/flowsim/run", response_model=SimPressureResponse, tags=["Reservoir Engineering"]) # Simplified response for now
async def run_flow_simulation(params: SimRunParamsRequest, current_user: UserResponse = Depends(get_current_active_user)):
    """
    Runs the 1D flow simulation with the current setup.
    WARNING: Uses a global simulator instance; not suitable for concurrent users without state management.
    """
    try:
        res_simulator.run_simulation(params.end_time, params.dt)
        if res_simulator.simulation_results.get("status") == "Failed: Singular matrix":
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Simulation failed due to singular matrix. Check parameters or boundary conditions.")

        # For simplicity, just return pressures for the first block or a summary
        # A full pressure field response could be very large.
        pressures = res_simulator.simulation_results.get('pressures_vs_time', [])
        block0_pressures = [p[0] for p in pressures if len(p) > 0] if pressures else []

        return SimPressureResponse(
            time_steps=res_simulator.simulation_results.get('time_array', np.array([])).tolist(),
            pressure_at_block={0: block0_pressures}, # Example: pressure for block 0
            status=res_simulator.simulation_results.get("status", "Unknown")
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Error during flow simulation run: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error during simulation: {str(e)}")

@app.get("/api/v1/reservoir/flowsim/results/well_rates", response_model=SimWellRateResponse, tags=["Reservoir Engineering"])
async def get_simulation_well_rates(current_user: UserResponse = Depends(get_current_active_user)):
    if not res_simulator.simulation_results or res_simulator.simulation_results.get("status") != "Completed":
        raise HTTPException(status_code=400, detail="Simulation not run or not completed successfully.")
    return SimWellRateResponse(
        time_steps=res_simulator.simulation_results.get('time_array', np.array([])).tolist(),
        rates=res_simulator.simulation_results.get('well_rates_vs_time', {}),
        status=res_simulator.simulation_results.get("status")
    )

# --- AI Prediction Endpoints ---
# Also uses a global instance `ai_predictor`, subject to same concurrency/state issues as simulator.

# @app.post("/api/v1/reservoir/prediction/train", response_model=AITrainResponse, tags=["Reservoir Engineering"])
# async def train_ai_models(
#     request: AIPredictionDataRequest,
#     current_user: UserResponse = Depends(get_current_active_user)
# ):
#     if ai_predictor is None:
#         raise HTTPException(status_code=503, detail="AIPrediction service is not available.")
#     try:
#         df = pd.DataFrame(request.records)
#         if df.empty:
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No records provided for training.")

#         X_train, X_test, y_train, y_test = ai_predictor.prepare_data(
#             df, request.target_column, request.feature_columns
#         )
#         trained_models = ai_predictor.train_models(X_train, y_train)
#         if not trained_models:
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Model training failed or no models were trained.")

#         return AITrainResponse(
#             message="Models trained successfully.",
#             trained_models=list(trained_models.keys()),
#         )
#     except ValueError as ve:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
#     except Exception as e:
#         logger.exception(f"Error during AI model training: {e}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error during AI training: {str(e)}")

# @app.post("/api/v1/reservoir/prediction/predict", response_model=AIPredictResponse, tags=["Reservoir Engineering"])
# async def predict_with_ai_models(
#     request: AIPredictRequest,
#     current_user: UserResponse = Depends(get_current_active_user)
# ):
#     if ai_predictor is None:
#         raise HTTPException(status_code=503, detail="AIPrediction service is not available.")
#     try:
#         df_features = pd.DataFrame(request.records)
#         if df_features.empty:
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No records provided for prediction.")

#         if not ai_predictor.trained_models:
#              raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No models available. Train models first.")

#         predictions = ai_predictor.predict(df_features[request.feature_columns])
#         serializable_predictions = {name: p.tolist() for name, p in predictions.items()}
#         return AIPredictResponse(predictions=serializable_predictions)
#     except ValueError as ve:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
#     except Exception as e:
#         logger.exception(f"Error during AI prediction: {e}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error during AI prediction: {str(e)}")

# @app.post("/api/v1/reservoir/prediction/save_model", tags=["Reservoir Engineering"])
# async def save_ai_model(
#     request: AISaveModelRequest,
#     current_user: UserResponse = Depends(get_current_active_user)
# ):
#     if ai_predictor is None:
#         raise HTTPException(status_code=503, detail="AIPrediction service is not available.")
#     model_filename = f"{request.model_name.replace(' ', '_')}_model.joblib"
#     # Corrected to use settings.AI_MODELS_DIR
#     full_path = os.path.join(settings.AI_MODELS_DIR, request.path, model_filename)

#     if ".." in request.path or request.path.startswith("/"):
#         raise HTTPException(status_code=400, detail="Invalid path specified.")

#     os.makedirs(os.path.join(settings.AI_MODELS_DIR, request.path), exist_ok=True)

#     result_message = ai_predictor.save_model(request.model_name, full_path)
#     if "Error" in result_message:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result_message)
#     return {"message": result_message, "saved_path": full_path}

# @app.post("/api/v1/reservoir/prediction/load_model", tags=["Reservoir Engineering"])
# async def load_ai_model(
#     request: AILoadModelRequest,
#     current_user: UserResponse = Depends(get_current_active_user)
# ):
#     if ai_predictor is None:
#         raise HTTPException(status_code=503, detail="AIPrediction service is not available.")
#     # Corrected to use settings.AI_MODELS_DIR
#     full_path = os.path.join(settings.AI_MODELS_DIR, request.path)

#     if ".." in request.path or not request.path.endswith(".joblib"):
#         raise HTTPException(status_code=400, detail="Invalid path or file type specified.")

#     success = ai_predictor.load_model(request.model_name, full_path)
#     if not success:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Failed to load model '{request.model_name}' from {full_path}. File not found or error during loading.")
#     return {"message": f"Model '{request.model_name}' loaded successfully from {request.path}."}


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server for development...")
    # Create a default admin user for testing if not exists
    # This is for dev convenience; in prod, user creation would be more controlled.
    try:
        # Use AuthManager's get_user_by_username which queries the DB
        admin_user_obj = auth_manager.get_user_by_username("admin")
        if not admin_user_obj:
            # Use AuthManager's create_user method which handles DB interaction and hashing
            auth_manager.create_user(
                username="admin",
                email="admin@example.com",
                password="adminpassword",
                role="admin", # Set role to admin
                full_name="Admin User"
            )
            logger.info("Created default admin user (admin/adminpassword) for development.")
        else:
            logger.info("Default admin user 'admin' already exists.")
    except Exception as e:
        logger.error(f"Could not create or check for default admin user: {e}")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
