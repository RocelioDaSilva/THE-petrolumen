from __future__ import annotations

import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.persistence.database import DatabaseManager
from app.persistence.dependencies import get_database_manager
from app.persistence.models import ProductionData
from app.api.production_routes import MAX_PRODUCTION_CSV_BYTES


@pytest.fixture
def production_import_client(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "PETROLUMEN_SECRET_KEY",
        "production-import-test-secret-key-at-least-32-characters",
    )
    manager = DatabaseManager(f"sqlite:///{tmp_path / 'production-import.db'}")
    assert manager.connect()
    manager.create_all()
    app.dependency_overrides[get_database_manager] = lambda: manager
    with TestClient(app) as client:
        yield client, manager
    app.dependency_overrides.pop(get_database_manager, None)
    manager.close()


def _login(
    client: TestClient, username: str = "production-engineer"
) -> dict[str, str]:
    registration = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "secure-password",
        },
    )
    assert registration.status_code == 201, registration.text
    token = client.post(
        "/api/auth/token",
        json={"username": username, "password": "secure-password"},
    )
    assert token.status_code == 200, token.text
    return {"Authorization": f"Bearer {token.json()['access_token']}"}


def test_production_csv_import_requires_authentication(production_import_client):
    client, _manager = production_import_client
    response = client.post(
        "/api/production/import/csv",
        files={"file": ("production.csv", b"well_name,date,oil_rate\nA,2025-01-01,1\n", "text/csv")},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Bearer authentication is required."


def test_production_csv_import_inserts_rows_and_skips_duplicates(
    production_import_client,
):
    client, manager = production_import_client
    headers = _login(client)
    content = (
        "\nwell_name,date,oil_rate,gas_rate,water_rate\n\n"
        "Well A,2025-01-01,10,,2\n"
        "Well A,2025-02-01,8,,3\n"
        "Well B,2025-01-01,,4,\n"
        "Well A,2025-01-01,99,,9\n"
    )

    response = client.post(
        "/api/production/import/csv",
        headers=headers,
        files={"file": ("production.csv", content.encode(), "text/csv")},
    )

    assert response.status_code == 201, response.text
    assert response.json() == {
        "rows_received": 4,
        "rows_imported": 3,
        "rows_skipped_duplicates": 1,
        "wells_created": 2,
    }

    with manager.session() as session:
        records = session.scalars(
            select(ProductionData).order_by(
                ProductionData.well_id, ProductionData.date
            )
        ).all()
    assert [(row.date, row.oil_rate, row.gas_rate, row.water_rate) for row in records] == [
        (datetime.date(2025, 1, 1), 10.0, None, 2.0),
        (datetime.date(2025, 2, 1), 8.0, None, 3.0),
        (datetime.date(2025, 1, 1), None, 4.0, None),
    ]

    repeated = client.post(
        "/api/production/import/csv",
        headers=headers,
        files={"file": ("production.csv", content.encode(), "text/csv")},
    )
    assert repeated.status_code == 201, repeated.text
    assert repeated.json() == {
        "rows_received": 4,
        "rows_imported": 0,
        "rows_skipped_duplicates": 4,
        "wells_created": 0,
    }


@pytest.mark.parametrize(
    "content",
    [
        "well_name,date,oil_rate\nWell A,not-a-date,10\n",
        "well_name,date,oil_rate\nWell A,2025-02-30,10\n",
        "well_name,date,oil_rate\nWell A,2025-01-01,NaN\n",
        "well_name,date,oil_rate\nWell A,2025-01-01,\n",
        "well_name,date\nWell A,2025-01-01\n",
    ],
)
def test_invalid_production_csv_has_no_database_side_effects(
    production_import_client, content,
):
    client, manager = production_import_client
    headers = _login(client)

    response = client.post(
        "/api/production/import/csv",
        headers=headers,
        files={"file": ("production.csv", content.encode(), "text/csv")},
    )

    assert response.status_code == 422, response.text
    assert manager.list_wells() == []


def test_production_csv_import_enforces_upload_size_limit(production_import_client):
    client, _manager = production_import_client
    headers = _login(client)
    content = b"x" * (MAX_PRODUCTION_CSV_BYTES + 1)

    response = client.post(
        "/api/production/import/csv",
        headers=headers,
        files={"file": ("large.csv", content, "text/csv")},
    )

    assert response.status_code == 413


def test_production_well_listing_is_isolated_by_owner(production_import_client):
    client, _manager = production_import_client
    user_a = _login(client, "user-a")
    user_b = _login(client, "user-b")

    def import_well(headers: dict[str, str], well_name: str):
        return client.post(
            "/api/production/import/csv",
            headers=headers,
            files={
                "file": (
                    "production.csv",
                    (
                        "well_name,date,oil_rate\n"
                        f"{well_name},2025-01-01,10\n"
                    ).encode(),
                    "text/csv",
                )
            },
        )

    assert import_well(user_a, "User A Well").status_code == 201
    assert client.get("/api/production/wells", headers=user_b).json() == []
    assert import_well(user_b, "User B Well").status_code == 201

    wells_a = client.get("/api/production/wells", headers=user_a)
    wells_b = client.get("/api/production/wells", headers=user_b)
    assert wells_a.status_code == 200
    assert wells_b.status_code == 200
    assert [well["name"] for well in wells_a.json()] == ["User A Well"]
    assert [well["name"] for well in wells_b.json()] == ["User B Well"]


def test_user_cannot_import_production_into_another_users_well(
    production_import_client,
):
    client, manager = production_import_client
    user_a = _login(client, "well-owner")
    user_b = _login(client, "other-user")

    content = b"well_name,date,oil_rate\nShared Name,2025-01-01,10\n"
    first_import = client.post(
        "/api/production/import/csv",
        headers=user_a,
        files={"file": ("production.csv", content, "text/csv")},
    )
    assert first_import.status_code == 201, first_import.text

    blocked_import = client.post(
        "/api/production/import/csv",
        headers=user_b,
        files={"file": ("production.csv", content, "text/csv")},
    )
    assert blocked_import.status_code == 409
    assert blocked_import.json()["detail"] == (
        "One or more well names are unavailable for this account."
    )
    assert client.get("/api/production/wells", headers=user_b).json() == []

    with manager.session() as session:
        records = session.scalars(select(ProductionData)).all()
    assert len(records) == 1
