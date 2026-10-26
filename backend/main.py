from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Path,
    Depends,
    status,
    Body,
    Request,
    Header,
    BackgroundTasks,
)
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from typing import Dict, List, Any, Tuple, Optional, Literal
from contextlib import asynccontextmanager
from pydantic import BaseModel, EmailStr
import logging
import os  # For environment variables
import datetime
import uuid
import structlog

from core.session_registry import SessionRegistry, get_engine_instance

# Updated imports to point to the new 'core' modules for data/auth management
# and directly to reservoir_engineering.py for tools.
# Imports should be relative to the backend/ directory as the top-level package.
# from gaia_genesis.core.data_uploader import DataUploader # Moved down for E402
from gaia_genesis.core.database_manager import DatabaseManager
from gaia_genesis.core.auth_manager import AuthManager
import auth_utils

# Assuming these classes are directly available in the top-level reservoir_engineering.py now
from gaia_genesis.reservoir_engineering import (
    DeclineAnalysis,  # Changed from AdvancedDeclineAnalysis
    # ReservoirSimulator, # This class might have more complex dependencies not yet resolved
    # PVTProperties,  # F401: Unused PVTProperties import
)

# For ReservoirSimulator and AIPrediction, need to confirm their new locations
# or if they are self-contained. For now, let's assume they might be in their own
# files at the top level of gaia_genesis
from gaia_genesis.flow_simulation import (
    FlowSimulation as ReservoirSimulator,
)  # Class is FlowSimulation, alias for minimal changes
from gaia_genesis.prediction import AIPrediction  # Import AIPrediction
from gaia_genesis.economics import (
    EconomicsEvaluator,
    EconomicParameters,
    ProductionForecast,
)


import pandas as pd
import numpy as np  # Added import
import numpy_financial as npf
import io
import lasio

from config import settings  # Import the settings instance # Moved up
from gaia_genesis.core.data_uploader import DataUploader  # Moved up
from database import initialize_database_schema

# Load environment variables from .env file
# This should be one of the first things to ensure .env is loaded before settings are initialized
# load_dotenv() # Removed, pydantic-settings in config.py should handle .env loading


# Setup logging using LOG_LEVEL from settings
# Note: basicConfig should only be called once. If other modules also call it,
# it might not reconfigure. It's better to configure logging based on settings early.
logging.basicConfig(level=settings.LOG_LEVEL.upper())
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize SessionRegistry
    registry = SessionRegistry(
        default_ttl=settings.SESSION_TTL_SECONDS,
        max_capacity=settings.SESSION_MAX_ENTRIES,
        cleanup_interval=settings.SESSION_CLEANUP_INTERVAL_SECONDS,
    )
    await registry.start_janitor_task()
    app.state.session_registry = registry
    logger.info("SessionRegistry initialized and Janitor cleanup task started.")

    yield

    # Shutdown: Clean up background tasks and release active sessions
    await registry.stop_janitor_task()
    await registry.clear_all()
    logger.info("SessionRegistry shut down successfully.")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "API for reservoir engineering tasks. Authentication implemented. "
        "Configuration via Pydantic BaseSettings."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    request_id = str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    logger.info("request_started", method=request.method, path=request.url.path)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    logger.info("request_finished", status_code=response.status_code)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_error", error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": structlog.contextvars.get_contextvars().get("request_id"),
        },
    )


# Add CORS middleware to allow the Tauri frontend to communicate with the API
# In production, origins should be restricted to the Tauri app's scheme/origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# --- Configuration now comes from settings object ---
# The old os.getenv calls and default value definitions are removed.
# Warnings for default keys can be handled by checking settings.SECRET_KEY against
# a known insecure default, or by simply ensuring a strong default in config.py and
# requiring .env override for production.
# Check if the SECRET_KEY is the default placeholder from config.py
# This ensures the warning is accurate and tied to the actual default value.
DEFAULT_PLACEHOLDER_SECRET_KEY = "!!!DEFAULT_PLACEHOLDER_SECRET_KEY_CHANGE_ME!!!"
if settings.SECRET_KEY == DEFAULT_PLACEHOLDER_SECRET_KEY:
    logger.warning(
        "SECURITY WARNING: Using default placeholder JWT SECRET_KEY. "
        "This is INSECURE and MUST be changed for production. "
        "Set a strong, random SECRET_KEY in your .env file or environment variables."
    )

# Check for default database URL (this warning is less critical but good for awareness)
DEFAULT_DATABASE_URL = "sqlite:///./default_app_data.db"  # As defined in config.py
if settings.DATABASE_URL == DEFAULT_DATABASE_URL:
    logger.info(
        f"Using default DATABASE_URL: {settings.DATABASE_URL}. "
        "For production, configure a robust database (e.g., PostgreSQL) via .env "
        "or environment variables."
    )


# --- Initialize Database Schema ---
initialize_database_schema()

# --- Initialize Managers with configuration from settings ---
db_manager = DatabaseManager.get_instance(db_url=settings.DATABASE_URL)
# Ensure DB is connected and tables are created on startup
if not db_manager.connect():
    logger.critical(
        f"FATAL: Could not connect to the database at {settings.DATABASE_URL} "
        "on startup. Exiting."
    )
    exit(1)

auth_manager = AuthManager.get_instance(
    db_manager=db_manager,
    secret_key=settings.SECRET_KEY,
    access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
)
auth_utils.auth_manager = auth_manager
data_uploader = DataUploader.get_instance(db_manager=db_manager)

# OAuth2 Scheme

# --- Initialize Reservoir Engineering Tools ---
# WARNING: dca_analyzer is a global instance. If DeclineAnalysis methods become
# stateful, this could lead to concurrency issues. Currently, DeclineAnalysis
# methods (fit_arps, forecast_production) appear stateless.
dca_analyzer = DeclineAnalysis()  # Changed from AdvancedDeclineAnalysis
logger.info("Initialized DeclineAnalysis.")

# WARNING: res_simulator is a global instance of FlowSimulation.
# FlowSimulation is stateful (stores grid, properties, wells, results).
# This is NOT thread-safe for concurrent users modifying the same simulation setup.
# In a real multi-user app, simulation state would need to be managed per
# user/session or per simulation ID. Consider implementing a /reset endpoint as a
# minimal step for single-user workflow.
try:
    res_simulator = ReservoirSimulator(
        nx=10, ny=10, nz=1, dx=100, dy=100, dz=10
    )  # Example default values
    logger.info(
        "Initialized ReservoirSimulator (FlowSimulation) with default parameters."
    )
except Exception as e:
    logger.error(
        f"Failed to initialize ReservoirSimulator (FlowSimulation): {e}. "
        "Simulation endpoints may not work."
    )
    res_simulator = None  # Set to None if initialization fails

ai_predictor = AIPrediction()  # Instantiate AIPrediction
logger.info("AIPrediction functionality enabled.")

