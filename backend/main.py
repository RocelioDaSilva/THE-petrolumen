from fastapi import FastAPI, HTTPException, Depends, Body, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
import os # For file operations if needed

# Import classes from our reservoir engineering package
from gaia_genesis.reservoir_engineering import (
    DataUploader,
    AdvancedDeclineAnalysis,
    AIPrediction,
    DatabaseManager, # Assuming DB interactions are managed through this
    ReservoirSimulator,
    AuthManager
)

# --- Configuration ---
# In a real app, use environment variables or a config file
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/petrolumen_db")
AUTH_DB_URL = os.getenv("AUTH_DATABASE_URL", "postgresql://auth_user:auth_pass@localhost:5432/petrolumen_auth_db") # Separate or same DB
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_for_fastapi_app") # CHANGE THIS!
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# --- Initialize Application and Managers ---
app = FastAPI(title="PetroLúmen Backend API", version="0.1.0")

# Database Manager (for main app data)
# This assumes DatabaseManager can parse a URL or take individual params
# For simplicity, let's assume it needs individual params based on its current __init__
# You'd parse DATABASE_URL here to extract components.
# For now, using placeholder direct params.
db_manager = DatabaseManager(
    db_name=os.getenv("DB_NAME", "petrolumen_db"),
    user=os.getenv("DB_USER", "user"),
    password=os.getenv("DB_PASS", "password"),
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432")
)
# Attempt to connect on startup (optional, can be done per-request)
# db_manager.connect() # Consider lifespan events for FastAPI for connect/close

# Auth Manager (for user authentication and JWTs)
# Similar parsing for AUTH_DB_URL needed if it's a single string.
auth_manager = AuthManager(
    secret_key=SECRET_KEY,
    access_token_expire_minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
    db_params={ # Assuming AuthManager takes a dict of params
        "db_name": os.getenv("AUTH_DB_NAME", "petrolumen_auth_db"),
        "user": os.getenv("AUTH_DB_USER", "auth_user"),
        "password": os.getenv("AUTH_DB_PASS", "auth_pass"),
        "host": os.getenv("AUTH_DB_HOST", "localhost"),
        "port": os.getenv("AUTH_DB_PORT", "5432"),
    }
)

# OAuth2 Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Points to the /token endpoint

# --- Pydantic Models for Request/Response ---
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    is_admin: Optional[bool] = False

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    is_admin: bool
    # created_at: datetime # Add if needed, ensure datetime is handled

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    roles: Optional[List[str]] = []


class WellInput(BaseModel):
    well_name: str
    field_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ProductionDataInput(BaseModel):
    timestamp: str # Assuming ISO format string e.g. "2023-01-01T10:00:00Z"
    oil_rate: Optional[float] = None
    gas_rate: Optional[float] = None
    water_rate: Optional[float] = None
    pressure: Optional[float] = None

class MultiProductionDataInput(BaseModel):
    well_name: str
    data: List[ProductionDataInput]

class DeclineParams(BaseModel):
    time: List[float]
    rate: List[float]
    # p0_exp, p0_hyp, p0_harm could be added if user wants to provide initial guesses

class PredictPayload(BaseModel):
    model_name: Optional[str] = None # e.g. 'xgboost'
    features: List[Dict[str, Any]] # List of feature dicts, e.g. [{'f1': v1, 'f2': v2}, ...]


