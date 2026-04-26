import pytest
import datetime

# from typing import List # Unused
import logging  # It's good practice to have logging available

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session  # Added import for Session

# Corrected imports
from gaia_genesis.core.database_manager import DatabaseManager

# Removed DBUser from this import as it's unused in this file
from gaia_genesis.core.database_models import Well, ProductionData

logger = logging.getLogger(__name__)

# Note: This test module focuses on DatabaseManager's direct methods.
# It uses the `db_session` and `test_db_manager` fixtures from conftest.py,
# which provide an isolated database session for each test.


def test_db_manager_initialization(test_db_manager: DatabaseManager):
    """Test that the DatabaseManager initializes correctly with the test engine."""
    assert test_db_manager.engine is not None
    assert test_db_manager.SessionLocal is not None
    # The actual URL might vary if conftest overrides it for tests.
    # This assertion assumes test_temp_app.db is used by conftest.
    # logger.info(f"Test DB Manager Engine URL: {str(test_db_manager.engine.url)}")
    assert "test_temp_app.db" in str(test_db_manager.engine.url)


def test_create_and_get_well(
    db_session, test_db_manager: DatabaseManager, clear_wells_and_production_data_tables
):
    """Test inserting and retrieving a well."""
    well_name = "TestWell-001"
    field_name = "TestField"
    lat, lon = 30.0, -90.0

    inserted_well_id = test_db_manager.insert_well(well_name, field_name, lat, lon)
    assert inserted_well_id is not None

    retrieved_well = test_db_manager.get_well_by_name(well_name)
    assert retrieved_well is not None
    assert retrieved_well.id == inserted_well_id
    assert retrieved_well.name == well_name
    assert retrieved_well.field == field_name
    assert retrieved_well.latitude == lat
    assert retrieved_well.longitude == lon
    # In core.database_models.Well, created_at uses func.now() which results in datetime, not just date
    # Allow for datetime comparison, or ensure model uses date.
    assert isinstance(retrieved_well.created_at, datetime.datetime) or isinstance(
        retrieved_well.created_at, datetime.date
    )

    # Test inserting duplicate well name (should return existing ID and not create new)
    initial_well_count = db_session.query(Well).count()
    duplicate_well_id = test_db_manager.insert_well(well_name, "AnotherField")
    assert duplicate_well_id == inserted_well_id
    assert db_session.query(Well).count() == initial_well_count  # No new well created

    non_existent_well = test_db_manager.get_well_by_name("NonExistentWell")
    assert non_existent_well is None


def test_insert_and_get_production_data(
    db_session, test_db_manager: DatabaseManager, clear_wells_and_production_data_tables
):
    """Test inserting and retrieving production data for a well."""
    well_id = test_db_manager.insert_well("ProdWell-001")
    assert well_id is not None

    prod_data = [
        {"date": "2023-01-01", "oil_rate": 100.0, "gas_rate": 50.0, "water_rate": 10.0},
        {
            "date": datetime.date(2023, 1, 2),
            "oil_rate": 95.0,
            "gas_rate": 48.0,
            "water_rate": 12.0,
        },
    ]
    success = test_db_manager.insert_production_data(well_id, prod_data)
    assert success

    retrieved_data = test_db_manager.get_well_production_data(well_id)
    assert len(retrieved_data) == 2
    assert retrieved_data[0]["oil_rate"] == 100.0
    # Dates are stored as Python date objects, ensure comparison is fair
    # The DB manager returns them as strings 'YYYY-MM-DD' from its `get_well_production_data`.
    assert retrieved_data[1]["date"] == "2023-01-02"

    # Test inserting duplicate production data (should be skipped by unique constraint)
    duplicate_prod_data = [
        {"date": "2023-01-01", "oil_rate": 999.0}
    ]  # Same date as first entry
    success_dup = test_db_manager.insert_production_data(well_id, duplicate_prod_data)
    assert success_dup  # Method might return True even if duplicates are skipped

    retrieved_data_after_dup = test_db_manager.get_well_production_data(well_id)
    assert (
        len(retrieved_data_after_dup) == 2
    )  # No new record added due to unique constraint

    # Verify original data for the duplicate date is unchanged
    original_entry_for_dup_date = next(
        item for item in retrieved_data_after_dup if item["date"] == "2023-01-01"
    )
    assert original_entry_for_dup_date["oil_rate"] == 100.0

    # Test date range query
    limited_data = test_db_manager.get_well_production_data(
        well_id, start_date=datetime.date(2023, 1, 2)
    )
    assert len(limited_data) == 1
    assert limited_data[0]["date"] == "2023-01-02"

    # Test with non-existent well ID
    assert not test_db_manager.insert_production_data(99999, prod_data)
    assert not test_db_manager.get_well_production_data(88888)