# Use AI_MODELS_DIR from settings
os.makedirs(settings.AI_MODELS_DIR, exist_ok=True)

# --- Import Custom Routers ---
try:
    from gaia_genesis.well_logs.las_parser import LASParser
    from gaia_genesis.api_v1.endpoints import (
        pvt_router,
        pvt_calculations as legacy_pvt_router,
        dca_router,
        rta_router,
        nodal_router,
        reservoir_router,
        simulation_router,
        economics_router,
        ai_router,
        auth_router,
        surveillance_router,
        reservoir_analysis_tools as gaia_reservoir_tools_router,
        static_modeling_tools as gaia_static_modeling_router,
        well_logs_router,
        jobs as jobs_router,
    )
    from gaia_genesis.api_v1.endpoints.jobs import (
        run_flowsim_task,
        run_prediction_train_task,
    )
    from gaia_genesis.core.database_models import Job

    app.include_router(
        auth_router.router, prefix="/api/v1/auth", tags=["Authentication"]
    )
    app.include_router(jobs_router.router, prefix="/api/v1/jobs", tags=["Jobs"])
    app.include_router(
        pvt_router.router, prefix="/api/v1/gaia/pvt", tags=["Gaia - PVT"]
    )
    app.include_router(
        legacy_pvt_router.router,
        prefix="/api/v1/gaia/pvt-legacy",
        tags=["Gaia - Legacy PVT"],
    )
    app.include_router(
        dca_router.router, prefix="/api/v1/gaia/dca", tags=["Gaia - DCA"]
    )
    app.include_router(
        rta_router.router, prefix="/api/v1/gaia/rta", tags=["Gaia - RTA"]
    )
    app.include_router(
        nodal_router.router, prefix="/api/v1/gaia/nodal", tags=["Gaia - Nodal"]
    )
    app.include_router(
        reservoir_router.router,
        prefix="/api/v1/gaia/reservoir",
        tags=["Gaia - Reservoir"],
    )
    app.include_router(
        simulation_router.router,
        prefix="/api/v1/gaia/simulation",
        tags=["Gaia - Simulation"],
    )
    app.include_router(
        economics_router.router,
        prefix="/api/v1/gaia/economics",
        tags=["Gaia - Economics"],
    )
    app.include_router(ai_router.router, prefix="/api/v1/gaia/ai", tags=["Gaia - AI"])
    app.include_router(
        surveillance_router.router,
        prefix="/api/v1/gaia/surveillance",
        tags=["Gaia - Surveillance"],
    )
    app.include_router(
        gaia_reservoir_tools_router.router,
        prefix="/api/v1/gaia/reservoir-tools",
        tags=["Gaia - Reservoir Tools"],
    )
    app.include_router(
        gaia_static_modeling_router.router,
        prefix="/api/v1/gaia/static-modeling",
        tags=["Gaia - Static Modeling"],
    )
    app.include_router(
        well_logs_router.router,
        prefix="/api/v1/gaia/well-logs",
        tags=["Gaia - Well Logs"],
    )

    logger.info("Successfully included all API routers.")
except Exception as e:
    logger.error(f"Error including API routers: {e}")


# --- Pydantic Models for API ---
class Token(BaseModel):
    access_token: str
    token_type: str


from auth_utils import UserBase, UserResponse


from pydantic import Field


class UserCreate(UserBase):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)
    role: Optional[Literal["admin", "editor", "user"]] = "user"


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[Literal["admin", "editor", "user"]] = None
    is_active: Optional[bool] = None


class WellMetadata(BaseModel):  # For creating wells along with data
    field_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# --- Decline Curve Analysis Models ---
class DCARequestData(BaseModel):
    time: List[float]  # In months or days, consistent units
    rate: List[float]  # Production rates corresponding to time data
    method_type: str  # 'exponential', 'hyperbolic', 'harmonic'


class DCAParams(BaseModel):  # Parameters for a single Arps model
    qi: float
    Di: float
    b: float  # b=0 for exponential, b=1 for harmonic
    type: str  # 'exponential', 'hyperbolic', 'harmonic'


class DCAResponse(BaseModel):  # Response for fitting a single model type
    fitted_params: DCAParams
    # best_model: Optional[str] = None # No longer fitting multiple, so no
    # 'best_model' selection here
    error: Optional[str] = None


class DCAPredictionRequest(BaseModel):
    # model_name: str # No longer needed as params are passed directly
    params: DCAParams  # Client sends the parameters of the model to use for prediction
    time_horizon: List[float]  # Array of future time points for prediction
    # (e.g., [30, 60, 90] days or months)
    # months_to_predict: int # Replaced by time_horizon for more flexibility


class DCAPredictionResponse(BaseModel):
    time_horizon: List[float]  # Echo back the time horizon used
    predicted_rate: List[float]
    model_used: str


class DCADataPoint(BaseModel):
    date: str
    time: float
    rate: float


class WellDCAResponse(BaseModel):
    well_name: str
    method_used: str
    fitted_params: DCAParams
    original_data: List[DCADataPoint]
    forecast_data: List[DCADataPoint]
    eur: float


# --- Flow Simulation Models ---
class SimGridRequest(BaseModel):
    nx: int
    dx: float
    area: float = 100.0


class SimFluidPropsRequest(BaseModel):
    viscosity: float
    compressibility: float
    fvf: float  # Formation Volume Factor


class SimRockPropsRequest(BaseModel):
    # Allow either a single value for homogeneous or a list for heterogeneous
    permeability: Any  # float or List[float]
    porosity: Any  # float or List[float]


class SimInitialConditionsRequest(BaseModel):
    initial_pressure: Any  # float or List[float]


class SimBoundaryConditionsRequest(BaseModel):
    type_left: str  # 'pressure' or 'flux'
    value_left: float
    type_right: str  # 'pressure' or 'flux'
    value_right: float


class SimWellRequest(BaseModel):
    name: str
    location_index: int  # 0-based index
    well_type: str = "producer"  # "producer" or "injector"
    control_type: str = "bhp"  # "bhp" or "rate"
    control_value: float  # BHP value or rate value (STB/day, negative for producer)
    rw: float = 0.25  # wellbore radius in ft
    skin: float = 0.0  # skin factor


class SimRunParamsRequest(BaseModel):
    end_time: float  # days
    dt: float  # days, time step size


class SimPressureResponse(BaseModel):
    time_steps: List[float]
    pressure_at_block: Dict[int, List[float]]  # Key is block index
    status: str


class SimWellRateResponse(BaseModel):
    time_steps: List[float]
    rates: Dict[str, List[float]]  # Key is well name
    status: str


# --- AI Prediction Models ---
class AIPredictionDataRequest(BaseModel):
    # Using a list of dicts for flexibility, similar to how DataFrames are often
    # sent via JSON. Each dict is a record/row.
    records: List[Dict[str, Any]]
    target_column: str
    feature_columns: List[str]
    # model_type: Optional[str] = "linear_regression" # Could be used to select
    # specific model type to train/use


