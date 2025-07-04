import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session # Added Session for type hinting
from backend.gaia_genesis_new.config import settings # Use the centralized settings
from backend.gaia_genesis_new.logger import logger

# DATABASE_URL is now primarily determined by settings.DB_PATH
# The structure f"sqlite:///{settings.DB_PATH}" is for SQLite.
# If using other databases, settings.DB_PATH would need to be the full URL.
# For SQLite, settings.DB_PATH is the absolute file path.

if str(settings.DB_PATH).startswith("postgresql") or str(settings.DB_PATH).startswith("mysql"):
    DATABASE_URL = str(settings.DB_PATH)
    connect_args = {}
else: # Assume SQLite
    DATABASE_URL = f"sqlite:///{settings.DB_PATH.resolve()}"
    connect_args = {"check_same_thread": False}


logger.info(f"Database URL determined as: {DATABASE_URL} (from settings.DB_PATH: {settings.DB_PATH})")

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for declarative models is now in core.database_models
# from backend.gaia_genesis_new.core.database_models import Base

def initialize_database_schema():
    """
    Initializes the database schema using Alembic.
    This should be called once on application startup if the database
    might not exist or migrations might not be applied.
    """
    logger.info(f"Checking database schema at {settings.DB_PATH}...")

    # Ensure the database file and its directory exist (handled by config.py on settings instantiation)
    # settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    # if not settings.DB_PATH.exists():
    #     logger.info(f"Database file not found at {settings.DB_PATH}, creating an empty one.")
    #     settings.DB_PATH.touch() # Create empty file for Alembic to connect to

    try:
        from alembic.config import Config
        from alembic import command

        # Construct the absolute path to alembic.ini
        # Assuming this database.py is in backend/ and alembic.ini is in backend/
        alembic_ini_path = Path(__file__).resolve().parent / "alembic.ini"
        logger.info(f"Using Alembic config from: {alembic_ini_path}")

        alembic_cfg = Config(str(alembic_ini_path))

        # Crucially, tell Alembic where the actual database is, overriding alembic.ini's default
        alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)

        logger.info("Applying Alembic migrations to 'head'...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database schema initialization/update complete.")

    except ImportError:
        logger.error("Alembic is not installed or not found. Cannot run migrations.")
        # Fallback: create tables directly from models (not recommended if using Alembic)
        # from backend.gaia_genesis_new.core.database_models import Base
        # logger.info("Alembic not found. Attempting to create tables directly from models (not recommended).")
        # Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.error(f"An error occurred during database schema initialization: {e}")
        # Depending on the error, you might want to raise it or handle it
        # For example, if alembic.ini is not found, the app might not be able to start

# Dependency for FastAPI to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Example of how this might be called at startup in main.py:
# from .database import initialize_database_schema
# initialize_database_schema()
# However, the refined `backend/gaia_genesis_new/config.py` already ensures DB path and dir.
# The `run_migrations()` in the previous version of `database.py` (if that's what you mean)
# is now better handled by `initialize_database_schema` being explicitly called at startup.

# For the purpose of this file, its main roles are:
# 1. Set up `engine` and `SessionLocal` based on `settings`.
# 2. Provide `get_db` dependency.
# 3. Provide `initialize_database_schema` utility.

# Note: The execution of `initialize_database_schema()` should be explicitly
# called from the main application startup logic (e.g., in main.py's startup event)
# rather than being run automatically on import of this database.py module,
# to ensure settings are fully loaded and to control when migrations run.
# The previous `initialize_database()` that was run on import is now effectively
# replaced by the logic in `settings = Settings()` for path creation, and this
# `initialize_database_schema()` for running migrations.

from pathlib import Path # Ensure Path is imported if used above. This was missing.
