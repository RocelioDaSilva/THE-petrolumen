from typing import List, Dict, Any
import pandas as pd

class DataUploader:
    def load_well_data(self, well_name: str, csv_files: List[str]) -> pd.DataFrame:
        """Loads and merges data from multiple CSVs for a given well."""
        pass

    def get_data_preview(self, well_name: str, n_rows: int = 5) -> pd.DataFrame:
        """Returns a preview (e.g., head) of the loaded data."""
        pass

    def get_well_statistics(self, well_name: str) -> Dict[str, Any]:
        """Calculates and returns descriptive statistics for a well's data."""
        pass

    # Implied validation methods
    def _validate_columns(self, df: pd.DataFrame) -> bool:
        """Validates the columns of the dataframe."""
        pass

    def _validate_data_types(self, df: pd.DataFrame) -> bool:
        """Validates the data types of the dataframe."""
        pass