class AITrainResponse(BaseModel):
    message: str
    trained_models: List[str]  # List of names of models trained
    performance: Optional[Dict[str, Dict[str, float]]] = None
    best_model: Optional[str] = None
    error: Optional[str] = None


class AIPredictRequest(BaseModel):
    records: List[Dict[str, Any]]  # Data to make predictions on (only features needed)
    feature_columns: List[str]  # To ensure correct feature order/selection
    # model_name: Optional[str] = None # If specific model prediction is desired


class AIPredictResponse(BaseModel):
    predictions: Dict[str, List[float]]  # Key: model_name, Value: list of predictions
    error: Optional[str] = None


# --- Economics Analysis Models ---
class EconomicsAnalyzeRequest(BaseModel):
    production_profile: List[float]
    oil_price: float
    opex: float
    capex: float
    discount_rate: float


class EconomicsAnalyzeResponse(BaseModel):
    npv: float
    irr: float
    payout_months: Optional[float] = None
    cash_flows: List[float]
    cumulative_cash_flow: List[float]


class AISaveModelRequest(BaseModel):
    model_name: str
    path: str  # Path where model should be saved on server


class AILoadModelRequest(BaseModel):
    model_name: str  # Name to assign to loaded model
    path: str  # Path from where model should be loaded on server


# --- API Helper Functions ---
def dataframe_to_json_serializable(df: pd.DataFrame | None) -> Any:
    """Converts DataFrame to JSON serializable format, handling NaNs."""
    if df is None:
        return pd.DataFrame().to_dict(orient="records")  # Return empty list for None df
    return df.where(pd.notnull(df), None).to_dict(orient="records")


from auth_utils import get_current_active_user, get_current_active_admin_user


# --- API Endpoints ---


@app.get("/", tags=["General"])
async def root() -> Dict[str, str]:
    """Root endpoint providing a welcome message."""
    return {
        "message": "Welcome to the PetroLúmen Backend API. Authentication is active."
    }


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
@app.post(
    "/api/v1/admin/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin", "Users"],
)
async def admin_create_new_user(
    user_in: UserCreate,
    current_admin_user: UserResponse = Depends(get_current_active_admin_user),
):
    """
    ADMIN Endpoint: Create a new user.
    Allows specifying username, email, password, full_name, and role.
    """
    logger.info(
        f"Admin user '{current_admin_user.username}' attempting to create new user "
        f"'{user_in.username}'."
    )
    # AuthManager.create_user handles hashing password and DB interaction.
    # It also checks for duplicate username/email and returns None if creation fails.
    created_user_dict = auth_manager.create_user(
        username=user_in.username,
        email=user_in.email,
        password=user_in.password,
        full_name=user_in.full_name,
        role=user_in.role,
    )
    if not created_user_dict:
        # This could be due to duplicate username/email, or other DB errors.
        # AuthManager logs specifics. We return a generic error here.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Could not create user '{user_in.username}'. Username or email "
                "might already exist, or data is invalid."
            ),
        )
    return UserResponse(**created_user_dict)


@app.get("/api/v1/users/me", response_model=UserResponse, tags=["Users"])
async def read_users_me(current_user: UserResponse = Depends(get_current_active_user)):
    """Fetch the current logged in user's details."""
    return current_user


# --- Admin User Management Endpoints ---
from fastapi import Query


@app.get(
    "/api/v1/admin/users",
    response_model=List[UserResponse],
    tags=["Admin", "Users"],
    dependencies=[Depends(get_current_active_admin_user)],
)
async def list_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=0),
    admin_user: UserResponse = Depends(
        get_current_active_admin_user
    ),  # Dependency for logging/audit if needed beyond auth
):
    """ADMIN Endpoint: List all users with pagination."""
    logger.info(
        f"Admin user '{admin_user.username}' listing all users (skip={skip}, "
        f"limit={limit})."
    )
    users = auth_manager.get_all_users(skip=skip, limit=limit)
    return [UserResponse(**user) for user in users]


@app.get(
    "/api/v1/admin/users/{username}",
    response_model=UserResponse,
    tags=["Admin", "Users"],
)
async def get_user_by_admin(
    username: str = Path(..., title="The username of the user to retrieve"),
    admin_user: UserResponse = Depends(get_current_active_admin_user),
):
    """ADMIN Endpoint: Get a specific user's details by username."""
    logger.info(
        f"Admin user '{admin_user.username}' retrieving details for user '{username}'."
    )
    user = auth_manager.get_user_details(username)  # Uses the new method in AuthManager
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found.",
        )
    return UserResponse(**user)


@app.put(
    "/api/v1/admin/users/{username}",
    response_model=UserResponse,
    tags=["Admin", "Users"],
)
async def update_user_by_admin(
    username: str = Path(..., title="The username of the user to update"),
    user_update_data: UserUpdate = Body(...),  # FastAPI uses Body for PUT request data
    admin_user: UserResponse = Depends(get_current_active_admin_user),
):
    """
    ADMIN Endpoint: Update a user's details (email, full_name, role, is_active).
    Password changes are not supported via this endpoint.
    """
    logger.info(
        f"Admin user '{admin_user.username}' attempting to update user '{username}'."
    )

    # Convert Pydantic model to dict, excluding unset values to avoid overwriting
    # with None
    update_data_dict = user_update_data.model_dump(exclude_unset=True)

    if not update_data_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided."
        )

    try:
        updated_user = auth_manager.update_user_details(username, update_data_dict)
    except (
        ValueError
    ) as e:  # Catch specific error for password update attempts from AuthManager
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not updated_user:
        # This could be because user not found, or DB update failed for other reasons.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found or update failed.",
        )
    return UserResponse(**updated_user)


@app.delete(
    "/api/v1/admin/users/{username}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Admin", "Users"],
)
async def delete_user_by_admin(
    username: str = Path(..., title="The username of the user to delete"),
    admin_user: UserResponse = Depends(get_current_active_admin_user),
):
    """ADMIN Endpoint: Delete a user by username."""
    logger.info(
        f"Admin user '{admin_user.username}' attempting to delete user '{username}'."
    )
    if username == admin_user.username:  # Prevent admin from deleting themselves
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin users cannot delete themselves.",
        )

    if not auth_manager.delete_user(username):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found or could not be deleted.",
        )
    # No content returned for 204
    return None


