import pandas as pd
import pytest

from app.engines.production.data_uploader import DataUploader


def _write_csv(path, rows):
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _row(date, oil, gas=20.0, water=3.0, pressure=150.0):
    return {
        "data": date,
        "q_oleo": oil,
        "q_gas": gas,
        "q_agua": water,
        "pressao": pressure,
    }


def test_data_uploader_validates_required_columns_and_values(tmp_path):
    uploader = DataUploader()
    valid_file = _write_csv(tmp_path / "valid.csv", [_row("2024-01-01", 10.0)])
    invalid_file = _write_csv(
        tmp_path / "invalid.csv",
        [{"data": "not-a-date", "q_oleo": -1, "q_gas": "bad", "q_agua": 3, "pressao": 150}],
    )
    missing_file = _write_csv(tmp_path / "missing.csv", [{"data": "2024-01-01"}])

    assert uploader.validate_csv(valid_file) == (True, [])
    is_valid, errors = uploader.validate_csv(invalid_file)
    assert not is_valid
    assert any("Negative values in column 'q_oleo'" in error for error in errors)
    assert any("Invalid numeric values in column 'q_gas'" in error for error in errors)
    assert any("Invalid dates in column 'data'" in error for error in errors)
    is_valid, errors = uploader.validate_csv(missing_file)
    assert not is_valid
    assert any("Missing required columns" in error for error in errors)


def test_data_uploader_combines_previews_and_summarizes_well_data(tmp_path):
    uploader = DataUploader()
    first = _write_csv(tmp_path / "first.csv", [_row("2024-02-01", 20.0)])
    second = _write_csv(tmp_path / "second.csv", [_row("2024-01-01", 10.0)])

    combined = uploader.load_well_data("Well A", [first, second])

    assert combined["well_name"].tolist() == ["Well A", "Well A"]
    assert combined["data"].dt.strftime("%Y-%m-%d").tolist() == ["2024-01-01", "2024-02-01"]
    assert len(uploader.get_data_preview("Well A", 1)) == 1
    assert uploader.get_well_statistics("Well A") == {
        "periodo": {"inicio": "2024-01-01", "fim": "2024-02-01"},
        "q_oleo": {"media": 15.0, "max": 20.0, "min": 10.0},
        "q_gas": {"media": 20.0, "max": 20.0, "min": 20.0},
        "q_agua": {"media": 3.0, "max": 3.0, "min": 3.0},
    }
    uploader.clear_cache("Well A")
    with pytest.raises(ValueError, match="No cached data"):
        uploader.get_data_preview("Well A")


def test_data_uploader_rejects_invalid_files_and_empty_well_names(tmp_path):
    uploader = DataUploader()
    invalid = _write_csv(tmp_path / "invalid.csv", [{"data": "2024-01-01"}])

    with pytest.raises(ValueError, match="Invalid production CSV data"):
        uploader.load_well_data("Well A", [invalid])
    with pytest.raises(ValueError, match="Well name must not be empty"):
        uploader.load_well_data(" ", [invalid])