# --- User Management Method Tests ---


def test_create_and_get_db_user(
    db_session, test_db_manager: DatabaseManager, clear_users_table
):
    """Test creating and retrieving a user from the database."""
    username = "db_user_test"
    email = "db_user@example.com"
    hashed_password = "hashed_password_example"
    full_name = "DB Test User"
    role = "editor"

    created_user = test_db_manager.create_db_user(
        username, email, hashed_password, full_name, role
    )
    assert created_user is not None
    assert created_user.username == username
    assert created_user.email == email
    assert created_user.hashed_password == hashed_password
    assert created_user.full_name == full_name
    assert created_user.role == role
    assert created_user.is_active is True

    retrieved_user_by_name = test_db_manager.get_db_user_by_username(username)
    assert retrieved_user_by_name is not None
    assert retrieved_user_by_name.id == created_user.id
    assert retrieved_user_by_name.email == email

    retrieved_user_by_email = test_db_manager.get_db_user_by_email(email)
    assert retrieved_user_by_email is not None
    assert retrieved_user_by_email.id == created_user.id
    assert retrieved_user_by_email.username == username

    assert test_db_manager.get_db_user_by_username("nosuchuser") is None
    assert test_db_manager.get_db_user_by_email("nosuch@example.com") is None


def test_create_db_user_duplicate_username(
    db_session, test_db_manager: DatabaseManager, clear_users_table
):
    """Test that creating a user with a duplicate username fails."""
    username = "duplicate_user"
    test_db_manager.create_db_user(username, "email1@example.com", "pass1")

    failed_creation = test_db_manager.create_db_user(
        username, "email2@example.com", "pass2"
    )
    assert failed_creation is None


def test_create_db_user_duplicate_email(
    db_session, test_db_manager: DatabaseManager, clear_users_table
):
    """Test that creating a user with a duplicate email fails."""
    email = "duplicate@example.com"
    test_db_manager.create_db_user("user1", email, "pass1")

    failed_creation = test_db_manager.create_db_user("user2", email, "pass2")
    assert failed_creation is None


def test_get_all_db_users(
    db_session, test_db_manager: DatabaseManager, clear_users_table
):
    """Test retrieving all users with pagination."""
    users_to_create = [
        ("user_a", "a@example.com"),
        ("user_b", "b@example.com"),
        ("user_c", "c@example.com"),
        ("user_d", "d@example.com"),
        ("user_e", "e@example.com"),
    ]
    for uname, uemail in users_to_create:
        test_db_manager.create_db_user(uname, uemail, "pass")

    all_users_from_db = test_db_manager.get_all_db_users()  # Using default limit
    assert len(all_users_from_db) == len(users_to_create)

    limited_users = test_db_manager.get_all_db_users(limit=2)
    assert len(limited_users) == 2

    users_page2 = test_db_manager.get_all_db_users(skip=2, limit=2)
    assert len(users_page2) == 2

    retrieved_page1_usernames = sorted([u.username for u in limited_users])
    retrieved_page2_usernames = sorted([u.username for u in users_page2])

    # Check that page 2 users are not in page 1 users to verify skip logic
    for user_p2_name in retrieved_page2_usernames:
        assert user_p2_name not in retrieved_page1_usernames


