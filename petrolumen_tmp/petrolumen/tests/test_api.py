from fastapi.testclient import TestClient

# Local import adjusted for running tests from repository root
from backend.main import app


client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
