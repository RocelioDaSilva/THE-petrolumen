from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

EXPECTED_TAGS = {
    "/api/engine/pvt/eos":             "PVT",
    "/api/engine/drilling/trajectory": "Drilling",
    "/api/engine/geology/grid":        "Geology",
    "/api/engine/reservoir/nodal":     "Reservoir",
    "/api/simulate/black-oil":         "Simulation",
    "/api/simulate/compositional":     "Simulation",
    "/api/simulate/thermal":           "Simulation",
}

def test_all_seven_routes_are_tagged():
    spec = client.get("/openapi.json").json()
    for path, tag in EXPECTED_TAGS.items():
        assert path in spec["paths"], f"route {path} missing from schema"
        post = spec["paths"][path].get("post")
        assert post is not None, f"{path} has no POST operation"
        assert tag in post.get("tags", []), f"{path} missing tag {tag}"

def test_docs_renders():
    r = client.get("/docs")
    assert r.status_code == 200
    assert "swagger" in r.text.lower()

def test_grid_endpoint_roundtrip():
    r = client.post("/api/engine/geology/grid",
                    json={"nx": 2, "ny": 2, "nz": 1, "dx": 50, "dy": 50, "dz": 10})
    assert r.status_code == 200
