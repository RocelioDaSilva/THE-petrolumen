from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_facies_classify_endpoint_with_default_training_data():
    payload = {
        "predict_data": [
            {
                "gamma": 36.0,
                "resistivity": 140.0,
                "density": 2.64,
                "porosity": 0.09,
                "depth": 2000.0,
            },
            {
                "gamma": 120.0,
                "resistivity": 5.0,
                "density": 2.36,
                "porosity": 0.24,
                "depth": 2001.0,
            },
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
            {
                "gamma": 40.0,
                "resistivity": 100.0,
                "density": 2.65,
                "porosity": 0.10,
            }
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
    payload = {
        "predict_data": [],
    }
    response = client.post("/api/engine/petrophysics/facies/classify", json=payload)
    assert response.status_code == 422
