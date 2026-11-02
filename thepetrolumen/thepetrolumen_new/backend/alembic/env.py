from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line reads the loggers section in your alembic.ini file.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add the 'backend' directory to sys.path to allow importing from gaia_genesis_new
# This assumes alembic commands are run from the project root or 'backend/' directory.
# Adjust if your project structure or execution context is different.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import your application's settings and Base model
# This is where Alembic will find your SQLAlchemy models.
try:
    # When env.py is run, sys.path already includes backend/ (added above).
    # So, import directly from modules within backend/.
    from config import settings
    from gaia_genesis.core.database_models import Base

    target_metadata = Base.metadata
except ImportError as e:
    sys.stderr.write(f"Error importing application modules in env.py: {e}\n")
    # Adding more debug info
    # import sys # sys is already imported at the top

    sys.stderr.write(f"Current sys.path: {sys.path}\n")
    sys.stderr.write(
        "Ensure backend modules are in PYTHONPATH or alembic is run from "
        "project root.\n"
    )
    sys.exit(1)


def get_db_url():
    """
    Returns the database URL from the application's settings.
    This ensures Alembic uses the same database URL as the application,
    respecting env vars and dynamic path resolution.
    """
    db_url_str = settings.DATABASE_URL

    if db_url_str.startswith("sqlite:///"):
        db_file_part = db_url_str.split("sqlite:///", 1)[1]

        # If the path starts with './', it's relative to the backend directory.
        # Example: "sqlite:///./default_app_data.db" -> "backend/default_app_data.db"
        if db_file_part.startswith("./"):
            # backend_dir is the absolute path to the 'backend' directory
            backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            # Remove './' and join with backend_dir
            absolute_db_path = os.path.join(backend_dir, db_file_part.lstrip("./"))
            # It's good practice to normalize the path
            absolute_db_path = os.path.normpath(absolute_db_path)
            return f"sqlite:///{absolute_db_path}"

        # If it's "sqlite:///file.db" (no leading './' and not absolute)
        # it implies relative to CWD. For Alembic, this means relative to where
        # the `alembic` command is run. If run from `backend/`, this is fine.
        # If it's already an absolute path like "sqlite:////path/to/file.db", it's also fine.
        # No change needed for these cases, SQLAlchemy handles them.

    # For non-SQLite URLs or absolute SQLite paths, return as is.
    return db_url_str


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available for this.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_db_url()  # Use our dynamic URL function
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Compare types when generating migrations
        compare_server_default=True,  # Compare server defaults
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get the database URL from our settings
    db_url = get_db_url()

    # Create a configuration dictionary for engine_from_config
    # Overwrite sqlalchemy.url from alembic.ini with our dynamic URL
    engine_config = config.get_section(config.config_ini_section, {})
    engine_config["sqlalchemy.url"] = db_url

    connectable = engine_from_config(
        engine_config,  # Use the modified config
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            # include_schemas=True # Uncomment if you use multiple schemas
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
