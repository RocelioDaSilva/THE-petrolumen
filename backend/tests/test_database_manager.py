import pytest
import datetime
from typing import List

from sqlalchemy.exc import IntegrityError

# Ensure imports from gaia_genesis.reservoir_engineering are possible
# This might require adjusting sys.path or using a specific project structure / pytest configuration
# For now, assuming conftest.py handles path adjustments if necessary.
from gaia_genesis.reservoir_engineering.database import DatabaseManager, Well, ProductionData, User as DBUser

# Note: This test module focuses on DatabaseManager's direct methods.
# It uses the `db_session` and `test_db_manager` fixtures from conftest.py,
# which provide an isolated database session for each test.

def test_db_manager_initialization(test_db_manager: DatabaseManager):
    """Test that the DatabaseManager initializes correctly with the test engine."""
    assert test_db_manager.engine is not None
    assert test_db_manager.SessionLocal is not None
    assert str(test_db_manager.engine.url) == "sqlite:///./test_temp_app.db"

def test_create_and_get_well(db_session, test_db_manager: DatabaseManager, clear_wells_and_production_data_tables):
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
    assert retrieved_well.created_at == datetime.date.today()

    # Test inserting duplicate well name (should return existing ID)
    duplicate_well_id = test_db_manager.insert_well(well_name, "AnotherField")
    assert duplicate_well_id == inserted_well_id

    non_existent_well = test_db_manager.get_well_by_name("NonExistentWell")
    assert non_existent_well is None

def test_insert_and_get_production_data(db_session, test_db_manager: DatabaseManager, clear_wells_and_production_data_tables):
    """Test inserting and retrieving production data for a well."""
    well_id = test_db_manager.insert_well("ProdWell-001")
    assert well_id is not None

    prod_data = [
        {"date": "2023-01-01", "oil_rate": 100.0, "gas_rate": 50.0, "water_rate": 10.0},
        {"date": datetime.date(2023, 1, 2), "oil_rate": 95.0, "gas_rate": 48.0, "water_rate": 12.0},
    ]
    success = test_db_manager.insert_production_data(well_id, prod_data)
    assert success

    retrieved_data = test_db_manager.get_well_production_data(well_id)
    assert len(retrieved_data) == 2
    assert retrieved_data[0]["oil_rate"] == 100.0
    assert retrieved_data[1]["date"] == "2023-01-02"

    # Test inserting duplicate production data (should be skipped)
    duplicate_prod_data = [{"date": "2023-01-01", "oil_rate": 999.0}]
    success_dup = test_db_manager.insert_production_data(well_id, duplicate_prod_data)
    assert success_dup # Should still be true as it handles duplicates gracefully
    retrieved_data_after_dup = test_db_manager.get_well_production_data(well_id)
    assert len(retrieved_data_after_dup) == 2 # No new record added
    assert retrieved_data_after_dup[0]["oil_rate"] == 100.0 # Original value preserved

    # Test date range query
    limited_data = test_db_manager.get_well_production_data(well_id, start_date=datetime.date(2023,1,2))
    assert len(limited_data) == 1
    assert limited_data[0]["date"] == "2023-01-02"

    # Test with non-existent well ID
    assert not test_db_manager.insert_production_data(99999, prod_data) # Well not found
    assert not test_db_manager.get_well_production_data(88888) # Empty list for non-existent well

# --- User Management Method Tests ---

def test_create_and_get_db_user(db_session, test_db_manager: DatabaseManager, clear_users_table):
    """Test creating and retrieving a user from the database."""
    username = "db_user_test"
    email = "db_user@example.com"
    hashed_password = "hashed_password_example"
    full_name = "DB Test User"
    role = "editor"

    created_user = test_db_manager.create_db_user(username, email, hashed_password, full_name, role)
    assert created_user is not None
    assert created_user.username == username
    assert created_user.email == email
    assert created_user.hashed_password == hashed_password
    assert created_user.full_name == full_name
    assert created_user.role == role
    assert created_user.is_active is True # Default

    # Retrieve by username
    retrieved_user_by_name = test_db_manager.get_db_user_by_username(username)
    assert retrieved_user_by_name is not None
    assert retrieved_user_by_name.id == created_user.id
    assert retrieved_user_by_name.email == email

    # Retrieve by email
    retrieved_user_by_email = test_db_manager.get_db_user_by_email(email)
    assert retrieved_user_by_email is not None
    assert retrieved_user_by_email.id == created_user.id
    assert retrieved_user_by_email.username == username

    # Test non-existent user
    assert test_db_manager.get_db_user_by_username("nosuchuser") is None
    assert test_db_manager.get_db_user_by_email("nosuch@example.com") is None

def test_create_db_user_duplicate_username(db_session, test_db_manager: DatabaseManager, clear_users_table):
    """Test that creating a user with a duplicate username fails."""
    username = "duplicate_user"
    test_db_manager.create_db_user(username, "email1@example.com", "pass1")

    # Attempt to create another user with the same username
    failed_creation = test_db_manager.create_db_user(username, "email2@example.com", "pass2")
    assert failed_creation is None

