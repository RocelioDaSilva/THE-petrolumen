import pytest
import asyncio
from httpx import AsyncClient, ASGITransport

from main import app
from config import settings


@pytest.mark.asyncio
async def test_static_analyzer_concurrency_isolation(
    client, test_db_manager, test_auth_manager, db_session
):
    """
    Verifies that when USE_SESSION_REGISTRY is True, two users setting up grids,
    well data, and running geostatistical operations concurrently remain isolated
    and operate strictly on their own session state.
    """
    user1_dict = test_auth_manager.create_user(
        username="user1_static@example.com",
        email="user1_static@example.com",
        password="password123",
        full_name="User One Static",
        role="user",
    )
    user2_dict = test_auth_manager.create_user(
        username="user2_static@example.com",
        email="user2_static@example.com",
        password="password123",
        full_name="User Two Static",
        role="user",
    )

    original_flag = settings.USE_SESSION_REGISTRY
    settings.USE_SESSION_REGISTRY = True

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as async_client:
        resp1 = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "user1_static@example.com", "password": "password123"},
        )
        resp2 = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "user2_static@example.com", "password": "password123"},
        )

        assert resp1.status_code == 200, f"Login 1 failed: {resp1.text}"
        assert resp2.status_code == 200, f"Login 2 failed: {resp2.text}"

        token1 = resp1.json()["access_token"]
        token2 = resp2.json()["access_token"]

        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User 1: 5x5 Grid and Well W1
        grid_user1 = {"nx": 5, "ny": 5, "nz": 1, "dx": 10.0, "dy": 10.0, "dz": 1.0}
        well_user1 = {
            "well_name": "W1",
            "x_coord": 10.0,
            "y_coord": 10.0,
            "properties": {
                "porosity": {"md": [100.0, 200.0], "values": [0.20, 0.22]}
            },
        }

        # User 2: 12x12 Grid and Well W2
        grid_user2 = {"nx": 12, "ny": 12, "nz": 1, "dx": 5.0, "dy": 5.0, "dz": 1.0}
        well_user2 = {
            "well_name": "W2",
            "x_coord": 25.0,
            "y_coord": 25.0,
            "properties": {
                "porosity": {"md": [150.0, 250.0], "values": [0.15, 0.18]}
            },
        }

        # Concurrent grid creation and well data addition
        grid_res1, grid_res2, well_res1, well_res2 = await asyncio.gather(
            async_client.post(
                "/api/v1/gaia/static-modeling/static-modeling/grid",
                json=grid_user1,
                headers=headers1,
            ),
            async_client.post(
                "/api/v1/gaia/static-modeling/static-modeling/grid",
                json=grid_user2,
                headers=headers2,
            ),
            async_client.post(
                "/api/v1/gaia/static-modeling/static-modeling/well-data",
                json=well_user1,
                headers=headers1,
            ),
            async_client.post(
                "/api/v1/gaia/static-modeling/static-modeling/well-data",
                json=well_user2,
                headers=headers2,
            ),
        )

        assert grid_res1.status_code == 201, f"User 1 grid failed: {grid_res1.text}"
        assert grid_res2.status_code == 201, f"User 2 grid failed: {grid_res2.text}"
        assert well_res1.status_code == 201, f"User 1 well failed: {well_res1.text}"
        assert well_res2.status_code == 201, f"User 2 well failed: {well_res2.text}"

        # Concurrent Kriging requests
        kriging_req = {"property_name": "porosity"}
        krig_res1, krig_res2 = await asyncio.gather(
            async_client.post(
                "/api/v1/gaia/static-modeling/static-modeling/kriging",
                json=kriging_req,
                headers=headers1,
            ),
            async_client.post(
                "/api/v1/gaia/static-modeling/static-modeling/kriging",
                json=kriging_req,
                headers=headers2,
            ),
        )

        assert krig_res1.status_code == 200, f"User 1 kriging failed: {krig_res1.text}"
        assert krig_res2.status_code == 200, f"User 2 kriging failed: {krig_res2.text}"

        data1 = krig_res1.json()
        data2 = krig_res2.json()

        # Assert User 1 grid dimensions remain [5, 5] and User 2 remain [12, 12]
        assert data1["grid_dimensions"] == [5, 5]
        assert data2["grid_dimensions"] == [12, 12]

    settings.USE_SESSION_REGISTRY = original_flag


@pytest.mark.asyncio
async def test_static_analyzer_fallback_global_singleton(
    client, test_db_manager, test_auth_manager, db_session
):
    """
    Verifies that when USE_SESSION_REGISTRY is False, requests fall back to the global
    singleton, reproducing the state-bleed bug where User 2 overwrites User 1's grid setup.
    """
    user1_dict = test_auth_manager.create_user(
        username="fallback_static1@example.com",
        email="fallback_static1@example.com",
        password="password123",
        full_name="Fallback Static One",
        role="user",
    )
    user2_dict = test_auth_manager.create_user(
        username="fallback_static2@example.com",
        email="fallback_static2@example.com",
        password="password123",
        full_name="Fallback Static Two",
        role="user",
    )

    original_flag = settings.USE_SESSION_REGISTRY
    settings.USE_SESSION_REGISTRY = False

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as async_client:
        resp1 = await async_client.post(
            "/api/v1/auth/token",
            data={
                "username": "fallback_static1@example.com",
                "password": "password123",
            },
        )
        resp2 = await async_client.post(
            "/api/v1/auth/token",
            data={
                "username": "fallback_static2@example.com",
                "password": "password123",
            },
        )

        assert resp1.status_code == 200
        assert resp2.status_code == 200

        token1 = resp1.json()["access_token"]
        token2 = resp2.json()["access_token"]

        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User 1 sets 5x5 grid and adds well W1
        grid_user1 = {"nx": 5, "ny": 5, "nz": 1, "dx": 10.0, "dy": 10.0, "dz": 1.0}
        well_user1 = {
            "well_name": "W1",
            "x_coord": 10.0,
            "y_coord": 10.0,
            "properties": {
                "porosity": {"md": [100.0, 200.0], "values": [0.20, 0.22]}
            },
        }

        grid_res1 = await async_client.post(
            "/api/v1/gaia/static-modeling/static-modeling/grid",
            json=grid_user1,
            headers=headers1,
        )
        assert grid_res1.status_code == 201

        well_res1 = await async_client.post(
            "/api/v1/gaia/static-modeling/static-modeling/well-data",
            json=well_user1,
            headers=headers1,
        )
        assert well_res1.status_code == 201

        # User 2 overwrites global singleton with 15x15 grid
        grid_user2 = {"nx": 15, "ny": 15, "nz": 1, "dx": 5.0, "dy": 5.0, "dz": 1.0}
        grid_res2 = await async_client.post(
            "/api/v1/gaia/static-modeling/static-modeling/grid",
            json=grid_user2,
            headers=headers2,
        )
        assert grid_res2.status_code == 201

        # User 1 performs kriging
        kriging_req = {"property_name": "porosity"}
        krig_res1 = await async_client.post(
            "/api/v1/gaia/static-modeling/static-modeling/kriging",
            json=kriging_req,
            headers=headers1,
        )
        assert krig_res1.status_code == 200

        data1 = krig_res1.json()

        # Due to global singleton state-bleed, User 1's grid dimensions are now User 2's [15, 15]
        assert data1["grid_dimensions"] == [15, 15]

    settings.USE_SESSION_REGISTRY = original_flag
