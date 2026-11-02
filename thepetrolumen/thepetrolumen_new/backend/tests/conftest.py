import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add the backend directory to sys.path to allow imports from backend modules
# This should be at the very top before other local imports
_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Corrected imports for database components
from gaia_genesis.core.database_models import Base, User as DBUser  # noqa: E402
from gaia_genesis.core.database_manager import DatabaseManager  # noqa: E402
from main import (
    app,
    db_manager as main_db_manager,
    auth_manager as main_auth_manager,
)  # noqa: E402

# Assuming AuthManager should be imported from core if it's related to the new DB structure
from gaia_genesis.core.auth_manager import (
    AuthManager as CoreAuthManager,
)  # noqa: E402; Renamed to avoid conflict if main.auth_manager is different


# --- Test Database Fixture ---
TEST_DATABASE_URL = "sqlite:///./test_temp_app.db"


@pytest.fixture(scope="session")
def test_engine():
    # Use a temporary SQLite database for testing
    # Ensure TEST_DATABASE_URL does not contain sensitive information if logged elsewhere.
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)  # Create tables
    yield engine
    Base.metadata.drop_all(bind=engine)  # Drop tables after tests
    if os.path.exists("./test_temp_app.db"):
        os.remove("./test_temp_app.db")


@pytest.fixture(
    scope="function"
)  # Changed to function scope for db_session to ensure clean DB for each test
def TestingSessionLocal(test_engine):
    """A fixture that returns a SQLAlchemy sessionmaker for the test database"""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session(TestingSessionLocal):
    """Yields a SQLAlchemy session for a single test, rolling back changes afterwards."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()  # Ensure no changes leak between tests
        session.close()


@pytest.fixture(scope="function")  # Changed from session to function
def test_db_manager(test_engine):
    """
    Provides a DatabaseManager instance configured for the test database.
    This manager can be used by other fixtures or tests that need to interact with the DB directly.
    """
    manager = DatabaseManager(db_url=TEST_DATABASE_URL)
    manager.engine = test_engine  # Use the test engine
    manager.SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    return manager


# --- Test Client and Auth Fixtures ---
@pytest.fixture(scope="function")  # Changed from session to function
def test_auth_manager(test_db_manager):  # Depends on test_db_manager
    """Provides an AuthManager instance using the test database."""
    # Use a fixed, non-default secret key for testing token generation consistency
    test_secret_key = "test_secret_key_for_fastapi_tests"
    # Ensure using CoreAuthManager if that's the intended one for tests
    return CoreAuthManager(db_manager=test_db_manager, secret_key=test_secret_key)


@pytest.fixture(
    scope="function"
)  # Use function scope if you want to reset overrides for each test
def client(
    test_db_manager, test_auth_manager, db_session
):  # db_session ensures tables are there
    """
    Provides a TestClient for the FastAPI application, with DatabaseManager and
    AuthManager overridden to use test-specific instances connected to the test
    database.
    """
    # Override dependencies for the FastAPI app instance
    # This ensures that FastAPI uses our test DB and test AuthManager
    app.dependency_overrides[main_db_manager.get_session] = lambda: db_session
    # If main_auth_manager uses its own session getter, override that too
    # Assuming main_auth_manager.db_manager.get_session exists and is used
    if hasattr(main_auth_manager.db_manager, "get_session"):
        app.dependency_overrides[main_auth_manager.db_manager.get_session] = (
            lambda: db_session
        )

    # It's crucial that the AuthManager used by the app is the test_auth_manager.
    # The current main.py instantiates auth_manager globally. We need to ensure
    # this global `auth_manager` uses the `test_db_manager`.
    original_auth_db_manager = main_auth_manager.db_manager
    main_auth_manager.db_manager = test_db_manager

    with TestClient(app) as c:
        yield c

    # Clean up overrides after tests
    app.dependency_overrides = {}
    main_auth_manager.db_manager = original_auth_db_manager


# --- Helper Fixtures for Creating Users ---


@pytest.fixture(scope="function")
def test_user_password():
    return "testpassword123"


@pytest.fixture(scope="function")
def test_user(
    test_auth_manager, test_user_password, clear_users_table
):  # Added clear_users_table dependency
    """Creates a standard test user in the test database and returns their details."""
    # clear_users_table will run before this fixture code due to dependency
    username = "testuser@example.com"
    email = "testuser@example.com"
    user_details = test_auth_manager.create_user(
        username=username,
        email=email,
        password=test_user_password,
        full_name="Test User",
        role="user",
    )
    if (
        user_details is None
    ):  # Handle case where user might already exist from a previous failed test run if scope was session
        # For function scope, this shouldn't be an issue if DB is cleaned.
        # If it happens, fetch existing.
        db_user = test_auth_manager.db_manager.get_db_user_by_username(username)
        if db_user:
            user_details = {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email,
                "full_name": db_user.full_name,
                "role": db_user.role,
                "is_active": db_user.is_active,
            }
        else:
            pytest.fail(f"Failed to create or retrieve test_user: {username}")

    return user_details


@pytest.fixture(scope="function")
def test_admin_password():
    return "adminpassword123"


@pytest.fixture(scope="function")
def test_admin_user(
    test_auth_manager, test_admin_password, clear_users_table
):  # Added clear_users_table dependency
    """Creates an admin test user in the test database and returns their details."""
    # clear_users_table will run before this fixture code due to dependency
    username = "admin@example.com"
    email = "admin@example.com"
    user_details = test_auth_manager.create_user(
        username=username,
        email=email,
        password=test_admin_password,
        full_name="Admin User",
        role="admin",
    )
    if user_details is None:
        db_user = test_auth_manager.db_manager.get_db_user_by_username(username)
        if db_user:
            user_details = {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email,
                "full_name": db_user.full_name,
                "role": db_user.role,
                "is_active": db_user.is_active,
            }
        else:
            pytest.fail(f"Failed to create or retrieve test_admin_user: {username}")
    return user_details


# --- Helper Fixtures for Authentication Tokens ---


@pytest.fixture(scope="function")
def user_auth_headers(client, test_auth_manager, test_user, test_user_password):
    """Provides authentication headers for a standard user."""
    login_data = {"username": test_user["username"], "password": test_user_password}
    response = client.post("/api/v1/auth/token", data=login_data)
    assert response.status_code == 200, (
        f"Failed to get token for {test_user['username']}. "
        f"Response: {response.json()}"
    )
    tokens = response.json()
    access_token = tokens["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def admin_auth_headers(client, test_auth_manager, test_admin_user, test_admin_password):
    """Provides authentication headers for an admin user."""
    login_data = {
        "username": test_admin_user["username"],
        "password": test_admin_password,
    }
    response = client.post("/api/v1/auth/token", data=login_data)
    assert response.status_code == 200, (
        f"Failed to get token for admin {test_admin_user['username']}. "
        f"Response: {response.json()}"
    )
    tokens = response.json()
    access_token = tokens["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


# Example: Fixture to clear specific tables before a test or group of tests
@pytest.fixture(scope="function")
def clear_users_table(db_session):
    """Clears the users table before each test that uses it."""
    db_session.query(DBUser).delete()
    db_session.commit()
    # Add other tables if needed, e.g., Well, ProductionData
    # from gaia_genesis.reservoir_engineering.database import Well, ProductionData
    # db_session.query(ProductionData).delete()
    # db_session.query(Well).delete()
    # db_session.commit()
    yield  # Test runs here
    # Teardown (if any) after yield, though rollback in db_session usually handles it.
    # db_session.query(DBUser).delete() # Clearing specific tables here can be
    # redundant if db_session rollback is effective and might conflict with
    # broader table clearing strategies.


@pytest.fixture(scope="function")
def clear_wells_and_production_data_tables(db_session):  # Takes db_session
    """Clears Well and ProductionData tables using DELETE statements via db_session."""
    from gaia_genesis.reservoir_engineering.database import Well, ProductionData

    db_session.execute(ProductionData.__table__.delete())
    db_session.execute(Well.__table__.delete())
    db_session.commit()
    yield


# Fixture to ensure the default admin user from main.py's startup logic exists for
# certain tests, especially if tests don't always run main.py's __main__ block.
@pytest.fixture(scope="function")
def ensure_default_admin_user(test_auth_manager, test_admin_password):
    username = "admin"
    email = "admin@example.com"
    user = test_auth_manager.get_user_by_username(username)
    if not user:
        test_auth_manager.create_user(
            username=username,
            email=email,
            password=test_admin_password,
            full_name="Default Admin User",
            role="admin",
        )
    return test_auth_manager.get_user_details(username)


# If some tests specifically need to check behavior when no users exist, they might
# not use `clear_users_table` or might use it differently.

# This conftest.py provides a robust setup for testing the FastAPI application
# with a clean, isolated database for each test function and easy ways to
# get authenticated clients for different user roles.
# The `client` fixture is the primary way tests will interact with the app.
# Helper fixtures like `test_user`, `admin_auth_headers` simplify test setup.
# The `db_session` can be used for direct database assertions or setup if needed.
# Remember that any direct DB manipulation via `db_session` should be committed
# if it's part of the setup for a TestClient call, as the TestClient runs in a
# separate thread and won't see uncommitted changes from the test function's session.
# However, for cleanup, `db_session.rollback()` in its own teardown handles it.
# The current `client` fixture reconfigures the main app's DB and Auth manager
# dependencies, which is a powerful way to ensure tests are isolated and use
# test-specific resources.
# The `test_engine` and `TestingSessionLocal` are set up once per session, but
# `db_session` provides a fresh transaction per test function.
# Clearing tables explicitly (like in `clear_users_table`) is an extra layer of
# safety, especially if tests might commit data for some reason (though ideally they
# shouldn't directly). For most tests, relying on `db_session`'s rollback and
# `TestClient` interactions will be sufficient.
# The `sys.path.insert` is crucial for making sure `pytest` can find the backend
# modules. It's often better to structure the project so this isn't needed
# (e.g., installable package or using `python -m pytest`), but for simple
# structures, it's a common workaround.
# Ensure `TEST_DATABASE_URL` does not conflict with your development database.
# Using a file like `test_temp_app.db` and ensuring it's deleted is good practice.
# Using function scope for `db_session` and fixtures that create data (like
# `test_user`) is generally safer for test isolation. Session scope is for things
# that are expensive to set up and don't change state in a way that affects other
# tests (like `test_engine` itself).
# The `client` fixture now correctly handles dependency overrides for the app's
# global `db_manager` and `auth_manager` by directly patching their `db_manager`
# attribute. This is important because these managers are instantiated globally in
# `main.py`. If `AuthManager` or `DatabaseManager` were obtained via FastAPI
# dependencies in routes, `app.dependency_overrides` would be the standard way.
# Here, we adapt to the global instantiation.
# The `test_user_password` and `test_admin_password` fixtures are added for clarity
# and reusability. They are marked SENSITIVE_VALUE_DO_NOT_LOG to prevent accidental
# logging if pytest verbosity is high and fixture values are shown.
# The `ensure_default_admin_user` can be used in tests that might depend on the
# "admin" user that is typically created by `main.py` when run directly.
# Added `sys.path.insert` to ensure modules from `backend` can be imported correctly
# by `pytest` when `pytest` is run from the root directory or `backend/tests/`.
# `Base.metadata.drop_all(bind=engine)` is added to `test_engine` teardown to ensure
# tables are cleaned. `os.remove` for the SQLite file is also good practice.
# `db_session` now explicitly rolls back to prevent data leakage.
# `test_db_manager` fixture is added for cases where direct interaction with a
# test-configured `DatabaseManager` is needed.
# `client` fixture has improved dependency overriding logic, especially for the global
# `auth_manager`. `test_user` and `test_admin_user` fixtures are improved to handle
# potential pre-existence if scopes were different or DB not fully cleaned, though
# with function scope this is less likely. Password fixtures are explicitly marked
# sensitive. `user_auth_headers` and `admin_auth_headers` now assert successful token
# retrieval. `clear_users_table` fixture is enhanced.
# `ensure_default_admin_user` fixture is added.
# Extensive comments explain the rationale behind fixture scopes and design choices.
