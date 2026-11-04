import io
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ============================================================
# LAS PARSE TESTS
# ============================================================

def test_las_parse_returns_curves():
    sample_file = FIXTURES_DIR / "sample.las"
    with open(sample_file, "rb") as f:
        response = client.post(
            "/api/petrophysics/las/parse",
            files={"file": ("sample.las", f, "application/octet-stream")},
        )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "well" in data
    assert "curves" in data
    for curve in ["GR", "RHOB", "NPHI"]:
        assert curve in data["curves"]
    assert data["row_count"] > 0
    assert len(data["depth_range"]) == 2
    assert data["depth_range"][0] <= data["depth_range"][1]
    assert "curve_stats" in data
    for curve in ["GR", "RHOB", "NPHI"]:
        assert curve in data["curve_stats"]
        stats = data["curve_stats"][curve]
        assert "min" in stats
        assert "max" in stats
        assert "mean" in stats
        assert "null_count" in stats


def test_las_parse_rejects_non_las_extension():
    response = client.post(
        "/api/petrophysics/las/parse",
        files={"file": ("invalid.txt", b"not a las", "text/plain")},
    )
    assert response.status_code == 422
    assert "Invalid file format" in response.json()["detail"]


def test_las_parse_handles_corrupt_las():
    response = client.post(
        "/api/petrophysics/las/parse",
        files={"file": ("corrupt.las", b"corrupted random data\x00\xff", "application/octet-stream")},
    )
    assert response.status_code == 422
    assert "Failed to parse LAS file" in response.json()["detail"]


def test_las_parse_handles_all_null_curve():
    all_null_las = (
        "~Version Information\n"
        "VERS.   2.0:   CWLS log ASCII Standard -VERSION 2.0\n"
        "WRAP.    NO:   One line per depth step\n"
        "~Well Information\n"
        "STRT .M          100.0 : START DEPTH\n"
        "STOP .M          100.2 : STOP DEPTH\n"
        "STEP .M            0.1 : STEP\n"
        "NULL .          -999.25: NULL VALUE\n"
        "WELL .           NULL-WELL : WELL\n"
        "~Curve Information\n"
        "DEPT .M                : DEPTH\n"
        "GR   .GAPI             : GAMMA RAY\n"
        "~A DEPTH   GR\n"
        "100.0  -999.25\n"
        "100.1  -999.25\n"
        "100.2  -999.25\n"
    )
    file_bytes = io.BytesIO(all_null_las.encode("utf-8"))
    response = client.post(
        "/api/petrophysics/las/parse",
        files={"file": ("null_test.las", file_bytes, "application/octet-stream")},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["row_count"] == 3
    gr_stats = data["curve_stats"]["GR"]
    assert gr_stats["null_count"] == 3
    assert gr_stats["null_count"] == data["row_count"]
    assert gr_stats["min"] is None
    assert gr_stats["max"] is None
    assert gr_stats["mean"] is None


# ============================================================
# FACIES CLASSIFICATION TESTS
# ============================================================

def test_facies_classify_endpoint_with_default_training_data():
    payload = {
        "predict_data": [
            {"gamma": 36.0, "resistivity": 140.0, "density": 2.64, "porosity": 0.09, "depth": 2000.0},
            {"gamma": 120.0, "resistivity": 5.0, "density": 2.36, "porosity": 0.24, "depth": 2001.0},
        ],
        "n_estimators": 50,
    }
    response = client.post("/api/engine/petrophysics/facies/classify", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "facies_predictions" in data
    assert "classes" in data
    assert "features_used" in data
    assert len(data["facies_predictions"]) == 2
    assert data["features_used"] == ["gamma", "resistivity", "density", "porosity"]
    assert data["facies_predictions"][0] == 1
    assert data["facies_predictions"][1] == 3


def test_facies_classify_endpoint_with_custom_training_data():
    payload = {
        "predict_data": [
            {"gamma": 40.0, "resistivity": 100.0, "density": 2.65, "porosity": 0.10}
        ],
        "training_data": [
            {"gamma": 30.0, "resistivity": 120.0, "density": 2.65, "porosity": 0.08, "facies": "Sand"},
            {"gamma": 35.0, "resistivity": 110.0, "density": 2.64, "porosity": 0.09, "facies": "Sand"},
            {"gamma": 110.0, "resistivity": 5.0, "density": 2.35, "porosity": 0.25, "facies": "Shale"},
            {"gamma": 120.0, "resistivity": 4.0, "density": 2.32, "porosity": 0.26, "facies": "Shale"},
        ],
        "n_estimators": 30,
    }
    response = client.post("/api/engine/petrophysics/facies/classify", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["facies_predictions"] == ["Sand"]
    assert "Sand" in data["classes"]
    assert "Shale" in data["classes"]


def test_facies_classify_endpoint_validation_error():
    payload = {"predict_data": []}
    response = client.post("/api/engine/petrophysics/facies/classify", json=payload)
    assert response.status_code == 422