# --- Well Data Management Endpoints (Now Protected) ---
@app.post("/api/v1/wells/{well_name}/data", tags=["Well Data Management"])
async def upload_well_data(
    well_name: str = Path(..., title="The name of the well", min_length=1),
    files: List[UploadFile] = File(
        ..., description="List of CSV files to upload for the well"
    ),
    metadata: Optional[
        WellMetadata
    ] = None,  # Optional metadata via query or form-data in future
    current_user: UserResponse = Depends(get_current_active_user),  # Protect endpoint
) -> JSONResponse:
    """
    Uploads CSV data files for a specific well. Data is stored in the database.
    Requires authentication.
    """
    logger.info(
        f"User '{current_user.username}' attempting to upload data for well "
        f"'{well_name}'."
    )
    if not files:
        raise HTTPException(status_code=400, detail="No files were provided.")

    csv_files_content: List[Tuple[str, str]] = []
    for file_upload in files:  # Renamed 'file' to 'file_upload' to avoid conflict
        if file_upload.content_type != "text/csv":
            raise HTTPException(
                status_code=400,
                detail=(
                    f"File '{file_upload.filename}' is not a CSV. "
                    f"Found: {file_upload.content_type}"
                ),
            )
        try:
            content_bytes = await file_upload.read()
            content_str = content_bytes.decode("utf-8")
            csv_files_content.append((file_upload.filename, content_str))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error reading file {file_upload.filename}: {str(e)}",
            )
        finally:
            await file_upload.close()

    # Pass metadata to data_uploader
    field_name = metadata.field_name if metadata else None
    latitude = metadata.latitude if metadata else None
    longitude = metadata.longitude if metadata else None

    success, message, well_id = data_uploader.load_well_data(
        well_name,
        csv_files_content,
        field_name=field_name,
        latitude=latitude,
        longitude=longitude,
    )

    if not success:
        # Consider status codes more carefully based on message
        raise HTTPException(status_code=400, detail=message)

    # Fetch a preview of the just loaded data if successful
    data_preview_df = None
    if well_id:
        # This is a bit redundant as load_well_data doesn't return the df directly
        # anymore. For a true preview, we'd query. For now, this part is simplified.
        # Let's get the preview from the DB to be accurate
        temp_preview_df = data_uploader.get_data_preview(well_name, n_rows=5)
        if temp_preview_df is not None and not temp_preview_df.empty:
            data_preview_df = temp_preview_df

    return JSONResponse(
        content=jsonable_encoder(
            {
                "message": message,
                "well_name": well_name,
                "well_id": well_id,
                "files_processed": [f.filename for f in files],
                "data_preview_first_5_rows": dataframe_to_json_serializable(
                    data_preview_df
                ),
            }
        )
    )


@app.get("/api/v1/wells/{well_name}/preview", tags=["Well Data Management"])
async def get_well_data_preview(
    well_name: str = Path(..., title="The name of the well", min_length=1),
    n_rows: int = 5,
    current_user: UserResponse = Depends(get_current_active_user),  # Protect endpoint
) -> JSONResponse:
    """
    Retrieves a preview (first N rows) of the data for a specific well from the
    database.
    """
    logger.info(
        f"User '{current_user.username}' requesting preview for well '{well_name}'."
    )
    preview_df = data_uploader.get_data_preview(well_name, n_rows)
    if preview_df is None:  # Well not found
        raise HTTPException(
            status_code=404, detail="Well '{}' not found.".format(well_name)
        )
    if (
        preview_df.empty
        and data_uploader.db_manager.get_well_by_name(well_name) is not None
    ):  # Well exists but no data
        pass  # Return empty preview is fine

    return JSONResponse(
        content={
            "well_name": well_name,
            "preview": dataframe_to_json_serializable(preview_df),
        }
    )


@app.get("/api/v1/wells/{well_name}/statistics", tags=["Well Data Management"])
async def get_well_data_statistics(
    well_name: str = Path(..., title="The name of the well", min_length=1),
    current_user: UserResponse = Depends(get_current_active_user),  # Protect endpoint
) -> JSONResponse:
    """
    Retrieves descriptive statistics for the data of a specific well from the
    database.
    """
    logger.info(
        f"User '{current_user.username}' requesting statistics for well '{well_name}'."
    )
    stats = data_uploader.get_well_statistics(well_name)
    if stats is None:  # Well not found
        raise HTTPException(
            status_code=404, detail="Well '{}' not found.".format(well_name)
        )
    # If stats exist but show 0 rows (well exists, no data), it's still a valid response
    return JSONResponse(content={"well_name": well_name, "statistics": stats})


@app.get("/api/v1/wells", tags=["Well Data Management"])
async def list_wells_with_data(
    current_user: UserResponse = Depends(get_current_active_user),  # Protect endpoint
) -> JSONResponse:
    """Lists all wells from the database."""
    logger.info(f"User '{current_user.username}' listing all wells.")
    wells = data_uploader.list_loaded_wells()  # This now returns list of dicts from DB
    return JSONResponse(content=jsonable_encoder({"wells": wells}))


@app.post("/api/v1/wells/{well_id}/upload-las", tags=["Well Data Management"])
async def upload_las_file(
    well_id: str = Path(..., title="The ID or name of the well"),
    file: UploadFile = File(..., description="The LAS file to upload"),
    current_user: UserResponse = Depends(get_current_active_user),
) -> JSONResponse:
    """
    Parses an uploaded .las file using LASParser and returns curves, metadata, tracks, and depth records.
    Requires authentication.
    """
    logger.info(
        f"User '{current_user.username}' uploading LAS file for well '{well_id}'."
    )
    try:
        content_bytes = await file.read()
        parsed_data = LASParser.parse_las(content_bytes)

        return JSONResponse(
            content=jsonable_encoder(
                {
                    "message": f"Successfully parsed LAS file '{file.filename}'.",
                    "well_id": well_id,
                    "filename": file.filename,
                    "metadata": parsed_data["metadata"],
                    "curves": parsed_data["curves"],
                    "tracks": parsed_data["tracks"],
                    "data": parsed_data["records"],
                    "summary": parsed_data["summary"],
                }
            )
        )
    except Exception as e:
        logger.error(f"Error parsing LAS file '{file.filename}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse LAS file: {str(e)}",
        )
    finally:
        await file.close()


