import pandas as pd

class DataUploader:
    def __init__(self):
        self.well_data = {}

    def load_well_data(self, well_name: str, csv_files: list[str]) -> None:
        """Loads and merges data from multiple CSVs for a given well."""
        if not csv_files:
            raise ValueError("No CSV files provided.")

        all_data = []
        for file_path in csv_files:
            try:
                df = pd.read_csv(file_path)
                all_data.append(df)
            except FileNotFoundError:
                print(f"Warning: File not found {file_path}")
            except pd.errors.EmptyDataError:
                print(f"Warning: No data in file {file_path}")
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

        if not all_data:
            self.well_data[well_name] = pd.DataFrame()
            print(f"No data loaded for well {well_name}.")
            return

        # Assuming CSVs for the same well might have overlapping time periods
        # or different sets of columns. We'll concatenate and then handle duplicates.
        # A more sophisticated merge strategy might be needed depending on data structure.
        merged_df = pd.concat(all_data, ignore_index=True)

        # Example: Drop duplicate rows if any, based on all columns
        merged_df.drop_duplicates(inplace=True)

        # Store the processed data
        self.well_data[well_name] = merged_df
        print(f"Data loaded and merged for well {well_name}. Shape: {merged_df.shape}")

    def get_data_preview(self, well_name: str, n_rows: int = 5) -> pd.DataFrame:
        """Returns a preview (e.g., head) of the loaded data for a well."""
        if well_name not in self.well_data:
            raise ValueError(f"No data loaded for well {well_name}.")
        return self.well_data[well_name].head(n_rows)

    def get_well_statistics(self, well_name: str) -> pd.DataFrame:
        """Calculates and returns descriptive statistics for a well's data."""
        if well_name not in self.well_data:
            raise ValueError(f"No data loaded for well {well_name}.")
        if self.well_data[well_name].empty:
            return pd.DataFrame(data={"message": [f"No data available to calculate statistics for well {well_name}."]})
        return self.well_data[well_name].describe(include='all')

    def _validate_columns(self, df: pd.DataFrame, required_columns: dict) -> bool:
        """
        Validates if the DataFrame contains required columns and if their data types match.
        required_columns should be a dict like {'col_name': expected_type}
        e.g. {'date': 'datetime64[ns]', 'rate': 'float64'}
        """
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            print(f"Validation Error: Missing columns: {missing_cols}")
            return False

        for col, expected_type_str in required_columns.items():
            actual_type = df[col].dtype
            # Basic type checking, can be expanded
            if expected_type_str == 'datetime64[ns]' and not pd.api.types.is_datetime64_any_dtype(actual_type):
                try:
                    # Attempt to convert if not already datetime
                    df[col] = pd.to_datetime(df[col])
                    actual_type = df[col].dtype # update actual type
                except Exception as e:
                    print(f"Validation Error: Column '{col}' could not be converted to datetime. Error: {e}")
                    return False

            if not pd.api.types.is_dtype_equal(actual_type, expected_type_str):
                # Allow for int vs float flexibility if values are compatible
                if pd.api.types.is_numeric_dtype(actual_type) and pd.api.types.is_numeric_dtype(pd.Series([], dtype=expected_type_str).dtype):
                    try:
                        df[col] = df[col].astype(expected_type_str)
                    except Exception as e:
                         print(f"Validation Error: Column '{col}' type is {actual_type} but expected {expected_type_str}. Attempted conversion failed: {e}")
                         return False
                else:
                    print(f"Validation Error: Column '{col}' type is {actual_type} but expected {expected_type_str}.")
                    return False
        print("Column validation successful.")
        return True

# Example Usage (optional, for testing purposes)
if __name__ == '__main__':
    uploader = DataUploader()

    # Create dummy CSV files for testing
    data1 = {'date': ['2023-01-01', '2023-01-02'], 'oil_rate': [100, 105], 'gas_rate': [50,52]}
    df1 = pd.DataFrame(data1)
    df1.to_csv('wellA_part1.csv', index=False)

    data2 = {'date': ['2023-01-03', '2023-01-04'], 'oil_rate': [110, 115], 'water_cut': [0.1, 0.12]}
    df2 = pd.DataFrame(data2)
    df2.to_csv('wellA_part2.csv', index=False)

    try:
        uploader.load_well_data('WellA', ['wellA_part1.csv', 'wellA_part2.csv'])
        print("\nData Preview for WellA:")
        print(uploader.get_data_preview('WellA'))

        print("\nStatistics for WellA:")
        print(uploader.get_well_statistics('WellA'))

        # Test validation
        well_a_df = uploader.well_data['WellA'].copy()
        print("\nValidating WellA data:")
        # Example: Convert 'date' column to datetime before validation if it's not already
        if 'date' in well_a_df.columns:
             well_a_df['date'] = pd.to_datetime(well_a_df['date'])

        required = {'date': 'datetime64[ns]', 'oil_rate': 'int64', 'gas_rate': 'float64'} # gas_rate will be float after merge due to NaN
        uploader._validate_columns(well_a_df, required)

    except ValueError as e:
        print(f"Error: {e}")
    finally:
        # Clean up dummy files
        import os
        if os.path.exists('wellA_part1.csv'):
            os.remove('wellA_part1.csv')
        if os.path.exists('wellA_part2.csv'):
            os.remove('wellA_part2.csv')
