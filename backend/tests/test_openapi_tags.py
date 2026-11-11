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


def test_every_endpoint_has_documented_responses():
    spec = client.get("/openapi.json").json()
    paths = spec.get("paths", {})
    assert len(paths) >= 12
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "delete", "patch"}:
                continue
            responses = operation.get("responses", {})
            success_codes = {code for code in responses if code.startswith("2")}
            assert success_codes or "307" in responses or "501" in responses, (
                f"{method.upper()} {path} missing standard response"
            )
            # Verify documented response schema exists
            target_code = (
                "501"
                if "501" in responses
                else (sorted(success_codes)[0] if success_codes else list(responses.keys())[0])
            )
            resp_obj = responses[target_code]
            content = resp_obj.get("content", {})
            if target_code == "204":
                assert not content, f"{method.upper()} {path} 204 response must not have content"
                continue
            json_media = content.get("application/json", {})
            schema = json_media.get("schema", {})
            assert schema, f"{method.upper()} {path} response {target_code} has no schema"
            assert "$ref" in schema or schema.get("type") or schema.get("properties"), (
                f"{method.upper()} {path} schema is empty: {schema}"
            )