@app.post(
    "/api/v1/economics/analyze",
    response_model=EconomicsAnalyzeResponse,
    tags=["Economics"],
)
async def analyze_economics(
    data: EconomicsAnalyzeRequest,
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Analyzes economics given a production profile, oil price, OPEX, CAPEX, and discount rate.
    Uses EconomicsEvaluator to calculate NPV, IRR, Payout Month, and cumulative cash flow.
    """
    try:
        econ_params = EconomicParameters(
            capex=abs(data.capex),
            oil_price=data.oil_price,
            opex_var_oil=data.opex,
            opex_fixed_monthly=0.0,
            royalty_rate=0.0,
            severance_tax_rate=0.0,
            income_tax_rate=0.0,
            discount_rate_annual=data.discount_rate,
            period_frequency="annual",
        )
        prod_forecast = ProductionForecast(
            time_periods=[float(i + 1) for i in range(len(data.production_profile))],
            oil_rates=data.production_profile,
            rates_are_daily=False,
        )

        res = EconomicsEvaluator.evaluate(econ_params, prod_forecast)

        return EconomicsAnalyzeResponse(
            npv=res.npv,
            irr=res.irr,
            payout_months=res.payout_months,
            cash_flows=[p.net_cash_flow for p in res.cash_flow_periods],
            cumulative_cash_flow=[p.cumulative_net_cash_flow for p in res.cash_flow_periods],
        )
    except Exception as e:
        logger.error(f"Error in economics analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Economics calculation failed: {str(e)}",
        )


# Admin endpoint - example of role-based access (conceptual, AuthManager doesn't
# enforce roles yet on this endpoint)
@app.delete("/api/v1/admin/wells/{well_name}", tags=["Admin", "Well Data Management"])
async def admin_delete_well(
    well_name: str = Path(..., title="The name of the well to delete"),
    admin_user: UserResponse = Depends(
        get_current_active_admin_user
    ),  # Use admin dependency
):
    """ADMIN Endpoint: Deletes a well and its associated data. Requires admin privileges."""
    logger.info(
        f"Admin user '{admin_user.username}' attempting to delete well '{well_name}'."
    )
    # The get_current_active_admin_user dependency already ensures user is an admin.

    well = data_uploader.db_manager.get_well_by_name(well_name)
    if not well:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Well '{}' not found.".format(well_name),
        )

    session = data_uploader.db_manager.get_session()
    try:
        # SQLAlchemy's cascade delete should handle ProductionData due to relationship
        # config
        session.delete(well)
        session.commit()
        logger.info(
            f"Admin user '{admin_user.username}' successfully deleted well "
            f"'{well_name}' (ID: {well.id})."
        )  # Corrected here
        return JSONResponse(
            content={
                "message": f"Well '{well_name}' and its data deleted successfully."
            }
        )
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting well '{well_name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not delete well '{well_name}'.",
        )
    finally:
        session.close()


# Removed /api/v1/admin/clear_all_well_data as deleting all data from a real DB is
# too destructive for a generic endpoint. Specific deletion logic (like per-well
# above) is preferred.


# --- Decline Curve Analysis Endpoints ---
@app.post(
    "/api/v1/reservoir/dca/fit",
    response_model=DCAResponse,
    tags=["Reservoir Engineering"],
)
async def fit_decline_models(
    data: DCARequestData, current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Fits a specified Arps decline curve model to provided time and rate data.
    """
    try:
        time_array = np.array(data.time)
        rate_array = np.array(data.rate)

        if data.method_type not in ["exponential", "hyperbolic", "harmonic"]:
            raise ValueError(
                "Invalid method_type. Must be 'exponential', 'hyperbolic', or "
                "'harmonic'."
            )

        # dca_analyzer is now an instance of DeclineAnalysis
        # fit_arps returns a dict like {'qi': ..., 'di': ..., 'b': ..., 'method': ...}
        fitted_params_dict = dca_analyzer.fit_arps(
            time=time_array, rate=rate_array, method=data.method_type
        )

        if (
            not fitted_params_dict
        ):  # Should not happen if fit_arps raises errors for bad fits
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Model fitting failed to return parameters.",
            )

        # Ensure 'b' is present, default if necessary (e.g. for
        # exponential/harmonic from fit_arps)
        b_value = fitted_params_dict.get("b")
        if (
            b_value is None
        ):  # fit_arps for exponential/harmonic might not return 'b' explicitly or
            # set it to 0/1
            if data.method_type == "exponential":
                b_value = 0.0
            elif data.method_type == "harmonic":
                b_value = 1.0
            else:
                # Default for hyperbolic if somehow missing, though fit_arps should
                # provide it
                b_value = 0.5

        response_params = DCAParams(
            qi=fitted_params_dict["qi"],
            Di=fitted_params_dict["di"],
            b=b_value,
            type=fitted_params_dict["method"],
        )

        return DCAResponse(fitted_params=response_params)
    except ValueError as ve:
        logger.error(f"ValueError in DCA fit: {ve}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Unexpected error in DCA fit endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during DCA model fitting.",
        )


# Note: For prediction, the current AdvancedDeclineAnalysis class stores state
# (fitted models). This is suitable if the dca_analyzer instance is per-request or
# per-user-session. If dca_analyzer is global, it's not thread-safe for
# concurrent users fitting different data. For this iteration, we'll assume a new
# instance is used or state is managed appropriately. A stateless approach would
# require passing model parameters for prediction.


