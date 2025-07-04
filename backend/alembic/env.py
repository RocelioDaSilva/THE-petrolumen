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
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your application's settings and Base model
# This is where Alembic will find your SQLAlchemy models.
try:
    from backend.gaia_genesis_new.config import settings
    from backend.gaia_genesis_new.core.database_models import Base
    target_metadata = Base.metadata
except ImportError as e:
    sys.stderr.write(f"Error importing application modules in env.py: {e}\n")
    sys.stderr.write("Ensure backend modules are in PYTHONPATH or alembic is run from project root.\n")
    sys.exit(1)


def get_db_url():
    """
    Returns the database URL from the application's settings.
    This ensures Alembic uses the same database URL as the application,
    respecting environment variables and dynamic path resolution.
    """
    db_path = settings.DB_PATH
    if str(db_path).startswith("postgresql") or str(db_path).startswith("mysql"):
        return str(db_path)
    else: # Assume SQLite
        # Ensure the path is absolute for SQLite
        return f"sqlite:///{db_path.resolve()}"

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_db_url() # Use our dynamic URL function
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True, # Compare types when generating migrations
        compare_server_default=True # Compare server defaults
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
        engine_config, # Use the modified config
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