def test_update_db_user(
    db_session, test_db_manager: DatabaseManager, clear_users_table
):
    """Test updating a user's details."""
    username = "update_target_user"
    original_email = "original@example.com"
    test_db_manager.create_db_user(
        username, original_email, "password", "Original Name", "user", True
    )

    updates = {
        "email": "updated@example.com",
        "full_name": "Updated Name",
        "role": "admin",
        "is_active": False,
    }
    updated_user = test_db_manager.update_db_user(username, updates)
    assert updated_user is not None
    assert updated_user.email == "updated@example.com"
    assert updated_user.full_name == "Updated Name"
    assert updated_user.role == "admin"
    assert updated_user.is_active is False

    no_username_update = test_db_manager.update_db_user(
        username, {"username": "new_username_shoud_fail"}
    )
    assert no_username_update is not None
    assert no_username_update.username == username

    assert test_db_manager.update_db_user("nosuchuser", {"email": "a@b.c"}) is None


def test_delete_db_user(
    db_session, test_db_manager: DatabaseManager, clear_users_table
):
    """Test deleting a user."""
    username_to_delete = "delete_me_user"
    test_db_manager.create_db_user(username_to_delete, "delete@example.com", "pass")

    assert test_db_manager.delete_db_user(username_to_delete) is True
    assert test_db_manager.get_db_user_by_username(username_to_delete) is None

    assert test_db_manager.delete_db_user("nosuchuser_to_delete") is False


def test_well_name_unique_constraint(
    db_session: Session,
    test_db_manager: DatabaseManager,
    clear_wells_and_production_data_tables,
):
    """Test the unique constraint on Well names directly using SQLAlchemy session."""
    well_name = "UniqueWellName"
    db_session.add(
        Well(name=well_name, field="F1", latitude=0, longitude=0)
    )  # Ensure all required fields
    db_session.commit()

    with pytest.raises(IntegrityError):
        db_session.add(Well(name=well_name, field="F2", latitude=1, longitude=1))
        db_session.commit()
    db_session.rollback()


# --- Connection and Session Management Tests ---

def test_db_manager_connect_failure():
    """Test DB connection failure with a bad URL."""
    bad_db_url = "sqlite:///nonexistent_path/should_fail.db" # Or an invalid postgresql URL etc.
    # Ensure the path is truly non-writable or invalid for the DB driver
    # For SQLite, a non-existent directory in the path usually causes failure.
    # If running in a sandbox where all paths might be writable, this needs care.
    # Let's try a deliberately malformed URL for a driver that's not installed.
    malformed_db_url = "postgresql+hopefullynotasdriver://user:pass@host/db"

    db_manager_fail = DatabaseManager(db_url=malformed_db_url)
    assert db_manager_fail.connect() is False
    assert db_manager_fail.engine is None
    assert db_manager_fail.SessionLocal is None


def test_create_tables_not_connected(caplog):
    """Test create_tables fails if DB is not connected."""
    db_manager_no_connect = DatabaseManager(db_url="sqlite:///memory_no_connect.db")
    # Do not call connect()
    with caplog.at_level(logging.ERROR):
        assert db_manager_no_connect.create_tables() is False
    assert "Cannot create tables: Database engine not initialized" in caplog.text


def test_get_session_not_connected(caplog):
    """Test get_session raises error if DB is not connected."""
    db_manager_no_connect = DatabaseManager(db_url="sqlite:///memory_get_session_fail.db")
    # Do not call connect()
    with pytest.raises(ConnectionError, match="Database not connected. Cannot get session."):
        db_manager_no_connect.get_session()
    # Also check log for "SessionLocal not initialized"
    # Note: caplog might not capture this if ConnectionError is raised before logging.
    # The primary check is the ConnectionError.


# --- More specific tests for insert_production_data ---