@app.post(
    "/api/v1/reservoir/dca/predict",
    response_model=DCAPredictionResponse,
    tags=["Reservoir Engineering"],
)
async def predict_decline(
    request: DCAPredictionRequest,  # This would need to include model params if
    # dca_analyzer is stateless
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Predicts future production rates using specified Arps model parameters.
    This endpoint is now stateless.
    """
    try:
        # Convert params from Pydantic model to dict for forecast_production
        params_dict = {
            "qi": request.params.qi,
            "di": request.params.Di,
            "b": request.params.b,
            "method": request.params.type,  # Ensure 'type' in DCAParams matches
            # 'method' for forecast_production
        }
        time_horizon_np = np.array(request.time_horizon)

        predicted_rates_np = dca_analyzer.forecast_production(
            params=params_dict, time=time_horizon_np
        )

        if predicted_rates_np is None or len(predicted_rates_np) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Prediction resulted in empty data.",
            )

        return DCAPredictionResponse(
            time_horizon=time_horizon_np.tolist(),
            predicted_rate=predicted_rates_np.tolist(),
            model_used=request.params.type,
        )
    except ValueError as ve:
        logger.error(f"ValueError in DCA predict: {ve}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Error during DCA prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during prediction: {str(e)}",
        )


@app.get(
    "/api/v1/reservoir/dca/well/{well_name}",
    response_model=WellDCAResponse,
    tags=["Reservoir Engineering"],
)
async def get_well_dca(
    well_name: str = Path(..., title="The name of the well"),
    method: str = "hyperbolic",
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Fetches production data for a well and performs Decline Curve Analysis.
    Returns fitted parameters and points for visualization.
    """
    # 1. Fetch data
    well = db_manager.get_well_by_name(well_name)
    if not well:
        raise HTTPException(status_code=404, detail=f"Well '{well_name}' not found")

    data_dicts = db_manager.get_well_production_data(well.id)
    if not data_dicts or len(data_dicts) < 2:
        raise HTTPException(
            status_code=400,
            detail="Not enough production data for DCA (minimum 2 points)",
        )

    df = pd.DataFrame(data_dicts)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # Use oil_rate for now
    if "oil_rate" not in df.columns or df["oil_rate"].isnull().all():
        raise HTTPException(
            status_code=400, detail=f"Well '{well_name}' has no oil_rate data for DCA"
        )

    # Drop NaNs for fitting
    df_fit = df.dropna(subset=["oil_rate"]).copy()

    if len(df_fit) < 2:
        raise HTTPException(
            status_code=400, detail="Not enough valid oil_rate points for DCA"
        )

    start_date = df_fit["date"].min()
    df_fit["time_days"] = (df_fit["date"] - start_date).dt.days.astype(float)

    time_np = df_fit["time_days"].values
    rate_np = df_fit["oil_rate"].values

    # 2. Fit model
    try:
        params = dca_analyzer.fit_arps(time_np, rate_np, method=method)
    except Exception as e:
        logger.error(f"DCA fit failed for well {well_name}: {e}")
        raise HTTPException(status_code=500, detail=f"DCA fitting failed: {str(e)}")

    # 3. Forecast
    # Forecast for existing range + 2 years
    last_day = time_np[-1]
    forecast_days = np.linspace(0, last_day + 730, 100)
    forecast_rates = dca_analyzer.forecast_production(params, forecast_days)

    # 4. EUR
    eur = dca_analyzer.calculate_eur(params)

    # 5. Prepare Response
    original_points = []
    for _, row in df_fit.iterrows():
        original_points.append(
            DCADataPoint(
                date=row["date"].strftime("%Y-%m-%d"),
                time=row["time_days"],
                rate=row["oil_rate"],
            )
        )

    forecast_points = []
    for d, r in zip(forecast_days, forecast_rates):
        forecast_date = start_date + datetime.timedelta(days=float(d))
        forecast_points.append(
            DCADataPoint(
                date=forecast_date.strftime("%Y-%m-%d"),
                time=float(d),
                rate=float(r),
            )
        )

    return WellDCAResponse(
        well_name=well_name,
        method_used=method,
        fitted_params=DCAParams(
            qi=params["qi"],
            Di=params["di"],
            b=params.get("b", 0),
            type=params["method"],
        ),
        original_data=original_points,
        forecast_data=forecast_points,
        eur=eur,
    )


# --- Flow Simulation Endpoints & Dependency Helper ---


async def get_res_simulator(
    request: Request,
    current_user: UserResponse = Depends(get_current_active_user),
    session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> ReservoirSimulator:
    """Dependency helper to get session-scoped ReservoirSimulator instance."""
    return await get_engine_instance(
        engine_name="res_simulator",
        factory_fn=ReservoirSimulator,
        request=request,
        current_user=current_user,
        session_id=session_id,
    )


@app.post(
    "/api/v1/reservoir/flowsim/reset", tags=["Reservoir Engineering", "Flow Simulation"]
)
async def reset_flow_simulation_instance(
    request: Request,
    current_user: UserResponse = Depends(get_current_active_user),
    session_id: Optional[str] = Header(None, alias="X-Session-ID"),
):
    """
    Resets the flow simulator instance.
    When USE_SESSION_REGISTRY is True, resets only the requesting user's session simulator instance.
    When USE_SESSION_REGISTRY is False, resets the global shared res_simulator.
    """
    if settings.USE_SESSION_REGISTRY:
        registry: SessionRegistry = getattr(request.app.state, "session_registry", None)
        if registry is not None:
            session_key = (
                f"{current_user.id}:{session_id}"
                if session_id
                else str(current_user.id)
            )
            await registry.reset_engine(
                session_key=session_key, engine_type="res_simulator"
            )
            logger.info(
                f"User '{current_user.username}' reset their session FlowSimulator instance."
            )
            return {
                "message": "Session reservoir simulator reset successfully.",
            }

    global res_simulator
    try:
        # Re-initialize with default parameters (same as on startup)
        res_simulator = ReservoirSimulator(nx=10, ny=10, nz=1, dx=100, dy=100, dz=10)
        logger.info(
            f"User '{current_user.username}' reset the global FlowSimulator instance."
        )
        return {
            "message": "Global FlowSimulator instance has been reset to default "
            "parameters.",
            "warning": "This operation affects a global, shared instance.",
        }
    except Exception as e:
        logger.error(
            f"Failed to reset ReservoirSimulator (FlowSimulation): {e}", exc_info=True
        )
        res_simulator = None
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset simulator: {str(e)}",
        )


@app.post(
    "/api/v1/reservoir/flowsim/setup/grid",
    tags=["Reservoir Engineering", "Flow Simulation"],
)
async def setup_simulation_grid(
    grid_data: SimGridRequest,
    simulator: ReservoirSimulator = Depends(get_res_simulator),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Sets up the grid for the flow simulator instance.
    """
    if simulator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Flow simulator is not available. Try resetting.",
        )
    try:
        simulator.setup_1d_grid(
            grid_data.nx, grid_data.dx, grid_data.area
        )  # Example for 1D
        return {
            "message": (
                f"Grid setup: nx={grid_data.nx}, dx={grid_data.dx}, "
                f"area={grid_data.area}"
            ),
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error setting up simulation grid: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error setting up grid.",
        )


@app.post(
    "/api/v1/reservoir/flowsim/setup/fluid",
    tags=["Reservoir Engineering", "Flow Simulation"],
)
async def setup_simulation_fluid_properties(
    props: SimFluidPropsRequest,
    simulator: ReservoirSimulator = Depends(get_res_simulator),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Sets fluid properties for the flow simulator instance.
    """
    if simulator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Flow simulator is not available. Try resetting.",
        )
    try:
        simulator.set_fluid_properties(
            props.viscosity, props.compressibility, props.fvf
        )
        return {
            "message": "Fluid properties set.",
        }
    except Exception as e:
        logger.error(f"Error setting fluid properties: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error setting fluid properties.",
        )


@app.post(
    "/api/v1/reservoir/flowsim/setup/rock",
    tags=["Reservoir Engineering", "Flow Simulation"],
)
async def setup_simulation_rock_properties(
    props: SimRockPropsRequest,
    simulator: ReservoirSimulator = Depends(get_res_simulator),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Sets rock properties for the flow simulator instance.
    """
    if simulator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Flow simulator is not available. Try resetting.",
        )
    try:
        simulator.set_rock_properties(props.permeability, props.porosity)
        return {
            "message": "Rock properties set.",
        }
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error setting rock properties: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error setting rock properties.",
        )


@app.post(
    "/api/v1/reservoir/flowsim/setup/initial",
    tags=["Reservoir Engineering", "Flow Simulation"],
)
async def setup_simulation_initial_conditions(
    cond: SimInitialConditionsRequest,
    simulator: ReservoirSimulator = Depends(get_res_simulator),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Sets initial conditions for the flow simulator instance.
    """
    if simulator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Flow simulator is not available. Try resetting.",
        )
    try:
        simulator.set_initial_conditions(cond.initial_pressure)
        return {
            "message": "Initial conditions set.",
        }
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error setting initial conditions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error setting initial conditions.",
        )


