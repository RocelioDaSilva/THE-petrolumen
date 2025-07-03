from typing import List, Dict, Any, Tuple
import pandas as pd
import io

# In-memory storage for demonstration purposes
# In a real application, this would be a database or a more robust storage solution.
_well_data_store: Dict[str, pd.DataFrame] = {}

class DataUploader:
    """
    Manages data loading, validation, and retrieval for well data.
    NOTE: Current implementation uses in-memory storage and basic logic for demonstration.
    """

    def load_well_data(self, well_name: str, csv_files_content: List[Tuple[str, str]]) -> Tuple[bool, str, pd.DataFrame | None]:
        """
        Loads and merges data from multiple CSV file contents for a given well.
        Args:
            well_name: The name of the well.
            csv_files_content: A list of tuples, where each tuple contains (filename, file_content_as_string).
        Returns:
            A tuple (success: bool, message: str, data: pd.DataFrame | None).
        """
        all_dfs = []
        try:
            for filename, content_str in csv_files_content:
                # Basic validation: check if content is not empty
                if not content_str.strip():
                    return False, f"File {filename} is empty.", None

                df = pd.read_csv(io.StringIO(content_str))

                # Basic validation: check if DataFrame is empty after read
                if df.empty:
                    return False, f"File {filename} resulted in an empty dataset (is it a valid CSV?).", None

                # TODO: Add more robust validation (columns, data types) here
                # if not self._validate_columns(df):
                #     return False, f"Invalid columns in {filename}.", None
                # if not self._validate_data_types(df):
                #     return False, f"Invalid data types in {filename}.", None

                all_dfs.append(df)

            if not all_dfs:
                return False, "No data files provided or all files were empty/invalid.", None

            merged_df = pd.concat(all_dfs, ignore_index=True)
            _well_data_store[well_name] = merged_df
            return True, f"Data for well '{well_name}' loaded successfully from {len(all_dfs)} file(s).", merged_df
        except pd.errors.EmptyDataError:
            return False, f"One of the files for well '{well_name}' was empty or not a valid CSV.", None
        except Exception as e:
            return False, f"Error loading data for well '{well_name}': {str(e)}", None

    def get_data_preview(self, well_name: str, n_rows: int = 5) -> pd.DataFrame | None:
        """Returns a preview (e.g., head) of the loaded data for a well."""
        if well_name in _well_data_store:
            return _well_data_store[well_name].head(n_rows)
        return None

    def get_well_statistics(self, well_name: str) -> Dict[str, Any] | None:
        """Calculates and returns descriptive statistics for a well's data."""
        if well_name in _well_data_store:
            df = _well_data_store[well_name]
            # Example statistics, can be expanded
            stats = {
                "rows": len(df),
                "columns": list(df.columns),
                "description": df.describe(include='all').to_dict()
            }
            return stats
        return None

    def _validate_columns(self, df: pd.DataFrame) -> bool:
        """Placeholder for column validation logic."""
        # Example: Check for specific required columns
        # required_cols = ["Date", "OilRate", "GasRate", "WaterRate"]
        # return all(col in df.columns for col in required_cols)
        return True # Basic implementation returns true

    def _validate_data_types(self, df: pd.DataFrame) -> bool:
        """Placeholder for data type validation logic."""
        # Example: Check if 'Date' column can be parsed as datetime
        # try:
        #     pd.to_datetime(df["Date"])
        #     return True
        # except Exception:
        #     return False
        return True # Basic implementation returns true

    def list_loaded_wells(self) -> List[str]:
        """Returns a list of well names for which data has been loaded."""
        return list(_well_data_store.keys())

# Helper to clear the store, e.g., for testing or specific scenarios
def clear_data_store():
    _well_data_store.clear()
