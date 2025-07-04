import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session # Though not directly used here, often in Depends

# --- Dynamic Path Setup for Imports ---
# This ensures that modules can be found when running main.py directly
# or when run by Uvicorn from the project root.
# Assuming main.py is in backend/gaia_genesis_new/
# We want 'backend' and the project root (one level above 'backend') to be in sys.path.

# Path to the 'backend' directory
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Path to the project root (directory containing 'backend')
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- Core Application Imports ---
# These imports should now work more reliably due to the path setup above.
from backend.database import initialize_database_schema, get_db # get_db will be used by endpoint dependencies
from backend.gaia_genesis_new.config import settings
from backend.gaia_genesis_new.logger import logger
from backend.gaia_genesis_new.api_v1.routers import health, reservoirs, wells, production
# PVT router - assuming it will be created in the pvt phase
from backend.gaia_genesis_new.api_v1.routers import pvt as pvt_router

# Initialize FastAPI app
app = FastAPI(
    title="Petrolúmen Reservoir Engineering Suite API",
    version=getattr(settings, 'APP_VERSION', "0.1.0"), # Safely get version from settings
    description="Backend API for the Petrolúmen desktop application, providing data management and calculation services for reservoir engineering.",
    openapi_url="/api/v1/openapi.json" # Standard OpenAPI path for documentation
)

# CORS Configuration
# Define allowed origins for Cross-Origin Resource Sharing
origins = [
    "http://localhost",       # General local development
    "http://localhost:3000",  # Default Next.js dev server port
    "tauri://localhost",      # Tauri application protocol
    "app://localhost",        # Another possible Tauri protocol if custom
    # Add production frontend URL if deployed separately and known
    # e.g., "https://www.petrolumen.com"
]

if settings.DEBUG_MODE:
    logger.warning("DEBUG_MODE is True. CORS middleware will allow all origins for easier development. This should NOT be used in production.")
    # In development, allowing all origins can simplify setup with various tools.
    # However, for production, this list MUST be restrictive.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # Allows all origins
        allow_credentials=True,
        allow_methods=["*"], # Allows all standard HTTP methods
        allow_headers=["*"], # Allows all headers
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins, # Use the specific list for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- Event Handlers ---
@app.on_event("startup")
async def on_startup():
    logger.info(f"Application startup... ENV: {settings.ENV}, DEBUG: {settings.DEBUG_MODE}")
    try:
        logger.info(f"Initializing database schema. DB_PATH used by settings: {settings.DB_PATH}")
        initialize_database_schema() # This function should run Alembic migrations
        logger.info("Database schema initialization/update process completed.")
    except Exception as e:
        logger.critical(f"DATABASE SCHEMA INITIALIZATION FAILED: {e}", exc_info=True)
        # Consider if the application should exit or run in a degraded state if DB init fails.

    # Initialize PVTService and potentially default models
    try:
        # Assuming PVTService is correctly placed and importable
        from backend.gaia_genesis_new.pvt.service import PVTService
        pvt_service_instance = PVTService() # This instance is local to startup, not stored on app state unless designed to

        # Example: Create a default black oil model if it doesn't exist (in-memory for now)
        default_blackoil_data = {
            "pb": 2500, "co": 1.8e-5, "rsb": 750, "bob": 1.42,
            "muob": 0.85, "muod": 3.2, "cg": 3.2e-4,
            "gamma_g": 0.78, "gamma_o": 0.86, "temperature": 180
        }
        # This will (re)create the model in the PVTService's in-memory dictionary each time.
        # For persistent models, PVTService would need to interact with DataManager.
        pvt_service_instance.create_black_oil_model("default_blackoil", default_blackoil_data)
        logger.info("Default black oil PVT model 'default_blackoil' (re)created in PVTService.")
    except ImportError:
        logger.warning("PVTService or its dependencies not found. Skipping PVT default model creation.")
    except Exception as e:
        logger.error(f"Error creating default PVT model during startup: {e}", exc_info=True)

    logger.info("Application startup complete.")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Application shutdown...")
    # Add any cleanup tasks, like closing external connections if necessary
    logger.info("Application shutdown complete.")

# --- API Routers ---
API_PREFIX = "/api/v1" # Define a common prefix for all v1 APIs

app.include_router(health.router, prefix=API_PREFIX, tags=["System"])
app.include_router(reservoirs.router, prefix=f"{API_PREFIX}/reservoirs", tags=["Reservoirs"])
app.include_router(wells.router, prefix=f"{API_PREFIX}/wells", tags=["Wells"])
app.include_router(production.router, prefix=f"{API_PREFIX}/production", tags=["Production Data"])
# When simulations router is ready:
# from backend.gaia_genesis_new.api_v1.routers import simulations
# app.include_router(simulations.router, prefix=f"{API_PREFIX}/simulations", tags=["Simulations"])

# Include the PVT router
app.include_router(pvt_router.router, prefix=f"{API_PREFIX}/pvt", tags=["PVT Analysis"])


# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    """Provides basic information about the API and links to documentation."""
    return {
        "message": f"Welcome to the Petrolúmen API (Version: {app.version})",
        "docs_url": app.docs_url or "/docs", # Default FastAPI docs URL
        "openapi_url": app.openapi_url,
        "health_url": f"{API_PREFIX}/health"
    }

# --- Main execution (for development using `python backend/gaia_genesis_new/main.py`) ---
# This block allows running the FastAPI app directly with Python for development.
# For production, Uvicorn should be run as a separate process, e.g., by a process manager or the Tauri sidecar.
if __name__ == "__main__":
    import uvicorn

    logger.info(f"Attempting to start Uvicorn development server on {settings.API_HOST}:{settings.API_PORT}")

    # The app string for Uvicorn should be 'module_name:app_instance_name'
    # If this main.py is run directly, its module name is '__main__'.
    # Uvicorn expects a module path.
    # A common way to run for development is:
    # uvicorn backend.gaia_genesis_new.main:app --reload --host <host> --port <port>
    # from the project root.
    # This __main__ block tries to achieve similar for direct `python <this_file>.py`

    # To make `python backend/gaia_genesis_new/main.py` work from project root:
    # Uvicorn needs to find 'main:app' within the 'backend.gaia_genesis_new' module context.
    # The sys.path manipulation at the top helps Python find 'backend.gaia_genesis_new'.
    # The string "main:app" assumes uvicorn is run with CWD as `backend/gaia_genesis_new`
    # or that `backend.gaia_genesis_new` is in path and `main` is the module.
    # For maximum robustness when running this file directly:
    app_module_path = "backend.gaia_genesis_new.main:app"

    uvicorn.run(
        app_module_path,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG_MODE, # Enable auto-reload in debug mode
        log_level="debug" if settings.DEBUG_MODE else "info"
    )
