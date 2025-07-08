from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Core Application Settings ---
    APP_NAME: str = "PetroLúmen Backend API"
    APP_VERSION: str = "0.3.0"  # Example version bump
    LOG_LEVEL: str = "INFO"

    # --- Database Settings ---
    DATABASE_URL: str = "sqlite:///./default_app_data.db"
    # For async database (if used in future, e.g. with asyncpg for PostgreSQL)
    # ASYNC_DATABASE_URL: Optional[str] = None

    # --- Security / JWT Settings ---
    # IMPORTANT: This is a default placeholder and MUST be changed in production.
    # Generate a strong, random key and set it via .env file or environment variable.
    # Example: openssl rand -hex 32
    SECRET_KEY: str = "!!!DEFAULT_PLACEHOLDER_SECRET_KEY_CHANGE_ME!!!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_ALGORITHM: str = "HS256"

    # --- CORS Settings (example, if needed later) ---
    # CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    # # Frontend, etc.
    # CORS_ALLOW_CREDENTIALS: bool = True
    # CORS_ALLOW_METHODS: list[str] = ["*"]
    # CORS_ALLOW_HEADERS: list[str] = ["*"]

    # --- Reservoir Engineering Tools Paths (example, if models/data are outside DB) ---
    # DCA_MODELS_PATH: str = "./reservoir_models/dca/"
    # SIMULATION_OUTPUT_PATH: str = "./simulation_output/"
    # Directory for saving/loading AI models
    AI_MODELS_DIR: str = "./trained_ai_models"

    # Pydantic settings configuration
    # This tells Pydantic to load .env files.
    # By default, it looks for a file named ".env".
    # You can specify a different path:
    # model_config = SettingsConfigDict(env_file=".env_prod")
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Create a single instance of the settings to be imported by other modules
settings = Settings()

# Example of how to use it:
if __name__ == "__main__":
    print("App Name:", settings.APP_NAME)
    print("Database URL:", settings.DATABASE_URL)
    print("Secret Key:", settings.SECRET_KEY)  # Be careful printing secrets
    print("AI Models Dir:", settings.AI_MODELS_DIR)
    # To test .env file loading:
    # Create a .env file in the same directory as this config.py with, e.g.:
    # DATABASE_URL="postgresql://user:pass@host/db"
    # SECRET_KEY="my_super_secret_from_env"
    # Then run `python config.py`
    # Note: python-dotenv's load_dotenv() might still be useful if called early in
    # main.py, especially before Pydantic tries to load. Pydantic-settings handles
    # .env loading internally.
    # If python-dotenv is used, it loads into os.environ, and Pydantic then reads
    # from os.environ. So, ensure load_dotenv() in main.py runs before this
    # settings object is created/imported if relying on that.
    # Or, rely solely on Pydantic's env_file mechanism.
    # For this project, main.py already calls load_dotenv().
    # Pydantic BaseSettings will prioritize environment variables over .env file
    # values if both exist. Then .env file values over default values in the class.
    # The `extra='ignore'` means Pydantic won't raise an error for extra fields in
    # the .env file.
    # `env_prefix` could be used if your env vars are prefixed, e.g.,
    # `APP_DATABASE_URL`.
    # `case_sensitive=False` is default for env vars.

    # Verify that .env loading works if a .env file is present
    # (Requires python-dotenv to be installed for pydantic-settings's .env support,
    # which it is)
    from dotenv import load_dotenv

    load_dotenv()  # Explicitly load for this test, or ensure pydantic handles it

    test_settings_after_dotenv = (
        Settings()
    )  # Re-instantiate to see if .env was picked up
    print("\nAfter potential .env load:")
    print("Database URL:", test_settings_after_dotenv.DATABASE_URL)
    print("Secret Key:", test_settings_after_dotenv.SECRET_KEY)

    # The MODELS_DIR in main.py should also use this settings.AI_MODELS_DIR
    # The default SECRET_KEY here is different and longer than the one previously
    # in main.py to demonstrate it's coming from this config.
    # The default DATABASE_URL is also slightly different.
    # The `APP_VERSION` could be used in FastAPI app definition.
    # `LOG_LEVEL` could be used to configure logging.
    # `JWT_ALGORITHM` is already defined in api.py, can be centralized here.
