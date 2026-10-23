import pytest
import asyncio
from httpx import AsyncClient, ASGITransport

import main
from main import app
from config import settings


@pytest.mark.asyncio
async def test_flowsim_concurrency_isolation(
    client, test_db_manager, test_auth_manager, db_session
):
    """
    Verifies that when USE_SESSION_REGISTRY is True, two users setting up and running
    simulations concurrently operate on independent, isolated simulator instances.
    """
    test_auth_manager.create_user(
        username="user1_sim@example.com",
        email="user1_sim@example.com",
        password="password123",
        full_name="User One Sim",
        role="user",
    )
    test_auth_manager.create_user(
        username="user2_sim@example.com",
        email="user2_sim@example.com",
        password="password123",
        full_name="User Two Sim",
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
            data={"username": "user1_sim@example.com", "password": "password123"},
        )
        resp2 = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "user2_sim@example.com", "password": "password123"},
        )

        assert resp1.status_code == 200, f"Login 1 failed: {resp1.text}"
        assert resp2.status_code == 200, f"Login 2 failed: {resp2.text}"

        token1 = resp1.json()["access_token"]
        token2 = resp2.json()["access_token"]

        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        # Setup distinct grids and rock properties
        # User 1: 10 cells, perm 100
        grid_u1 = {"nx": 10, "dx": 100.0, "area": 100.0}
        rock_u1 = {"permeability": 100.0, "porosity": 0.2}

        # User 2: 20 cells, perm 500
        grid_u2 = {"nx": 20, "dx": 50.0, "area": 100.0}
        rock_u2 = {"permeability": 500.0, "porosity": 0.3}

        # Perform setups concurrently
        res_g1, res_g2, res_r1, res_r2 = await asyncio.gather(
            async_client.post(
                "/api/v1/reservoir/flowsim/setup/grid",
                json=grid_u1,
                headers=headers1,
            ),
            async_client.post(
                "/api/v1/reservoir/flowsim/setup/grid",
                json=grid_u2,
                headers=headers2,
            ),
            async_client.post(
                "/api/v1/reservoir/flowsim/setup/rock",
                json=rock_u1,
                headers=headers1,
            ),
            async_client.post(
                "/api/v1/reservoir/flowsim/setup/rock",
                json=rock_u2,
                headers=headers2,
            ),
        )

        assert res_g1.status_code == 200, f"Grid setup 1 failed: {res_g1.text}"
        assert res_g2.status_code == 200, f"Grid setup 2 failed: {res_g2.text}"
        assert res_r1.status_code == 200, f"Rock setup 1 failed: {res_r1.text}"
        assert res_r2.status_code == 200, f"Rock setup 2 failed: {res_r2.text}"

        # Run simulations concurrently
        run_params = {"end_time": 10.0, "dt": 1.0}
        run_res1, run_res2 = await asyncio.gather(
            async_client.post(
                "/api/v1/reservoir/flowsim/run",
                json=run_params,
                headers=headers1,
            ),
            async_client.post(
                "/api/v1/reservoir/flowsim/run",
                json=run_params,
                headers=headers2,
            ),
        )

        assert run_res1.status_code == 200, f"Run 1 failed: {run_res1.text}"
        assert run_res2.status_code == 200, f"Run 2 failed: {run_res2.text}"

        data1 = run_res1.json()
        data2 = run_res2.json()

        assert data1["status"] == "Completed"
        assert data2["status"] == "Completed"

        # Check pressures at block 0 are distinct due to different grid and permeability
        pressures_u1 = data1["pressure_at_block"]["0"]
        pressures_u2 = data2["pressure_at_block"]["0"]

        assert pressures_u1 != pressures_u2

    settings.USE_SESSION_REGISTRY = original_flag