@app.post(
    "/api/v1/reservoir/flowsim/setup/boundary",
    tags=["Reservoir Engineering", "Flow Simulation"],
)
async def setup_simulation_boundary_conditions(
    bc: SimBoundaryConditionsRequest,
    simulator: ReservoirSimulator = Depends(get_res_simulator),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Sets boundary conditions for the flow simulator instance.
    """
    if simulator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Flow simulator is not available. Try resetting.",
        )
    try:
        simulator.set_boundary_conditions(
            bc.type_left, bc.value_left, bc.type_right, bc.value_right
        )
        return {
            "message": "Boundary conditions set.",
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error setting boundary conditions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error setting boundary conditions.",
        )


@app.post(
    "/api/v1/reservoir/flowsim/setup/well",
    tags=["Reservoir Engineering", "Flow Simulation"],
)
async def add_simulation_well(
    well_data: SimWellRequest,
    simulator: ReservoirSimulator = Depends(get_res_simulator),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Adds a well to the flow simulator instance.
    """
    if simulator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Flow simulator is not available. Try resetting.",
        )
    try:
        simulator.add_well(
            name=well_data.name,
            location_index=well_data.location_index,
            well_type=well_data.well_type,
            control_type=well_data.control_type,
            control_value=well_data.control_value,
            rw=well_data.rw,
            skin=well_data.skin,
        )
        return {
            "message": f"Well '{well_data.name}' added.",
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error adding simulation well: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding well.",
        )


@app.post(
    "/api/v1/reservoir/flowsim/run",
    response_model=SimPressureResponse,
    tags=["Reservoir Engineering", "Flow Simulation"],
)
async def run_flow_simulation(
    params: SimRunParamsRequest,
    simulator: ReservoirSimulator = Depends(get_res_simulator),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Runs the 1D flow simulation using the current state of the simulator instance.
    """
    if simulator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Flow simulator is not available. Try resetting.",
        )
    try:
        simulator.run_simulation(params.end_time, params.dt)

        sim_status = simulator.simulation_results.get("status", "Unknown")
        if sim_status == "Failed: Singular matrix":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Simulation failed due to singular matrix. Check parameters or "
                    "boundary conditions."
                ),
            )
        elif sim_status != "Completed":
            logger.warning(f"Simulation completed with status: {sim_status}")

        pressures_vs_time = simulator.simulation_results.get("pressures_vs_time", [])
        block0_pressures = (
            [
                p_step[0]
                for p_step in pressures_vs_time
                if isinstance(p_step, (np.ndarray, list)) and len(p_step) > 0
            ]
            if pressures_vs_time
            else []
        )
        time_array_list = simulator.simulation_results.get(
            "time_array", np.array([])
        ).tolist()

        return SimPressureResponse(
            time_steps=time_array_list,
            pressure_at_block={0: block0_pressures},
            status=sim_status,
        )
    except HTTPException:
        raise
    except ValueError as ve:
        logger.error(f"ValueError during flow simulation run: {ve}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Error during flow simulation run: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during simulation: {str(e)}",
        )


@app.post(
    "/api/v1/reservoir/flowsim/run_async",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Reservoir Engineering", "Flow Simulation"],
)
async def run_flow_simulation_async(
    params: SimRunParamsRequest,
    background_tasks: BackgroundTasks,
    simulator: ReservoirSimulator = Depends(get_res_simulator),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Submits a flow simulation run as an asynchronous background job.
    Returns 202 Accepted with job_id immediately.
    """
    if simulator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Flow simulator is not available.",
        )

    db_mgr = DatabaseManager.get_instance()
    session = db_mgr.get_session()
    try:
        new_job = Job(
            user_id=uuid.UUID(str(current_user.id)),
            status="pending",
        )
        session.add(new_job)
        session.commit()
        session.refresh(new_job)
        job_id = str(new_job.id)
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating job for flowsim_async: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create background job.",
        )
    finally:
        session.close()

    background_tasks.add_task(
        run_flowsim_task,
        job_id=job_id,
        simulator=simulator,
        end_time=params.end_time,
        dt=params.dt,
    )

    return {"job_id": job_id, "status": "pending"}


@app.get(
    "/api/v1/reservoir/flowsim/results/well_rates",
    response_model=SimWellRateResponse,
    tags=["Reservoir Engineering"],
)
async def get_simulation_well_rates(
    simulator: ReservoirSimulator = Depends(get_res_simulator),
    current_user: UserResponse = Depends(get_current_active_user),
):
    if (
        not simulator.simulation_results
        or simulator.simulation_results.get("status") != "Completed"
    ):
        raise HTTPException(
            status_code=400, detail="Simulation not run or not completed successfully."
        )
    return SimWellRateResponse(
        time_steps=simulator.simulation_results.get(
            "time_array", np.array([])
        ).tolist(),
        rates=simulator.simulation_results.get("well_rates_vs_time", {}),
        status=simulator.simulation_results.get("status"),
    )


# --- AI Prediction Endpoints & Dependency Helper ---


async def get_ai_predictor(
    request: Request,
    current_user: UserResponse = Depends(get_current_active_user),
    session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> AIPrediction:
    """Dependency helper to get session-scoped AIPrediction instance."""
    return await get_engine_instance(
        engine_name="ai_predictor",
        factory_fn=AIPrediction,
        request=request,
        current_user=current_user,
        session_id=session_id,
    )


@app.post(
    "/api/v1/reservoir/prediction/train",
    response_model=AITrainResponse,
    tags=["Reservoir Engineering", "AI Prediction"],
)
async def train_ai_models(
    request: AIPredictionDataRequest,
    predictor: AIPrediction = Depends(get_ai_predictor),
    current_user: UserResponse = Depends(get_current_active_user),
):
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AIPrediction service is not available.",
        )
    try:
        df = pd.DataFrame(request.records)
        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No records provided for training.",
            )

        if not all(col in df.columns for col in request.feature_columns):
            missing_cols = [
                col for col in request.feature_columns if col not in df.columns
            ]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing feature columns in provided records: {missing_cols}",
            )
        if request.target_column not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Target column '{request.target_column}' not found in "
                    "provided records."
                ),
            )

        X_train, X_test, y_train, y_test = predictor.prepare_data(
            df, request.target_column, request.feature_columns
        )
        predictor.train_models(X_train, y_train, X_test, y_test)

        trained_model_names = list(predictor.models.keys())
        if not trained_model_names:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Model training did not result in any models.",
            )

        performance = {}
        for name, info in predictor.models.items():
            performance[name] = {
                "r2": info.get("test_r2", 0),
                "rmse": info.get("test_rmse", 0),
            }

        return AITrainResponse(
            message="Models trained successfully. Best model selected based on R2 score.",
            trained_models=trained_model_names,
            performance=performance,
            best_model=predictor.best_model,
        )
    except HTTPException:
        raise
    except ValueError as ve:
        logger.error(f"ValueError during AI model training: {ve}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Unexpected error in AI model training endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during AI training: {str(e)}",
        )


