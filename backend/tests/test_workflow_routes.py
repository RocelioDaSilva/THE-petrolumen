from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_ooip_upload_returns_session():
    sample_file = FIXTURES_DIR / "sample.las"
    with open(sample_file, "rb") as f:
        response = client.post(
            "/api/workflow/ooip/upload",
            files={"file": ("sample.las", f, "application/octet-stream")},
        )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "session_id" in data
    assert len(data["session_id"]) == 32
    assert "curve_list" in data
    assert len(data["curve_list"]) > 0
    assert "well_summary" in data
    assert "depth_range" in data


def test_ooip_run_with_valid_session():
    sample_file = FIXTURES_DIR / "sample.las"
    with open(sample_file, "rb") as f:
        upload_resp = client.post(
            "/api/workflow/ooip/upload",
            files={"file": ("sample.las", f, "application/octet-stream")},
        )
    assert upload_resp.status_code == 200
    session_id = upload_resp.json()["session_id"]

    run_payload = {
        "session_id": session_id,
        "area_acres": 100.0,
        "net_to_gross_cutoff": 0.1,
        "water_saturation_method": "archie",
        "archie_params": {
            "a": 1.0,
            "m": 2.0,
            "n": 2.0,
            "Rw": 0.1,
        },
    }
    response = client.post("/api/workflow/ooip/run", json=run_payload)
    assert response.status_code == 200, response.text
    data = response.json()

    expected_keys = [
        "net_pay_ft",
        "gross_pay_ft",
        "net_to_gross",
        "average_porosity",
        "average_sw",
        "ooip_bbl",
        "ooip_stb_per_acre_ft",
        "facies_breakdown",
        "per_curve_summary",
        "note",
    ]
    for key in expected_keys:
        assert key in data, f"Key {key} missing from response"

    assert data["ooip_bbl"] > 0
    assert data["ooip_stb_per_acre_ft"] > 0
    assert data["net_pay_ft"] > 0
    assert data["gross_pay_ft"] > 0


def test_ooip_run_with_unknown_session():
    run_payload = {
        "session_id": "nonexistent",
        "area_acres": 100.0,
    }
    response = client.post("/api/workflow/ooip/run", json=run_payload)
    assert response.status_code == 404
    assert "Session not found or expired" in response.json()["detail"]


def test_ooip_run_validates_area():
    run_payload = {
        "session_id": "any_id",
        "area_acres": 0,
    }
    response = client.post("/api/workflow/ooip/run", json=run_payload)
    assert response.status_code == 422