@pytest.mark.asyncio
async def test_flowsim_reset_session_isolation(
    client, test_db_manager, test_auth_manager, db_session
):
    """
    Verifies that when User 1 issues a /reset request, only User 1's simulator instance
    is cleared from the SessionRegistry, and User 2's active session is completely preserved.
    """
    test_auth_manager.create_user(
        username="reset_user1@example.com",
        email="reset_user1@example.com",
        password="password123",
        full_name="Reset User One",
        role="user",
    )
    test_auth_manager.create_user(
        username="reset_user2@example.com",
        email="reset_user2@example.com",
        password="password123",
        full_name="Reset User Two",
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
            data={"username": "reset_user1@example.com", "password": "password123"},
        )
        resp2 = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "reset_user2@example.com", "password": "password123"},
        )

        assert resp1.status_code == 200
        assert resp2.status_code == 200

        token1 = resp1.json()["access_token"]
        token2 = resp2.json()["access_token"]

        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        # Both users set up grids and run simulation
        await async_client.post(
            "/api/v1/reservoir/flowsim/setup/grid",
            json={"nx": 10, "dx": 100.0, "area": 100.0},
            headers=headers1,
        )
        await async_client.post(
            "/api/v1/reservoir/flowsim/setup/grid",
            json={"nx": 20, "dx": 50.0, "area": 100.0},
            headers=headers2,
        )

        run_params = {"end_time": 10.0, "dt": 1.0}
        res_run1 = await async_client.post(
            "/api/v1/reservoir/flowsim/run",
            json=run_params,
            headers=headers1,
        )
        res_run2 = await async_client.post(
            "/api/v1/reservoir/flowsim/run",
            json=run_params,
            headers=headers2,
        )

        assert res_run1.status_code == 200
        assert res_run2.status_code == 200

        # User 1 issues /reset
        reset_res = await async_client.post(
            "/api/v1/reservoir/flowsim/reset",
            headers=headers1,
        )
        assert reset_res.status_code == 200
        assert (
            "Session reservoir simulator reset successfully."
            in reset_res.json()["message"]
        )

        # User 2 requests well rates - User 2's completed simulation results remain intact
        rates_res2 = await async_client.get(
            "/api/v1/reservoir/flowsim/results/well_rates",
            headers=headers2,
        )
        assert rates_res2.status_code == 200
        assert rates_res2.json()["status"] == "Completed"

        # User 1 requests well rates - fails with 400 because User 1's simulator was reset
        rates_res1 = await async_client.get(
            "/api/v1/reservoir/flowsim/results/well_rates",
            headers=headers1,
        )
        assert rates_res1.status_code == 400
        assert (
            "Simulation not run or not completed successfully"
            in rates_res1.json()["detail"]
        )

    settings.USE_SESSION_REGISTRY = original_flag


@pytest.mark.asyncio
async def test_flowsim_fallback_global_singleton(
    client, test_db_manager, test_auth_manager, db_session
):
    """
    Verifies that when USE_SESSION_REGISTRY is False, requests fall back to the global
    singleton, reproducing state-bleed where User 2's setup overwrites User 1's simulator setup.
    """
    test_auth_manager.create_user(
        username="fallback_sim1@example.com",
        email="fallback_sim1@example.com",
        password="password123",
        full_name="Fallback Sim One",
        role="user",
    )
    test_auth_manager.create_user(
        username="fallback_sim2@example.com",
        email="fallback_sim2@example.com",
        password="password123",
        full_name="Fallback Sim Two",
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
            data={"username": "fallback_sim1@example.com", "password": "password123"},
        )
        resp2 = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "fallback_sim2@example.com", "password": "password123"},
        )

        assert resp1.status_code == 200
        assert resp2.status_code == 200

        token1 = resp1.json()["access_token"]
        token2 = resp2.json()["access_token"]

        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User 1 sets up 10-cell grid
        grid_u1 = {"nx": 10, "dx": 100.0, "area": 100.0}
        res_g1 = await async_client.post(
            "/api/v1/reservoir/flowsim/setup/grid",
            json=grid_u1,
            headers=headers1,
        )
        assert res_g1.status_code == 200

        # Verify global singleton has nx=10
        assert main.res_simulator.nx == 10

        # User 2 sets up 25-cell grid, mutating global singleton
        grid_u2 = {"nx": 25, "dx": 40.0, "area": 100.0}
        res_g2 = await async_client.post(
            "/api/v1/reservoir/flowsim/setup/grid",
            json=grid_u2,
            headers=headers2,
        )
        assert res_g2.status_code == 200

        # Global singleton was overwritten by User 2, so nx is now 25 for all users
        assert main.res_simulator.nx == 25

    settings.USE_SESSION_REGISTRY = original_flag
