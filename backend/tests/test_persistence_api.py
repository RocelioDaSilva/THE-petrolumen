import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.persistence.database import DatabaseManager
from app.persistence.dependencies import get_database_manager


@pytest.fixture
def persistence_client(tmp_path, monkeypatch):
    monkeypatch.setenv("PETROLUMEN_SECRET_KEY", "test-secret-key-with-at-least-32-characters")
    manager = DatabaseManager(f"sqlite:///{tmp_path / 'persistence.db'}")
    assert manager.connect()
    manager.create_all()
    app.dependency_overrides[get_database_manager] = lambda: manager
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.pop(get_database_manager, None)
    manager.close()


def _register_and_login(client, username):
    registration = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "secure-password",
        },
    )
    assert registration.status_code == 201, registration.text
    assert registration.json()["role"] == "user"

    login = client.post(
        "/api/auth/token",
        json={"username": username, "password": "secure-password"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_registration_cannot_assign_privileged_role(persistence_client):
    response = persistence_client.post(
        "/api/auth/register",
        json={
            "username": "role-test",
            "email": "role-test@example.com",
            "password": "secure-password",
            "role": "admin",
        },
    )

    assert response.status_code == 422


def test_authenticated_user_can_save_list_get_and_delete_simulations(
    persistence_client,
):
    client = persistence_client
    headers = _register_and_login(client, "engineer")
    assert client.get("/api/auth/me", headers=headers).json()["username"] == "engineer"

    saved = client.post(
        "/api/saved-simulations",
        headers=headers,
        json={
            "name": "Base case",
            "simulation_type": "black_oil",
            "input_data": {"pressure": 3000.0, "wells": []},
            "result_data": {"pressure": [2980.0, 2975.0]},
        },
    )

    assert saved.status_code == 201, saved.text
    record = saved.json()
    assert record["input_data"]["pressure"] == 3000.0
    assert record["result_data"]["pressure"] == [2980.0, 2975.0]

    listing = client.get("/api/saved-simulations", headers=headers)
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()] == [record["id"]]
    assert "result_data" not in listing.json()[0]

    fetched = client.get(
        f"/api/saved-simulations/{record['id']}", headers=headers
    )
    assert fetched.status_code == 200
    assert fetched.json()["result_data"] == record["result_data"]

    assert client.delete(
        f"/api/saved-simulations/{record['id']}", headers=headers
    ).status_code == 204
    assert client.get(
        f"/api/saved-simulations/{record['id']}", headers=headers
    ).status_code == 404


def test_saved_simulations_are_isolated_by_owner(persistence_client):
    client = persistence_client
    first_user = _register_and_login(client, "first")
    second_user = _register_and_login(client, "second")
    saved = client.post(
        "/api/saved-simulations",
        headers=first_user,
        json={
            "name": "Private run",
            "simulation_type": "black_oil",
            "input_data": {},
            "result_data": {},
        },
    )
    assert saved.status_code == 201, saved.text

    response = client.get(
        f"/api/saved-simulations/{saved.json()['id']}",
        headers=second_user,
    )
    assert response.status_code == 404
    assert client.get("/api/saved-simulations", headers=second_user).json() == []


def test_persistence_endpoints_require_configured_secret_key(
    persistence_client, monkeypatch
):
    monkeypatch.setenv("PETROLUMEN_SECRET_KEY", "")
    response = persistence_client.post(
        "/api/auth/register",
        json={
            "username": "blocked",
            "email": "blocked@example.com",
            "password": "secure-password",
        },
    )

    assert response.status_code == 503
    assert "PETROLUMEN_SECRET_KEY" in response.json()["detail"]
