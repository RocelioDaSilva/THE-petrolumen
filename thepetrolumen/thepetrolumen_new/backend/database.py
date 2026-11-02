from pathlib import Path  # Ensure Path is imported
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging  # Use standard logging

# Imports from local packages (assuming backend/ is in PYTHONPATH)
from config import settings

logger = logging.getLogger(__name__)

# DATABASE_URL is now directly from settings
DATABASE_URL = settings.DATABASE_URL
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

logger.info(f"Database URL determined as: {DATABASE_URL}")

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for declarative models is in gaia_genesis.core.database_models
# It's not directly used here but good to note.


def initialize_database_schema():
    """
    Initializes the database schema using Alembic.
    This should be called once on application startup.
    """
    logger.info(f"Checking database schema using DATABASE_URL: {DATABASE_URL}...")

    try:
        from alembic.config import Config
        from alembic import command

        # Construct the absolute path to alembic.ini
        # This database.py is in backend/, alembic.ini is also in backend/
        alembic_ini_path = Path(__file__).resolve().parent / "alembic.ini"

        if not alembic_ini_path.exists():
            logger.error(
                f"Alembic config file not found at {alembic_ini_path}. "
                "Cannot run migrations."
            )
            # Potentially raise an error or exit if migrations are critical for startup
            return

        logger.info(f"Using Alembic config from: {alembic_ini_path}")
        alembic_cfg = Config(str(alembic_ini_path))

        # Override sqlalchemy.url from alembic.ini with the one from our settings,
        # ensuring it's correctly resolved (especially for SQLite absolute paths from
        # env.py logic). The get_db_url() in env.py should handle this, but
        # explicitly setting it here for the Config object ensures this script uses
        # the right DB if used standalone. However, `command.upgrade` using this
        # `alembic_cfg` will trigger `env.py` which itself calls `get_db_url()`.
        # So, this explicit set_main_option here might be redundant if env.py is
        # robust, but doesn't hurt.
        alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)

        logger.info("Applying Alembic migrations to 'head'...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database schema initialization/update complete.")

    except ImportError:
        logger.error("Alembic is not installed or not found. Cannot run migrations.")
    except Exception as e:
        logger.error(
            f"An error occurred during database schema initialization: {e}",
            exc_info=True,
        )


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
# However, the refined `backend/gaia_genesis_new/config.py` already ensures DB path
# and dir. The `run_migrations()` in the previous version of `database.py` (if that's
# what you mean) is now better handled by `initialize_database_schema` being
# explicitly called at startup.

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