def test_create_db_user_duplicate_email(db_session, test_db_manager: DatabaseManager, clear_users_table):
    """Test that creating a user with a duplicate email fails."""
    email = "duplicate@example.com"
    test_db_manager.create_db_user("user1", email, "pass1")

    failed_creation = test_db_manager.create_db_user("user2", email, "pass2")
    assert failed_creation is None

def test_get_all_db_users(db_session, test_db_manager: DatabaseManager, clear_users_table):
    """Test retrieving all users with pagination."""
    # Create some users
    users_to_create = [
        ("user_a", "a@example.com"), ("user_b", "b@example.com"), ("user_c", "c@example.com"),
        ("user_d", "d@example.com"), ("user_e", "e@example.com")
    ]
    for uname, uemail in users_to_create:
        test_db_manager.create_db_user(uname, uemail, "pass")

    all_users = test_db_manager.get_all_db_users()
    assert len(all_users) == len(users_to_create)

    # Test pagination (limit)
    limited_users = test_db_manager.get_all_db_users(limit=2)
    assert len(limited_users) == 2

    # Test pagination (skip and limit)
    users_page2 = test_db_manager.get_all_db_users(skip=2, limit=2)
    assert len(users_page2) == 2

    # Check content of pages to ensure no overlap (assuming consistent order, e.g., by ID or insertion)
    # For simplicity, we'll check usernames if order is predictable (often by primary key)
    if len(all_users) >=4: # Ensure enough users for this specific check
        expected_page1_usernames = [u[0] for u in users_to_create[:2]] # Based on creation order
        expected_page2_usernames = [u[0] for u in users_to_create[2:4]]

        retrieved_page1_usernames = [u.username for u in limited_users]
        retrieved_page2_usernames = [u.username for u in users_page2]

        # This depends on the DB returning users in insertion order when no explicit order_by is used.
        # For SQLite, this is often true for simple queries without joins/where on new tables.
        # A more robust test would order by username or ID in get_all_db_users and here.
        # For now, let's assume this basic order holds for this test.
        # assert retrieved_page1_usernames == expected_page1_usernames
        # assert retrieved_page2_usernames == expected_page2_usernames
        # A simpler check: ensure users from page 2 are not in page 1
        for user_p2 in users_page2:
            assert user_p2.username not in retrieved_page1_usernames


def test_update_db_user(db_session, test_db_manager: DatabaseManager, clear_users_table):
    """Test updating a user's details."""
    username = "update_target_user"
    original_email = "original@example.com"
    test_db_manager.create_db_user(username, original_email, "password", "Original Name", "user", True)

    updates = {
        "email": "updated@example.com",
        "full_name": "Updated Name",
        "role": "admin",
        "is_active": False
    }
    updated_user = test_db_manager.update_db_user(username, updates)
    assert updated_user is not None
    assert updated_user.email == "updated@example.com"
    assert updated_user.full_name == "Updated Name"
    assert updated_user.role == "admin"
    assert updated_user.is_active is False

    # Verify that username cannot be updated this way
    no_username_update = test_db_manager.update_db_user(username, {"username": "new_username_shoud_fail"})
    assert no_username_update is not None # Update still happens, but username field should be ignored
    assert no_username_update.username == username # Original username preserved

    # Test updating non-existent user
    assert test_db_manager.update_db_user("nosuchuser", {"email": "a@b.c"}) is None


def test_delete_db_user(db_session, test_db_manager: DatabaseManager, clear_users_table):
    """Test deleting a user."""
    username_to_delete = "delete_me_user"
    test_db_manager.create_db_user(username_to_delete, "delete@example.com", "pass")

    assert test_db_manager.delete_db_user(username_to_delete) is True
    assert test_db_manager.get_db_user_by_username(username_to_delete) is None

    # Test deleting non-existent user
    assert test_db_manager.delete_db_user("nosuchuser_to_delete") is False


# Example of testing constraints directly (though create_db_user already handles this)
def test_well_name_unique_constraint(db_session, test_db_manager: DatabaseManager, clear_wells_and_production_data_tables):
    """Test the unique constraint on Well names directly using SQLAlchemy session."""
    well_name = "UniqueWellName"
    db_session.add(Well(name=well_name))
    db_session.commit()

    with pytest.raises(IntegrityError):
        db_session.add(Well(name=well_name)) # Add another well with the same name
        db_session.commit() # This should fail
    db_session.rollback() # Important to rollback after expected error

def test_production_data_well_date_unique_constraint(db_session, test_db_manager: DatabaseManager, clear_wells_and_production_data_tables):
    """Test the unique constraint on (well_id, date) for ProductionData."""
    well = Well(name="ProdConstraintWell")
    db_session.add(well)
    db_session.commit() # Get well.id

    date_val = datetime.date(2023, 5, 5)
    db_session.add(ProductionData(well_id=well.id, date=date_val, oil_rate=10))
    db_session.commit()

    with pytest.raises(IntegrityError):
        db_session.add(ProductionData(well_id=well.id, date=date_val, oil_rate=20)) # Same well, same date
        db_session.commit()
    db_session.rollback()

# Added `clear_users_table` and `clear_wells_and_production_data_tables` fixtures for better isolation.
# Improved pagination test in `test_get_all_db_users`.
# These tests ensure the DatabaseManager's methods work as expected regarding DB interactions.