# --- Helper Functions ---
async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Dependency to get current user from token."""
    payload = auth_manager.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # 'sub' typically holds username, but we stored more in token_data
    token_data = TokenData(
        username=payload.get("sub"),
        user_id=payload.get("user_id"),
        roles=payload.get("roles", [])
    )
    if token_data.username is None or token_data.user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Could also check if user exists in DB and is active here
    return token_data

async def get_current_active_admin(current_user: TokenData = Depends(get_current_user)):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Not enough permissions. Admin required.")
    return current_user


# --- API Endpoints ---

@app.on_event("startup")
async def startup_event():
    # You can place database connection logic here if you want it managed by FastAPI's lifespan
    if not db_manager.connect(ensure_db_exists=True): # ensure_db_exists might be slow for startup
        print("Warning: Main DB connection failed on startup.")
    # Auth DB connection is handled by AuthManager's __init__ or methods
    # No explicit call needed here unless you change AuthManager
    print("FastAPI application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    db_manager.close()
    auth_manager.close_db_connection()
    print("FastAPI application shutdown complete.")

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_auth_info = auth_manager.authenticate_user(form_data.username, form_data.password)
    if not user_auth_info:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_payload = {
        "sub": user_auth_info["username"],
        "user_id": user_auth_info["user_id"],
        "roles": ["user"] # Base role
    }
    if user_auth_info.get("is_admin"):
        token_payload["roles"].append("admin")

    access_token = auth_manager.create_access_token(data=token_payload)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/create", response_model=UserResponse, status_code=201)
async def create_new_user(user_in: UserCreate, admin_user: TokenData = Depends(get_current_active_admin) ): # Example: only admin can create users
    # In a public scenario, this might not need admin rights or use a different flow (e.g. email verification)
    db_user = auth_manager.get_user_by_username(user_in.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    # Check email too if desired. AuthManager's create_user handles this via DB unique constraints.

    created_user = auth_manager.create_user(
        username=user_in.username,
        email=user_in.email,
        password=user_in.password,
        is_admin=user_in.is_admin
    )
    if not created_user:
        raise HTTPException(status_code=500, detail="Could not create user.")
    return UserResponse(**created_user) # Map dict to Pydantic model

@app.get("/users/me", response_model=TokenData)
async def read_users_me(current_user: TokenData = Depends(get_current_user)):
    return current_user


# --- Data Management Endpoints (Example) ---
# Initialize DataUploader (could be request-scoped or singleton)
data_uploader = DataUploader()

@app.post("/data/upload_well_csvs/{well_name}", summary="Upload CSV files for a well")
async def upload_well_csv_data(
    well_name: str,
    files: List[UploadFile] = File(...),
    current_user: TokenData = Depends(get_current_user)
):
    # This is a simplified example. In production, save files to a temp location first.
    # data_uploader.load_well_data expects file paths.
    # For this example, we'll assume it can take file-like objects or content.
    # This part needs careful implementation for security and efficiency.

    # Let's simulate saving and then loading (NOT PRODUCTION READY)
    temp_file_paths = []
    for file in files:
        temp_path = f"temp_{well_name}_{file.filename}" # Highly insecure, just for structure
        try:
            with open(temp_path, "wb") as buffer:
                buffer.write(await file.read())
            temp_file_paths.append(temp_path)
        except Exception as e:
            # Clean up already saved temp files if one fails
            for p in temp_file_paths: os.remove(p)
            raise HTTPException(status_code=500, detail=f"Could not process file {file.filename}: {e}")

    try:
        data_uploader.load_well_data(well_name, temp_file_paths)
        preview = data_uploader.get_data_preview(well_name, n_rows=5) # Get a small preview
        # Clean up temp files
        for p in temp_file_paths: os.remove(p)
        return {"message": f"Data for well '{well_name}' loaded from {len(files)} files.", "preview_head": preview.to_dict()}
    except ValueError as ve:
        for p in temp_file_paths: os.remove(p)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        for p in temp_file_paths: os.remove(p)
        raise HTTPException(status_code=500, detail=f"Error during data processing: {e}")


@app.get("/data/preview/{well_name}", summary="Get data preview for a well")
async def get_well_data_preview(well_name: str, n_rows: int = 5, current_user: TokenData = Depends(get_current_user)):
    try:
        preview_df = data_uploader.get_data_preview(well_name, n_rows)
        return preview_df.to_dict(orient="records")
    except ValueError as e: # e.g. well not found in uploader
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/data/statistics/{well_name}", summary="Get statistics for a well's data")
async def get_well_data_stats(well_name: str, current_user: TokenData = Depends(get_current_user)):
    try:
        stats_df = data_uploader.get_well_statistics(well_name)
        return stats_df.to_dict() # describe() output can be complex, adjust as needed
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- Decline Curve Analysis Endpoints (Example) ---
@app.post("/analysis/decline_curve", summary="Fit decline curve models")
async def fit_decline_models(params: DeclineParams, current_user: TokenData = Depends(get_current_user)):
    try:
        dca = AdvancedDeclineAnalysis(time=np.array(params.time), rate=np.array(params.rate))
        dca.fit_models() # Using default initial guesses

        # Prepare results for JSON response
        fitted_params = {k: v for k, v in dca.params.items() if v is not None} # Filter out None if fit failed
        if not fitted_params:
            return {"message": "Could not fit any decline models to the provided data.", "fitted_parameters": {}}

        return {"message": "Decline models fitted.", "fitted_parameters": fitted_params}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during decline analysis: {e}")


# --- AI Prediction Endpoints (Example) ---
# Global AI predictor instance (or manage scope appropriately)
# This instance will hold trained models. For a stateless API, models might be loaded per request.
# For simplicity, one instance. This implies models are trained & kept in memory.
ai_predictor = AIPrediction()

@app.post("/ai/train_models", summary="Train AI prediction models (conceptual)")
async def train_ai_models_endpoint(
    # This endpoint would need data. How is it provided? From DB? From DataUploader?
    # For now, let's assume it's a conceptual trigger and data source is implicit.
    # A real endpoint would take DataFrame-like JSON or pointers to data.
    target_column: str = Body("target"),
    feature_columns: List[str] = Body(["feature1", "feature2"]),
    # Example: Use data from a specific well loaded in DataUploader
    source_well_name: Optional[str] = Body(None, description="Well name from DataUploader to use for training data"),
    current_user: TokenData = Depends(get_current_user)
):
    if not source_well_name:
        raise HTTPException(status_code=400, detail="source_well_name must be provided to fetch training data.")

    try:
        training_df = data_uploader.well_data.get(source_well_name)
        if training_df is None or training_df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for well '{source_well_name}' in DataUploader.")

        X_train, X_test, y_train, y_test = ai_predictor.prepare_data(
            training_df, target_column, feature_columns
        )
        ai_predictor.train_models(X_train, y_train, X_test, y_test, hyperparam_tuning=False) # Keep tuning light for API

        return {
            "message": "AI models training initiated/completed.",
            "trained_models": list(ai_predictor.trained_models.keys()),
            "performance": ai_predictor.performance_metrics
        }
    except KeyError as ke: # If well_data[source_well_name] doesn't exist
        raise HTTPException(status_code=404, detail=f"Data for source well '{source_well_name}' not loaded or prepared.")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during AI model training: {str(e)}")


@app.post("/ai/predict", summary="Make predictions using a trained AI model")
async def predict_with_ai_model(payload: PredictPayload, current_user: TokenData = Depends(get_current_user)):
    if not ai_predictor.trained_models:
        raise HTTPException(status_code=400, detail="No AI models are currently trained. Train models first.")

    try:
        # Convert list of dicts to DataFrame for prediction
        features_df = pd.DataFrame(payload.features)
        # Note: The AIPrediction class's predict method expects X_new to be scaled if training data was scaled.
        # This implies that the client sending /ai/predict requests must know the feature names and structure.
        # The `AIPrediction.predict` method internally handles scaling if a scaler was saved.
        predictions = ai_predictor.predict(features_df, model_name=payload.model_name)
        return {"predictions": predictions.tolist()} # Convert numpy array to list for JSON
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re: # e.g. "No models have been trained yet."
        raise HTTPException(status_code=400, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during AI prediction: {str(e)}")


# --- Database Interaction Endpoints (Example) ---
@app.post("/db/wells", summary="Add a new well to the database", status_code=201)
async def add_well_to_db(well_input: WellInput, current_user: TokenData = Depends(get_current_user)):
    if not db_manager.conn: # Ensure connection
        if not db_manager.connect():
            raise HTTPException(status_code=503, detail="Database service unavailable.")

    well_id = db_manager.insert_well(
        well_name=well_input.well_name,
        field_name=well_input.field_name,
        latitude=well_input.latitude,
        longitude=well_input.longitude
    )
    if well_id is None:
        # This could be due to conflict (already exists) or actual error.
        # The DatabaseManager's insert_well tries to return existing ID on conflict.
        # If it's truly None, it might be an actual DB error.
        existing_id = db_manager.get_well_id_by_name(well_input.well_name)
        if existing_id:
             return {"message": f"Well '{well_input.well_name}' already exists with ID {existing_id}.", "well_id": existing_id, "status": "existed"}
        raise HTTPException(status_code=500, detail=f"Failed to insert well '{well_input.well_name}' into database.")
    return {"message": f"Well '{well_input.well_name}' added/found with ID {well_id}.", "well_id": well_id, "status": "created_or_found"}

@app.post("/db/production_data", summary="Add production data for a well")
async def add_production_data_to_db(payload: MultiProductionDataInput, current_user: TokenData = Depends(get_current_user)):
    if not db_manager.conn:
        if not db_manager.connect():
            raise HTTPException(status_code=503, detail="Database service unavailable.")

    well_id = db_manager.get_well_id_by_name(payload.well_name)
    if not well_id:
        raise HTTPException(status_code=404, detail=f"Well '{payload.well_name}' not found in database. Add well first.")

    # Convert Pydantic models to list of dicts for DatabaseManager
    data_to_insert = [item.model_dump() for item in payload.data]

    success = db_manager.insert_production_data(well_id, data_to_insert)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to insert production data for well '{payload.well_name}'.")
    return {"message": f"Production data for well '{payload.well_name}' ({len(data_to_insert)} records) processed."}

@app.get("/db/wells/{well_name}/data", summary="Get production data for a well from DB")
async def get_well_production_data_from_db(
    well_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user)
):
    if not db_manager.conn:
        if not db_manager.connect():
            raise HTTPException(status_code=503, detail="Database service unavailable.")

    data_df = db_manager.get_well_data(well_name, start_date, end_date)
    if data_df is None: # Could mean well not found or DB error
        raise HTTPException(status_code=404, detail=f"Could not retrieve data for well '{well_name}'. Check if well exists or logs for DB errors.")
    if data_df.empty:
        return {"message": f"No production data found for well '{well_name}' within the specified criteria.", "data": []}

    # Convert Timestamps to ISO format strings for JSON compatibility
    for col in data_df.select_dtypes(include=['datetime64[ns, UTC]', 'datetime64[ns]']).columns:
        data_df[col] = data_df[col].dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    return data_df.to_dict(orient="records")


# --- Root Endpoint ---
@app.get("/")
async def root():
    return {"message": "Welcome to the PetroLúmen Backend API. Refer to /docs for API documentation."}


# To run this application (save as backend/main.py):
# 1. Ensure all dependencies are installed (fastapi, uvicorn, pydantic, psycopg2-binary, pyjwt, pandas, numpy, scikit-learn, xgboost, joblib, werkzeug, python-multipart for forms/files)
#    Create a requirements.txt and pip install -r requirements.txt
# 2. Navigate to the 'backend' directory in your terminal.
# 3. Run Uvicorn: uvicorn main:app --reload
#    (This assumes your file is named main.py and your FastAPI instance is 'app')
# 4. Access the API at http://127.0.0.1:8000 and docs at http://127.0.0.1:8000/docs

# Note: This is a structural example. Error handling, logging, configuration management,
# security hardening, and detailed business logic for each endpoint would need significant expansion
# for a production application. For instance, the DataUploader and AIPredictor instances are global here;
# in a larger app, their lifecycle and state management (especially for trained models) would need careful design
# (e.g., using FastAPI dependencies for request-scoped instances or a more robust model registry).
```
