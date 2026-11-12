import datetime

import pytest
from sqlalchemy import create_engine, inspect, select, text

from app.persistence.database import DatabaseManager
from app.persistence.models import ProductionData, Well


@pytest.fixture
def database_manager(tmp_path):
    manager = DatabaseManager(f"sqlite:///{tmp_path / 'database.db'}")
    assert manager.connect()
    manager.create_all()
    yield manager
    manager.close()


def test_database_manager_field_data_filters_dates_and_sorts_wells(database_manager):
    well_b = database_manager.insert_well("Well B", "Field A")
    well_a = database_manager.insert_well("Well A", "Field A")
    other_field = database_manager.insert_well("Well C", "Field B")
    assert well_b is not None and well_a is not None and other_field is not None
    database_manager.insert_production_data(
        well_b,
        [
            {"date": "2024-01-01", "oil_rate": 10.0},
            {"date": "2024-02-01", "oil_rate": 20.0},
        ],
    )
    database_manager.insert_production_data(
        well_a, [{"date": "2024-01-15", "oil_rate": 15.0}]
    )
    database_manager.insert_production_data(
        other_field, [{"date": "2024-01-15", "oil_rate": 99.0}]
    )

    rows = database_manager.get_field_data(
        "Field A",
        start_date=datetime.date(2024, 1, 10),
        end_date=datetime.date(2024, 1, 31),
    )

    assert [(row["well_name"], row["oil_rate"]) for row in rows] == [
        ("Well A", 15.0)
    ]
    assert all(row["field_name"] == "Field A" for row in rows)


def test_database_manager_updates_well_and_rejects_invalid_date_range(database_manager):
    well_id = database_manager.insert_well("Well A", "Field A")
    assert well_id is not None

    assert database_manager.update_well(well_id, "Field B", -20.0, 130.0)
    well = database_manager.get_well_by_name("Well A")
    assert well is not None
    assert (well.field, well.latitude, well.longitude) == ("Field B", -20.0, 130.0)
    assert not database_manager.update_well(well_id + 1, field="Missing")

    with pytest.raises(ValueError, match="Start date must not be after end date"):
        database_manager.get_field_data(
            "Field B",
            start_date=datetime.date(2024, 2, 1),
            end_date=datetime.date(2024, 1, 1),
        )


def test_saved_simulation_owner_listing_has_composite_index(database_manager):
    indexes = {
        index["name"]: index["column_names"]
        for index in inspect(database_manager.engine).get_indexes("saved_simulations")
    }

    assert indexes["ix_saved_simulations_owner_created_at_id"] == [
        "owner_id",
        "created_at",
        "id",
    ]


def test_create_all_adds_owner_column_to_existing_wells_table(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'legacy-database.db'}"
    legacy_engine = create_engine(database_url)
    with legacy_engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE users ("
                "id INTEGER PRIMARY KEY, username VARCHAR, email VARCHAR, "
                "hashed_password VARCHAR, full_name VARCHAR, role VARCHAR, "
                "is_active BOOLEAN, created_at DATE)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE wells ("
                "id INTEGER PRIMARY KEY, name VARCHAR NOT NULL UNIQUE, "
                "field VARCHAR, latitude FLOAT, longitude FLOAT, created_at DATE)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO wells (id, name, created_at) "
                "VALUES (1, 'Legacy well', '2025-01-01')"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE production_data ("
                "id INTEGER PRIMARY KEY, well_id INTEGER NOT NULL, "
                "date DATE NOT NULL, oil_rate FLOAT, gas_rate FLOAT, "
                "water_rate FLOAT)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO production_data "
                "(id, well_id, date, oil_rate) "
                "VALUES (1, 1, '2025-01-01', 10)"
            )
        )
    legacy_engine.dispose()

    manager = DatabaseManager(database_url)
    assert manager.connect()
    try:
        manager.create_all()
        columns = {
            column["name"] for column in inspect(manager.engine).get_columns("wells")
        }
        assert "owner_id" in columns
        production_columns = {
            column["name"]
            for column in inspect(manager.engine).get_columns("production_data")
        }
        assert "imported_at" in production_columns
        assert any(
            foreign_key["referred_table"] == "users"
            for foreign_key in inspect(manager.engine).get_foreign_keys("wells")
        )
        with manager.session() as session:
            legacy_well = session.scalar(select(Well).where(Well.id == 1))
            legacy_record = session.scalar(
                select(ProductionData).where(ProductionData.id == 1)
            )
        assert legacy_well is not None
        assert legacy_well.owner_id is None
        assert legacy_record is not None
        assert legacy_record.imported_at is not None
    finally:
        manager.close()