@app.post(
    "/api/v1/reservoir/prediction/train_async",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Reservoir Engineering", "AI Prediction"],
)
async def train_ai_models_async(
    request: AIPredictionDataRequest,
    background_tasks: BackgroundTasks,
    predictor: AIPrediction = Depends(get_ai_predictor),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Submits an AI model training run as an asynchronous background job.
    Returns 202 Accepted with job_id immediately.
    """
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AIPrediction service is not available.",
        )

    db_mgr = DatabaseManager.get_instance()
    session = db_mgr.get_session()
    try:
        new_job = Job(
            user_id=uuid.UUID(str(current_user.id)),
            status="pending",
        )
        session.add(new_job)
        session.commit()
        session.refresh(new_job)
        job_id = str(new_job.id)
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating job for train_async: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create background job.",
        )
    finally:
        session.close()

    background_tasks.add_task(
        run_prediction_train_task,
        job_id=job_id,
        predictor=predictor,
        records=request.records,
        target_column=request.target_column,
        feature_columns=request.feature_columns,
    )

    return {"job_id": job_id, "status": "pending"}


@app.post(
    "/api/v1/reservoir/prediction/well/{well_name}/train",
    response_model=AITrainResponse,
    tags=["Reservoir Engineering", "AI Prediction"],
)
async def train_well_ai_models(
    well_name: str = Path(..., title="The name of the well"),
    target_column: str = Body(..., embed=True),
    feature_columns: List[str] = Body(..., embed=True),
    predictor: AIPrediction = Depends(get_ai_predictor),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Fetches production data for a well and trains AI models to predict production.
    """
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AIPrediction service is not available.",
        )

    well = db_manager.get_well_by_name(well_name)
    if not well:
        raise HTTPException(status_code=404, detail=f"Well '{well_name}' not found")

    data_dicts = db_manager.get_well_production_data(well.id)
    if not data_dicts or len(data_dicts) < 10:
        raise HTTPException(
            status_code=400,
            detail="Not enough production data for AI training (minimum 10 points)",
        )

    df = pd.DataFrame(data_dicts)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    start_date = df["date"].min()
    df["days_from_start"] = (df["date"] - start_date).dt.days.astype(float)

    available_cols = df.columns.tolist()
    if target_column not in available_cols:
        raise HTTPException(
            status_code=400, detail=f"Target column '{target_column}' not found"
        )
    for col in feature_columns:
        if col not in available_cols:
            raise HTTPException(
                status_code=400, detail=f"Feature column '{col}' not found"
            )

    try:
        X_train, X_test, y_train, y_test = predictor.prepare_data(
            df, target_column, feature_columns
        )
        predictor.train_models(X_train, y_train, X_test, y_test)

        performance = {}
        for name, info in predictor.models.items():
            performance[name] = {
                "r2": info.get("test_r2", 0),
                "rmse": info.get("test_rmse", 0),
            }

        return AITrainResponse(
            message=f"Models for well '{well_name}' trained successfully.",
            trained_models=list(predictor.models.keys()),
            performance=performance,
            best_model=predictor.best_model,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"AI training failed for well {well_name}: {e}")
        raise HTTPException(status_code=500, detail=f"AI training failed: {str(e)}")


@app.post(
    "/api/v1/reservoir/prediction/predict",
    response_model=AIPredictResponse,
    tags=["Reservoir Engineering", "AI Prediction"],
)
async def predict_with_ai_models(
    request: AIPredictRequest,
    predictor: AIPrediction = Depends(get_ai_predictor),
    current_user: UserResponse = Depends(get_current_active_user),
):
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AIPrediction service is not available.",
        )
    try:
        df_features = pd.DataFrame(request.records)
        if df_features.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No records provided for prediction.",
            )

        if not predictor.feature_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "AI model has not been trained or feature columns are not set. "
                    "Load or train a model first."
                ),
            )

        if not all(col in df_features.columns for col in predictor.feature_columns):
            missing_cols = [
                col
                for col in predictor.feature_columns
                if col not in df_features.columns
            ]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Prediction data missing required feature columns: "
                    f"{missing_cols}"
                ),
            )

        model_to_use_name = (
            getattr(request, "model_name", None)
            if getattr(request, "model_name", None)
            else predictor.best_model
        )
        if not model_to_use_name or model_to_use_name not in predictor.models:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No suitable model available for prediction. Train or load a model.",
            )

        predictions_array = predictor.predict(df_features, model_name=model_to_use_name)

        serializable_predictions = {model_to_use_name: predictions_array.tolist()}

        return AIPredictResponse(predictions=serializable_predictions)
    except HTTPException:
        raise
    except ValueError as ve:
        logger.error(f"ValueError during AI prediction: {ve}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Unexpected error in AI prediction endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during AI prediction: {str(e)}",
        )


@app.post(
    "/api/v1/reservoir/prediction/save_model",
    tags=["Reservoir Engineering", "AI Prediction"],
)
async def save_ai_model(
    request: AISaveModelRequest,
    predictor: AIPrediction = Depends(get_ai_predictor),
    current_user: UserResponse = Depends(get_current_active_user),
):
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AIPrediction service is not available.",
        )

    if ".." in request.path or request.path.startswith("/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid path specified. Path should be relative and not contain '..'.",
        )

    full_save_path = Path(settings.AI_MODELS_DIR) / request.path

    try:
        predictor.save_model(str(full_save_path), model_name=request.model_name)
        return {
            "message": (
                f"Model '{request.model_name}' saved successfully to "
                f"'{full_save_path}'."
            ),
            "saved_path": str(full_save_path),
        }
    except FileNotFoundError as fnfe:
        logger.error(f"Save AI Model Error: {fnfe}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(fnfe))
    except ValueError as ve:
        logger.error(f"Save AI Model Error: {ve}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Error during AI model saving: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save model '{request.model_name}': {str(e)}",
        )


@app.post(
    "/api/v1/reservoir/prediction/load_model",
    tags=["Reservoir Engineering", "AI Prediction"],
)
async def load_ai_model(
    request: AILoadModelRequest,
    predictor: AIPrediction = Depends(get_ai_predictor),
    current_user: UserResponse = Depends(get_current_active_user),
):
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AIPrediction service is not available.",
        )

    if ".." in request.path or request.path.startswith("/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid path specified. Path should be relative and not contain '..'.",
        )

    full_load_path = Path(settings.AI_MODELS_DIR) / request.path

    if not full_load_path.suffix == ".joblib":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Path must point to a .joblib file.",
        )

    try:
        loaded_model_name = predictor.load_model(str(full_load_path))
        return {
            "message": (
                f"Model '{loaded_model_name}' loaded successfully from "
                f"'{request.path}'. This is now the active model."
            )
        }
    except FileNotFoundError:
        logger.error(f"AI model file not found at {full_load_path}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model file not found at '{request.path}'.",
        )
    except Exception as e:
        logger.exception(f"Error loading AI model from {full_load_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load model from '{request.path}': {str(e)}",
        )


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
                role="admin",  # Set role to admin
                full_name="Admin User",
            )
            logger.info(
                "Created default admin user (admin/adminpassword) for development."
            )
        else:
            logger.info("Default admin user 'admin' already exists.")
    except Exception as e:
        logger.error(f"Could not create or check for default admin user: {e}")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
