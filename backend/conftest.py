import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys
import logging
import structlog

# Add the backend directory to sys.path
_backend_dir = os.path.abspath(os.path.dirname(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Configure structlog to use standard logging for tests so caplog works
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Corrected imports for database components
from gaia_genesis.models import Base, User as DBUser
from gaia_genesis.core.database_manager import DatabaseManager
from main import (
    app,
    db_manager as main_db_manager,
    auth_manager as main_auth_manager,
)

from gaia_genesis.core.auth_manager import AuthManager as CoreAuthManager

TEST_DATABASE_URL = "sqlite:///./test_temp_app.db"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_temp_app.db"):
        os.remove("./test_temp_app.db")

@pytest.fixture(scope="function")
def TestingSessionLocal(test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def db_session(TestingSessionLocal):
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def test_db_manager(test_engine):
    DatabaseManager.reset_instance()
    manager = DatabaseManager.get_instance(db_url=TEST_DATABASE_URL)
    manager.engine = test_engine
    manager.SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    return manager

@pytest.fixture(scope="function")
def test_auth_manager(test_db_manager):
    test_secret_key = "test_secret_key_for_fastapi_tests"
    CoreAuthManager.reset_instance()
    return CoreAuthManager.get_instance(
        db_manager=test_db_manager, secret_key=test_secret_key
    )

@pytest.fixture(scope="function")
def client(test_db_manager, test_auth_manager, db_session):
    app.dependency_overrides[main_db_manager.get_session] = lambda: db_session
    if hasattr(main_auth_manager.db_manager, "get_session"):
        app.dependency_overrides[main_auth_manager.db_manager.get_session] = (
            lambda: db_session
        )

    from main import data_uploader as main_data_uploader
    original_auth_db_manager = main_auth_manager.db_manager
    main_auth_manager.db_manager = test_db_manager
    original_data_uploader_db_manager = main_data_uploader.db_manager
    main_data_uploader.db_manager = test_db_manager

    with TestClient(app) as c:
        yield c

    app.dependency_overrides = {}
    main_auth_manager.db_manager = original_auth_db_manager
    main_data_uploader.db_manager = original_data_uploader_db_manager

@pytest.fixture(scope="function")
def test_user_password():
    return "testpassword123"

@pytest.fixture(scope="function")
def test_user(test_auth_manager, test_user_password, clear_users_table):
    username = "testuser@example.com"
    email = "testuser@example.com"
    user_details = test_auth_manager.create_user(
        username=username,
        email=email,
        password=test_user_password,
        full_name="Test User",
        role="user",
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
            pytest.fail(f"Failed to create or retrieve test_user: {username}")
    return user_details

@pytest.fixture(scope="function")
def test_admin_password():
    return "adminpassword123"

@pytest.fixture(scope="function")
def test_admin_user(test_auth_manager, test_admin_password, clear_users_table):
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

@pytest.fixture(scope="function")
def user_auth_headers(client, test_auth_manager, test_user, test_user_password):
    login_data = {"username": test_user["username"], "password": test_user_password}
    response = client.post("/api/v1/auth/token", data=login_data)
    assert response.status_code == 200
    tokens = response.json()
    access_token = tokens["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope="function")
def admin_auth_headers(client, test_auth_manager, test_admin_user, test_admin_password):
    login_data = {
        "username": test_admin_user["username"],
        "password": test_admin_password,
    }
    response = client.post("/api/v1/auth/token", data=login_data)
    assert response.status_code == 200
    tokens = response.json()
    access_token = tokens["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope="function")
def clear_users_table(db_session):
    db_session.query(DBUser).delete()
    db_session.commit()
    yield

@pytest.fixture(scope="function")
def clear_wells_and_production_data_tables(db_session):
    from gaia_genesis.models import Well, ProductionData
    db_session.execute(ProductionData.__table__.delete())
    db_session.execute(Well.__table__.delete())
    db_session.commit()
    yield

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
