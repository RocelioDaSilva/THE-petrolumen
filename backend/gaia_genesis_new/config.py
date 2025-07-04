import os
import platform
from pathlib import Path
from pydantic import BaseSettings, Field, validator

class Settings(BaseSettings):
    # Application Environment
    # TAURI_ENV is expected to be set by the Tauri sidecar in production.
    # It defaults to "development" if not set.
    ENV: str = Field("development", env="TAURI_ENV")

    # Database Path
    # This will be dynamically set based on ENV or explicit DATABASE_URL from .env
    DB_PATH: Path = Field(None) # Will be initialized in __init__ or __post_init__

    # API Configuration (can be overridden by .env file)
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    # Development/Debug Mode (can be overridden by .env file)
    DEBUG_MODE: bool = True

    # Security (MUST be overridden by .env file in production)
    SECRET_KEY: str = "a_very_default_secret_key_please_change"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Example of other potential settings
    # DATA_CACHE_DIR: Path = Path("./data_cache") # Needs to be resolved relative to a base path
    # SIMULATION_MAX_WORKERS: int = 4

    class Config:
        env_file = ".env" # Load .env file if present in the working directory of the backend
        env_file_encoding = "utf-8"
        # Allow extra fields not defined in Settings to be ignored
        extra = "ignore"


    # Using __init__ to set DB_PATH because it might depend on ENV
    # which is loaded from environment variables by Pydantic before __init__.
    # Alternatively, a @validator for DB_PATH with always=True could also work.
    def __init__(self, **values: any):
        super().__init__(**values)

        # Determine DB_PATH if not explicitly set by DATABASE_URL in .env
        # and not already populated (e.g. by direct instantiation for tests)
        if self.DB_PATH is None:
            # Check if DATABASE_URL was loaded from .env by Pydantic
            # Pydantic loads .env variables into the initial `values` dict for __init__
            env_db_url = values.get("DATABASE_URL") # Pydantic v1
            if not env_db_url and hasattr(self, '_extra') and self._extra: # Pydantic v2 stores extras differently
                 env_db_url = self._extra.get("DATABASE_URL")


            if env_db_url and env_db_url.startswith("sqlite:///"):
                # Use path from DATABASE_URL if it's a SQLite connection string
                self.DB_PATH = Path(env_db_url.replace("sqlite:///", ""))
            elif self.ENV == "production":
                # Production: Use platform-specific app data directories
                # This path should ideally be created by the Tauri sidecar
                # and the sidecar should pass the DATABASE_URL env var.
                if platform.system() == "Windows":
                    base = Path(os.getenv('APPDATA', Path.home() / "AppData" / "Roaming"))
                elif platform.system() == "Darwin": # macOS
                    base = Path.home() / "Library" / "Application Support"
                else:  # Linux/Unix
                    base = Path.home() / ".config"
                self.DB_PATH = base / "Petrolumen" / "database.db" # App-specific subdirectory
            else:
                # Development: Default to a local file in the backend directory
                # This assumes backend/ is the current working directory or config.py is there.
                # For more robustness, resolve relative to this config file's location.
                self.DB_PATH = Path(__file__).resolve().parent.parent / "reservoir_data_dev.db"

        # Ensure the directory for the database exists
        if self.DB_PATH:
            self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Instantiate settings
settings = Settings()

# To use in other modules:
# from backend.gaia_genesis_new.config import settings
# print(settings.DB_PATH)
# print(settings.API_HOST)
