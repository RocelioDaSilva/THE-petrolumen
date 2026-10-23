import pytest
import asyncio
from httpx import AsyncClient, ASGITransport

from main import app


@pytest.mark.asyncio
async def test_flowsim_run_async_and_poll_job(
    client, test_db_manager, test_auth_manager, db_session
):
    """
    Tests submitting a flow simulation job asynchronously via /run_async,
    verifying 202 Accepted response with job_id, polling /api/v1/jobs/{job_id}
    until completed, and validating the result payload.
    """
    test_auth_manager.create_user(
        username="bg_flowsim_user@example.com",
        email="bg_flowsim_user@example.com",
        password="password123",
        full_name="BG Flowsim User",
        role="user",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as async_client:
        auth_resp = await async_client.post(
            "/api/v1/auth/token",
            data={
                "username": "bg_flowsim_user@example.com",
                "password": "password123",
            },
        )
        assert auth_resp.status_code == 200
        token = auth_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Submit flow simulation run_async
        run_params = {"end_time": 10.0, "dt": 1.0}
        post_resp = await async_client.post(
            "/api/v1/reservoir/flowsim/run_async",
            json=run_params,
            headers=headers,
        )

        assert post_resp.status_code == 202
        data = post_resp.json()
        assert "job_id" in data
        assert data["status"] == "pending"

        job_id = data["job_id"]

        # Poll job status until completed
        max_retries = 20
        job_data = None
        for _ in range(max_retries):
            get_resp = await async_client.get(
                f"/api/v1/jobs/{job_id}",
                headers=headers,
            )
            assert get_resp.status_code == 200
            job_data = get_resp.json()
            if job_data["status"] in ["completed", "failed"]:
                break
            await asyncio.sleep(0.1)

        assert job_data is not None
        assert job_data["status"] == "completed"
        assert job_data["error"] is None
        assert job_data["result"] is not None
        assert "time_steps" in job_data["result"]
        assert "pressure_at_block" in job_data["result"]
        assert job_data["result"]["status"] == "Completed"


@pytest.mark.asyncio
async def test_prediction_train_async_and_poll_job(
    client, test_db_manager, test_auth_manager, db_session
):
    """
    Tests submitting an AI training job asynchronously via /train_async,
    verifying 202 Accepted response with job_id, polling /api/v1/jobs/{job_id}
    until completed, and validating the training result payload.
    """
    test_auth_manager.create_user(
        username="bg_train_user@example.com",
        email="bg_train_user@example.com",
        password="password123",
        full_name="BG Train User",
        role="user",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as async_client:
        auth_resp = await async_client.post(
            "/api/v1/auth/token",
            data={
                "username": "bg_train_user@example.com",
                "password": "password123",
            },
        )
        assert auth_resp.status_code == 200
        token = auth_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create dummy training data records
        records = [
            {"feat1": float(i), "feat2": float(i * 2), "target": float(i * 3 + 1)}
            for i in range(20)
        ]
        train_payload = {
            "records": records,
            "target_column": "target",
            "feature_columns": ["feat1", "feat2"],
        }

        post_resp = await async_client.post(
            "/api/v1/reservoir/prediction/train_async",
            json=train_payload,
            headers=headers,
        )

        assert post_resp.status_code == 202
        data = post_resp.json()
        assert "job_id" in data
        assert data["status"] == "pending"

        job_id = data["job_id"]

        # Poll job status until completed
        max_retries = 20
        job_data = None
        for _ in range(max_retries):
            get_resp = await async_client.get(
                f"/api/v1/jobs/{job_id}",
                headers=headers,
            )
            assert get_resp.status_code == 200
            job_data = get_resp.json()
            if job_data["status"] in ["completed", "failed"]:
                break
            await asyncio.sleep(0.1)

        assert job_data is not None
        assert job_data["status"] == "completed"
        assert job_data["error"] is None
        assert job_data["result"] is not None
        assert "trained_models" in job_data["result"]
        assert "performance" in job_data["result"]
        assert "best_model" in job_data["result"]


@pytest.mark.asyncio
async def test_job_authorization_isolation(
    client, test_db_manager, test_auth_manager, db_session
):
    """
    Verifies that a user cannot retrieve the job status or result of a job
    belonging to another user (enforces HTTP 403 Forbidden).
    """
    test_auth_manager.create_user(
        username="user_a_bg@example.com",
        email="user_a_bg@example.com",
        password="password123",
        full_name="User A BG",
        role="user",
    )
    test_auth_manager.create_user(
        username="user_b_bg@example.com",
        email="user_b_bg@example.com",
        password="password123",
        full_name="User B BG",
        role="user",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as async_client:
        auth_a = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "user_a_bg@example.com", "password": "password123"},
        )
        auth_b = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "user_b_bg@example.com", "password": "password123"},
        )

        assert auth_a.status_code == 200
        assert auth_b.status_code == 200

        token_a = auth_a.json()["access_token"]
        token_b = auth_b.json()["access_token"]

        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User A submits job
        post_resp = await async_client.post(
            "/api/v1/reservoir/flowsim/run_async",
            json={"end_time": 10.0, "dt": 1.0},
            headers=headers_a,
        )
        assert post_resp.status_code == 202
        job_id = post_resp.json()["job_id"]

        # User A can access job
        get_a = await async_client.get(
            f"/api/v1/jobs/{job_id}",
            headers=headers_a,
        )
        assert get_a.status_code == 200

        # User B attempts to access User A's job -> 403 Forbidden
        get_b = await async_client.get(
            f"/api/v1/jobs/{job_id}",
            headers=headers_b,
        )
        assert get_b.status_code == 403
        assert "Not authorized" in get_b.json()["detail"]


@pytest.mark.asyncio
async def test_get_nonexistent_job(
    client, test_db_manager, test_auth_manager, db_session
):
    """Verifies 404 Not Found when requesting a non-existent job_id."""
    test_auth_manager.create_user(
        username="nonexistent_job_user@example.com",
        email="nonexistent_job_user@example.com",
        password="password123",
        full_name="Nonexistent Job User",
        role="user",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as async_client:
        auth_resp = await async_client.post(
            "/api/v1/auth/token",
            data={
                "username": "nonexistent_job_user@example.com",
                "password": "password123",
            },
        )
        assert auth_resp.status_code == 200
        token = auth_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        fake_uuid = "00000000-0000-0000-0000-000000000000"
        get_resp = await async_client.get(
            f"/api/v1/jobs/{fake_uuid}",
            headers=headers,
        )
        assert get_resp.status_code == 404
        assert "Job not found" in get_resp.json()["detail"]


@pytest.mark.asyncio
async def test_get_job_invalid_id_format(
    client, test_db_manager, test_auth_manager, db_session
):
    """Verifies 400 Bad Request when requesting job with invalid UUID string."""
    test_auth_manager.create_user(
        username="invalid_job_user@example.com",
        email="invalid_job_user@example.com",
        password="password123",
        full_name="Invalid Job User",
        role="user",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as async_client:
        auth_resp = await async_client.post(
            "/api/v1/auth/token",
            data={
                "username": "invalid_job_user@example.com",
                "password": "password123",
            },
        )
        assert auth_resp.status_code == 200
        token = auth_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        get_resp = await async_client.get(
            "/api/v1/jobs/not-a-valid-uuid",
            headers=headers,
        )
        assert get_resp.status_code == 400
        assert "Invalid job_id format" in get_resp.json()["detail"]
