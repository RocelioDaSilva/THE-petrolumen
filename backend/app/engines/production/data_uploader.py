from pathlib import Path

import pandas as pd


class DataUploader:
    """Validate, combine, preview, and summarize well production CSV data."""

    required_columns = {
        "q_oleo",
        "q_gas",
        "q_agua",
        "pressao",
        "data",
    }
    rate_columns = ("q_oleo", "q_gas", "q_agua", "pressao")

    def __init__(self) -> None:
        self.data_cache: dict[str, pd.DataFrame] = {}

    def validate_csv(self, file_path: str | Path) -> tuple[bool, list[str]]:
        path = Path(file_path)
        try:
            data = pd.read_csv(path)
        except (OSError, UnicodeDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
            return False, [f"Unable to read CSV '{path}': {exc}"]

        errors: list[str] = []
        missing_columns = self.required_columns.difference(data.columns)
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(sorted(missing_columns))}")

        for column in self.rate_columns:
            if column not in data:
                continue
            values = pd.to_numeric(data[column], errors="coerce")
            if values.isna().any():
                errors.append(f"Invalid numeric values in column '{column}'")
            elif (values < 0).any():
                errors.append(f"Negative values in column '{column}'")

        if "data" in data:
            dates = pd.to_datetime(data["data"], errors="coerce")
            if dates.isna().any():
                errors.append("Invalid dates in column 'data'")

        null_columns = data.columns[data.isna().any()].tolist()
        if null_columns:
            errors.append(f"Null values in columns: {', '.join(null_columns)}")

        return not errors, errors

    def load_well_data(self, well_name: str, csv_files: list[str | Path]) -> pd.DataFrame:
        if not well_name.strip():
            raise ValueError("Well name must not be empty.")
        if not csv_files:
            raise ValueError("At least one CSV file is required.")

        frames: list[pd.DataFrame] = []
        failures: list[str] = []
        for file_path in csv_files:
            is_valid, errors = self.validate_csv(file_path)
            if not is_valid:
                failures.extend(f"{file_path}: {error}" for error in errors)
                continue
            frame = pd.read_csv(file_path)
            frame["data"] = pd.to_datetime(frame["data"])
            frame["well_name"] = well_name
            frames.append(frame)

        if failures:
            raise ValueError("Invalid production CSV data: " + "; ".join(failures))
        if not frames:
            raise ValueError("No valid CSV files were provided.")

        combined = pd.concat(frames, ignore_index=True).sort_values("data").reset_index(drop=True)
        self.data_cache[well_name] = combined
        return combined.copy()

    def get_data_preview(self, well_name: str, n_rows: int = 5) -> pd.DataFrame:
        if well_name not in self.data_cache:
            raise ValueError(f"No cached data found for well '{well_name}'.")
        if n_rows < 0:
            raise ValueError("Preview row count must not be negative.")
        return self.data_cache[well_name].head(n_rows).copy()

    def get_well_statistics(self, well_name: str) -> dict[str, dict[str, str | float]]:
        if well_name not in self.data_cache:
            raise ValueError(f"No cached data found for well '{well_name}'.")

        data = self.data_cache[well_name]
        statistics: dict[str, dict[str, str | float]] = {
            "periodo": {
                "inicio": data["data"].min().strftime("%Y-%m-%d"),
                "fim": data["data"].max().strftime("%Y-%m-%d"),
            }
        }
        for column in ("q_oleo", "q_gas", "q_agua"):
            statistics[column] = {
                "media": float(data[column].mean()),
                "max": float(data[column].max()),
                "min": float(data[column].min()),
            }
        return statistics

    def clear_cache(self, well_name: str | None = None) -> None:
        if well_name is None:
            self.data_cache.clear()
        else:
            self.data_cache.pop(well_name, None)
