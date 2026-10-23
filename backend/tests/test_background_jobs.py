import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_flowsim_run_async_and_poll_job(
    client, test_user, user_auth_headers, test_db_manager
):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post(
            "/api/v1/reservoir/flowsim/run_async",
            json={"end_time": 10.0, "dt": 1.0},
            headers=user_auth_headers,
        )
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        job_id = data["job_id"]

        # Poll job status
        completed = False
        for _ in range(30):
            job_resp = await ac.get(
                f"/api/v1/jobs/{job_id}", headers=user_auth_headers
            )
            assert job_resp.status_code == 200
            job_data = job_resp.json()
            assert job_data["id"] == job_id
            if job_data["status"] == "completed":
                completed = True
                assert "result" in job_data
                assert job_data["result"] is not None
                assert "time_steps" in job_data["result"]
                assert "pressure_at_block" in job_data["result"]
                break
            elif job_data["status"] == "failed":
                pytest.fail(f"Job failed with error: {job_data.get('error')}")
            await asyncio.sleep(0.1)

        assert completed, "Job did not complete in time"


@pytest.mark.asyncio
async def test_prediction_train_async_and_poll_job(
    client, test_user, user_auth_headers, test_db_manager
):
    sample_records = [
        {"feat1": 1.0, "feat2": 2.0, "target": 10.0},
        {"feat1": 2.0, "feat2": 3.0, "target": 20.0},
        {"feat1": 3.0, "feat2": 4.0, "target": 30.0},
        {"feat1": 4.0, "feat2": 5.0, "target": 40.0},
        {"feat1": 5.0, "feat2": 6.0, "target": 50.0},
    ]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post(
            "/api/v1/reservoir/prediction/train_async",
            json={
                "records": sample_records,
                "target_column": "target",
                "feature_columns": ["feat1", "feat2"],
            },
            headers=user_auth_headers,
        )
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        job_id = data["job_id"]

        completed = False
        for _ in range(30):
            job_resp = await ac.get(
                f"/api/v1/jobs/{job_id}", headers=user_auth_headers
            )
            assert job_resp.status_code == 200
            job_data = job_resp.json()
            if job_data["status"] == "completed":
                completed = True
                assert "result" in job_data
                assert job_data["result"] is not None
                assert "trained_models" in job_data["result"]
                assert "best_model" in job_data["result"]
                break
            elif job_data["status"] == "failed":
                pytest.fail(f"Job failed with error: {job_data.get('error')}")
            await asyncio.sleep(0.1)

        assert completed, "AI training job did not complete in time"


@pytest.mark.asyncio
async def test_job_access_control(
    client, test_user, user_auth_headers, test_auth_manager
):
    # Create User B
    user_b_details = test_auth_manager.create_user(
        username="user_b@example.com",
        email="user_b@example.com",
        password="userbpassword123",
        full_name="User B",
        role="user",
    )
    assert user_b_details is not None

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # User A creates a job
        response = await ac.post(
            "/api/v1/reservoir/flowsim/run_async",
            json={"end_time": 5.0, "dt": 1.0},
            headers=user_auth_headers,
        )
        assert response.status_code == 202
        job_id = response.json()["job_id"]

        # Authenticate User B
        login_resp = await ac.post(
            "/api/v1/auth/token",
            data={"username": "user_b@example.com", "password": "userbpassword123"},
        )
        assert login_resp.status_code == 200
        token_b = login_resp.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User B attempts to access User A's job
        job_resp = await ac.get(f"/api/v1/jobs/{job_id}", headers=headers_b)
        assert job_resp.status_code == 403
        assert "Access forbidden" in job_resp.json()["detail"]


@pytest.mark.asyncio
async def test_non_existent_job_returns_404(client, user_auth_headers):
    fake_job_id = "00000000-0000-0000-0000-000000000000"
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        job_resp = await ac.get(f"/api/v1/jobs/{fake_job_id}", headers=user_auth_headers)
        assert job_resp.status_code == 404