def test_insert_production_data_invalid_date_formats(
    test_db_manager: DatabaseManager, clear_wells_and_production_data_tables, caplog
):
    """Test insert_production_data with various invalid date formats/types, ensuring they are skipped."""
    well_id = test_db_manager.insert_well("WellForInvalidDates")
    assert well_id is not None

    prod_data_invalid_dates = [
        {"date": "2023/01/01", "oil_rate": 100.0}, # Wrong format
        {"date": "not-a-date", "oil_rate": 110.0}, # Not a date string
        {"date": 12345, "oil_rate": 120.0},        # Wrong type (int)
        {"date": None, "oil_rate": 130.0},         # None date
        {"date": "2023-01-05", "oil_rate": 150.0}  # Valid one to ensure something can be inserted
    ]

    with caplog.at_level(logging.WARNING):
        success = test_db_manager.insert_production_data(well_id, prod_data_invalid_dates)

    assert success is True # The method returns True if any valid data is processed or no new data needs inserting

    # Check logs for warnings about skipped records
    assert "Invalid date format for record: {'date': '2023/01/01', 'oil_rate': 100.0}. Skipping." in caplog.text
    assert "Invalid date format for record: {'date': 'not-a-date', 'oil_rate': 110.0}. Skipping." in caplog.text
    assert "Invalid date type for record: {'date': 12345, 'oil_rate': 120.0}. Skipping." in caplog.text
    assert "Invalid date type for record: {'date': None, 'oil_rate': 130.0}. Skipping." in caplog.text

    retrieved_data = test_db_manager.get_well_production_data(well_id)
    assert len(retrieved_data) == 1 # Only the valid date should be inserted
    assert retrieved_data[0]["date"] == "2023-01-05"
    assert retrieved_data[0]["oil_rate"] == 150.0


def test_insert_production_data_no_new_data_to_insert(
    test_db_manager: DatabaseManager, clear_wells_and_production_data_tables, caplog
):
    """Test insert_production_data when all provided data already exists or is invalid."""
    well_id = test_db_manager.insert_well("WellForNoNewData")
    assert well_id is not None

    # Insert initial valid data
    initial_data = [{"date": "2023-02-01", "oil_rate": 200.0}]
    assert test_db_manager.insert_production_data(well_id, initial_data) is True

    # Attempt to insert same data again, plus some invalid data
    data_to_try_insert = [
        {"date": "2023-02-01", "oil_rate": 201.0}, # Duplicate date
        {"date": "invalid-date", "oil_rate": 202.0}  # Invalid date
    ]

    with caplog.at_level(logging.INFO): # To catch "No new production data"
        success = test_db_manager.insert_production_data(well_id, data_to_try_insert)

    assert success is True
    assert f"No new production data to insert for well ID {well_id}." in caplog.text

    retrieved_data = test_db_manager.get_well_production_data(well_id)
    assert len(retrieved_data) == 1
    assert retrieved_data[0]["oil_rate"] == 200.0 # Original data unchanged


# --- Test DatabaseManager.close() ---
def test_db_manager_close_connected(test_db_manager_with_real_connect: DatabaseManager, mocker):
    """Test that close() disposes the engine if connected."""
    # test_db_manager_with_real_connect is a fixture that ensures connect() was called.
    # We need to spy on engine.dispose.
    # Ensure engine exists first
    assert test_db_manager_with_real_connect.engine is not None

    mock_dispose = mocker.spy(test_db_manager_with_real_connect.engine, 'dispose')

    test_db_manager_with_real_connect.close()

    mock_dispose.assert_called_once()


def test_db_manager_close_not_connected(mocker):
    """Test that close() does not fail if engine is None (not connected)."""
    db_manager_no_engine = DatabaseManager()
    assert db_manager_no_engine.engine is None # Engine is None by default

    # No need to mock dispose as it shouldn't be called if engine is None.
    # Just ensure calling close() doesn't raise an error.
    try:
        db_manager_no_engine.close()
    except Exception as e:
        pytest.fail(f"DatabaseManager.close() raised an exception when not connected: {e}")


def test_production_data_well_date_unique_constraint(
    db_session: Session,
    test_db_manager: DatabaseManager,
    clear_wells_and_production_data_tables,
):
    """Test the unique constraint on (well_id, date) for ProductionData."""
    well = Well(name="ProdConstraintWell", field="F", latitude=0, longitude=0)
    db_session.add(well)
    db_session.commit()

    date_val = datetime.date(2023, 5, 5)
    db_session.add(ProductionData(well_id=well.id, date=date_val, oil_rate=10))
    db_session.commit()

    with pytest.raises(IntegrityError):
        db_session.add(ProductionData(well_id=well.id, date=date_val, oil_rate=20))
        db_session.commit()
    db_session.rollback()
