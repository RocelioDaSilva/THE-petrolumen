import pytest
import asyncio
from httpx import AsyncClient, ASGITransport

from main import app
from config import settings


@pytest.mark.asyncio
async def test_ai_predictor_concurrency_isolation(
    client, test_db_manager, test_auth_manager, db_session
):
    """
    Verifies that when USE_SESSION_REGISTRY is True, two users training models
    concurrently with different feature sets remain completely isolated and do not
    experience feature mismatch errors during prediction.
    """
    user1_dict = test_auth_manager.create_user(
        username="user1_ai@example.com",
        email="user1_ai@example.com",
        password="password123",
        full_name="User One",
        role="user",
    )
    user2_dict = test_auth_manager.create_user(
        username="user2_ai@example.com",
        email="user2_ai@example.com",
        password="password123",
        full_name="User Two",
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
            data={"username": "user1_ai@example.com", "password": "password123"},
        )
        resp2 = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "user2_ai@example.com", "password": "password123"},
        )

        assert resp1.status_code == 200, f"Login 1 failed: {resp1.text}"
        assert resp2.status_code == 200, f"Login 2 failed: {resp2.text}"

        token1 = resp1.json()["access_token"]
        token2 = resp2.json()["access_token"]

        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User 1 Dataset A
        data_user1 = {
            "records": [
                {
                    "porosity": 0.15 + i * 0.01,
                    "permeability": 50 + i * 5,
                    "oil_rate": 100 + i * 10,
                }
                for i in range(20)
            ],
            "target_column": "oil_rate",
            "feature_columns": ["porosity", "permeability"],
        }

        # User 2 Dataset B
        data_user2 = {
            "records": [
                {
                    "depth": 2000 + i * 100,
                    "pressure": 3000 + i * 50,
                    "temperature": 150 + i * 2,
                    "gas_rate": 500 + i * 20,
                }
                for i in range(20)
            ],
            "target_column": "gas_rate",
            "feature_columns": ["depth", "pressure", "temperature"],
        }

        # Concurrent training
        res1_train, res2_train = await asyncio.gather(
            async_client.post(
                "/api/v1/reservoir/prediction/train", json=data_user1, headers=headers1
            ),
            async_client.post(
                "/api/v1/reservoir/prediction/train", json=data_user2, headers=headers2
            ),
        )

        assert res1_train.status_code == 200, f"User 1 train failed: {res1_train.text}"
        assert res2_train.status_code == 200, f"User 2 train failed: {res2_train.text}"

        # Prediction requests
        predict_req1 = {
            "records": [{"porosity": 0.18, "permeability": 65}],
            "feature_columns": ["porosity", "permeability"],
        }
        predict_req2 = {
            "records": [{"depth": 2500, "pressure": 3250, "temperature": 160}],
            "feature_columns": ["depth", "pressure", "temperature"],
        }

        res1_pred, res2_pred = await asyncio.gather(
            async_client.post(
                "/api/v1/reservoir/prediction/predict",
                json=predict_req1,
                headers=headers1,
            ),
            async_client.post(
                "/api/v1/reservoir/prediction/predict",
                json=predict_req2,
                headers=headers2,
            ),
        )

        assert res1_pred.status_code == 200, f"User 1 predict failed: {res1_pred.text}"
        assert res2_pred.status_code == 200, f"User 2 predict failed: {res2_pred.text}"

        pred1_data = res1_pred.json().get("predictions", {})
        pred2_data = res2_pred.json().get("predictions", {})

        assert len(pred1_data) > 0
        assert len(pred2_data) > 0

    settings.USE_SESSION_REGISTRY = original_flag


@pytest.mark.asyncio
async def test_ai_predictor_fallback_global_singleton(
    client, test_db_manager, test_auth_manager, db_session
):
    """
    Verifies that when USE_SESSION_REGISTRY is False, requests fall back to the global
    singleton, reproducing the state-bleed defect where User 2 overwrites User 1's model.
    """
    user1_dict = test_auth_manager.create_user(
        username="fallback_user1@example.com",
        email="fallback_user1@example.com",
        password="password123",
        full_name="Fallback User One",
        role="user",
    )
    user2_dict = test_auth_manager.create_user(
        username="fallback_user2@example.com",
        email="fallback_user2@example.com",
        password="password123",
        full_name="Fallback User Two",
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
            data={"username": "fallback_user1@example.com", "password": "password123"},
        )
        resp2 = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "fallback_user2@example.com", "password": "password123"},
        )

        assert resp1.status_code == 200
        assert resp2.status_code == 200

        token1 = resp1.json()["access_token"]
        token2 = resp2.json()["access_token"]

        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User 1 trains with porosity and permeability
        data_user1 = {
            "records": [
                {
                    "porosity": 0.15 + i * 0.01,
                    "permeability": 50 + i * 5,
                    "oil_rate": 100 + i * 10,
                }
                for i in range(20)
            ],
            "target_column": "oil_rate",
            "feature_columns": ["porosity", "permeability"],
        }
        res1_train = await async_client.post(
            "/api/v1/reservoir/prediction/train", json=data_user1, headers=headers1
        )
        assert res1_train.status_code == 200

        # User 2 trains with different feature columns, overwriting global singleton
        data_user2 = {
            "records": [
                {
                    "depth": 2000 + i * 100,
                    "pressure": 3000 + i * 50,
                    "temperature": 150 + i * 2,
                    "gas_rate": 500 + i * 20,
                }
                for i in range(20)
            ],
            "target_column": "gas_rate",
            "feature_columns": ["depth", "pressure", "temperature"],
        }
        res2_train = await async_client.post(
            "/api/v1/reservoir/prediction/train", json=data_user2, headers=headers2
        )
        assert res2_train.status_code == 200

        # User 1 attempts prediction with User 1's features
        predict_req1 = {
            "records": [{"porosity": 0.18, "permeability": 65}],
            "feature_columns": ["porosity", "permeability"],
        }
        res1_pred = await async_client.post(
            "/api/v1/reservoir/prediction/predict", json=predict_req1, headers=headers1
        )

        # Global singleton was mutated by User 2, so User 1 gets 400 feature mismatch
        assert res1_pred.status_code == 400
        assert "Prediction data missing required feature columns" in res1_pred.text

    settings.USE_SESSION_REGISTRY = original_flag
