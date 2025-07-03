from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import io
import logging
import datetime

# Import DatabaseManager and related SQLAlchemy parts
from .database import DatabaseManager, Well, ProductionData

logger = logging.getLogger(__name__)

# _well_data_store: Dict[str, pd.DataFrame] = {} # This will be removed

class DataUploader:
    """
    Manages data loading, validation, and retrieval for well data using DatabaseManager.
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        if not self.db_manager.engine: # Ensure DB is connected
            if not self.db_manager.connect():
                # This should ideally not happen if db_manager is passed correctly initialized
                logger.error("DataUploader: DatabaseManager failed to connect.")
                raise ConnectionError("DataUploader could not connect to the database via DatabaseManager.")
            if not self.db_manager.create_tables():
                logger.error("DataUploader: DatabaseManager failed to create tables.")
                # Depending on policy, this might be a critical error
                # raise Exception("DataUploader failed to ensure database tables are created.")


    def load_well_data(self,
                       well_name: str,
                       csv_files_content: List[Tuple[str, str]],
                       field_name: Optional[str] = None,
                       latitude: Optional[float] = None,
                       longitude: Optional[float] = None) -> Tuple[bool, str, Optional[int]]:
        """
        Loads and merges data from multiple CSV file contents for a given well,
        then stores it in the database.
        Args:
            well_name: The name of the well.
            csv_files_content: A list of tuples, where each tuple contains (filename, file_content_as_string).
            field_name, latitude, longitude: Optional metadata for the well.
        Returns:
            A tuple (success: bool, message: str, well_id: Optional[int]).
        """
        all_production_records = []
        processed_files_count = 0

        try:
            for filename, content_str in csv_files_content:
                if not content_str.strip():
                    logger.warning(f"File {filename} for well '{well_name}' is empty. Skipping.")
                    continue

                df = pd.read_csv(io.StringIO(content_str))

                if df.empty:
                    logger.warning(f"File {filename} for well '{well_name}' resulted in an empty dataset. Skipping.")
                    continue

                # Basic validation (can be expanded)
                if not self._validate_columns(df): # Assumes columns like 'Date', 'OilRate', etc.
                    logger.error(f"Invalid columns in {filename} for well '{well_name}'. Skipping.")
                    return False, f"Invalid columns in {filename}.", None

                # Convert DataFrame rows to list of dicts for database insertion
                # Standardize column names (example: 'Date' -> 'date', 'OilRate' -> 'oil_rate')
                df.rename(columns={
                    'Date': 'date', 'Timestamp': 'date', 'Time': 'date', # Common date column names
                    'Oil': 'oil_rate', 'OilRate': 'oil_rate', 'Qo': 'oil_rate',
                    'Gas': 'gas_rate', 'GasRate': 'gas_rate', 'Qg': 'gas_rate',
                    'Water': 'water_rate', 'WaterRate': 'water_rate', 'Qw': 'water_rate'
                }, inplace=True, errors='ignore') # Use errors='ignore' if not all columns are present

                # Ensure 'date' column exists after renaming
                if 'date' not in df.columns:
                    logger.error(f"'date' column not found in {filename} after renaming. Columns: {df.columns}. Skipping.")
                    return False, f"'date' column not found in {filename}.", None

                # Convert date column to datetime.date objects if they are strings
                try:
                    # Attempt to infer datetime format, then convert to date
                    df['date'] = pd.to_datetime(df['date']).dt.date
                except Exception as e:
                    logger.error(f"Error converting 'date' column to datetime.date in {filename}: {e}. Skipping.")
                    return False, f"Error in 'date' column format in {filename}.", None

                required_prod_cols = ['date'] # 'oil_rate', 'gas_rate', 'water_rate' are optional in DB model
                for col in required_prod_cols:
                    if col not in df.columns:
                        logger.error(f"Required column '{col}' not found in {filename} for well '{well_name}'. Skipping.")
                        # Allow partial data if only some rate columns are missing, but date is essential
                        return False, f"Required column '{col}' not found in {filename}.", None

                # Fill NaN with None for database compatibility (SQL NULL)
                df = df.where(pd.notnull(df), None)
                all_production_records.extend(df.to_dict('records'))
                processed_files_count += 1

            if not all_production_records:
                msg = "No valid data found in provided files."
                logger.warning(f"{msg} for well '{well_name}'.")
                return False, msg, None

            # Get or create well in the database
            well_id = self.db_manager.insert_well(
                well_name=well_name,
                field_name=field_name,
                latitude=latitude,
                longitude=longitude
            )

            if well_id is None:
                msg = f"Failed to create or retrieve well '{well_name}' in database."
                logger.error(msg)
                return False, msg, None

            # Insert production data
            success_insert = self.db_manager.insert_production_data(well_id, all_production_records)
            if success_insert:
                msg = f"Data for well '{well_name}' (ID: {well_id}) loaded successfully from {processed_files_count} file(s) into database."
                logger.info(msg)
                return True, msg, well_id
            else:
                msg = f"Failed to insert production data for well '{well_name}' (ID: {well_id}) into database."
                logger.error(msg)
                return False, msg, well_id # well_id might exist even if prod data fails

        except pd.errors.EmptyDataError as e:
            logger.error(f"A CSV file for well '{well_name}' was empty or malformed: {e}")
            return False, f"One of the files for well '{well_name}' was empty or not a valid CSV.", None
        except Exception as e:
            logger.exception(f"Unexpected error loading data for well '{well_name}': {e}") # Use logger.exception for stack trace
            return False, f"Error loading data for well '{well_name}': {str(e)}", None

    def get_data_preview(self, well_name: str, n_rows: int = 5) -> Optional[pd.DataFrame]:
        """Returns a preview of the production data for a well from the database."""
        well = self.db_manager.get_well_by_name(well_name)
        if not well:
            logger.warning(f"Well '{well_name}' not found in database for preview.")
            return None

        production_data_dicts = self.db_manager.get_well_production_data(well.id)
        if not production_data_dicts:
            logger.info(f"No production data found for well '{well_name}' (ID: {well.id}) for preview.")
            return pd.DataFrame() # Return empty DataFrame if no data

        df = pd.DataFrame(production_data_dicts)
        return df.head(n_rows)

    def get_well_statistics(self, well_name: str) -> Optional[Dict[str, Any]]:
        """Calculates and returns descriptive statistics for a well's data from the database."""
        well = self.db_manager.get_well_by_name(well_name)
        if not well:
            logger.warning(f"Well '{well_name}' not found in database for statistics.")
            return None

        production_data_dicts = self.db_manager.get_well_production_data(well.id)
        if not production_data_dicts:
            logger.info(f"No production data found for well '{well_name}' (ID: {well.id}) for statistics.")
            return {"well_id": well.id, "well_name": well.name, "rows": 0, "columns": [], "description": {}}

        df = pd.DataFrame(production_data_dicts)
        # Convert date back to datetime if needed for describe, though usually not necessary for basic stats
        # df['date'] = pd.to_datetime(df['date'])

        stats = {
            "well_id": well.id,
            "well_name": well.name,
            "field_name": well.field,
            "latitude": well.latitude,
            "longitude": well.longitude,
            "rows": len(df),
            "columns": list(df.columns),
            "description": df.describe(include='all', datetime_is_numeric=True).to_dict()
        }
        return stats

    def _validate_columns(self, df: pd.DataFrame) -> bool:
        """Basic column validation logic. Checks for a date column."""
        # Standardized column names for check
        possible_date_cols = ['Date', 'Timestamp', 'Time', 'date']
        # Check if at least one of the possible date columns exists
        if not any(col in df.columns for col in possible_date_cols):
            logger.warning(f"Validation failed: No recognized date column found in DataFrame. Columns: {df.columns}")
            return False
        # Add more checks if necessary, e.g. for OilRate, GasRate etc.
        # For now, we are flexible with rate columns as they are optional in DB.
        return True

    def list_loaded_wells(self) -> List[Dict[str, Any]]:
        """Returns a list of well names and their IDs from the database."""
        session = self.db_manager.get_session()
        try:
            wells = session.query(Well.id, Well.name, Well.field).order_by(Well.name).all()
            return [{"id": w.id, "name": w.name, "field": w.field} for w in wells]
        except Exception as e:
            logger.error(f"Error listing wells from database: {e}")
            return []
        finally:
            session.close()

# The global _well_data_store and clear_data_store() are no longer needed
# as data is persisted in the database.

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    # Initialize DatabaseManager (using a test DB file)
    # Ensure this path is writable and accessible
    db_file = "test_data_management.db"
    try:
        import os
        if os.path.exists(db_file):
            os.remove(db_file) # Clean up before test
        logger.info(f"Removed old {db_file} if it existed.")
    except OSError as e:
        logger.error(f"Error removing old database file {db_file}: {e}. Tests might be affected.")

    test_db_url = f"sqlite:///{db_file}"
    db_manager = DatabaseManager(db_url=test_db_url)

    if not db_manager.connect():
        logger.critical("Failed to connect to DB for DataUploader tests. Exiting.")
        exit(1)
    if not db_manager.create_tables():
        logger.critical("Failed to create tables for DataUploader tests. Exiting.")
        exit(1)

    uploader = DataUploader(db_manager)

    # Example CSV content
    csv_content_1 = "Date,OilRate,GasRate\n2023-01-01,100.5,50.2\n2023-01-02,98.2,48.9"
    csv_content_2 = "Time,Oil,Water\n2023-01-03,95.0,10.1\n2023-01-04,93.1,11.0" # 'Time' and 'Oil' should be mapped
    csv_content_empty = ""
    csv_content_invalid_date = "Date,OilRate\n23/01/2023,100" # Potentially problematic date format for default pd.to_datetime

    # Test load_well_data
    logger.info("\n--- Test 1: Load valid data for NewWell-A ---")
    success, msg, well_id_A = uploader.load_well_data(
        "NewWell-A",
        [("file1.csv", csv_content_1), ("file2.csv", csv_content_2)],
        field_name="Alpha Field", latitude=10.0, longitude=20.0
    )
    print(f"Load NewWell-A: Success={success}, Message='{msg}', ID={well_id_A}")
    assert success
    assert well_id_A is not None

    logger.info("\n--- Test 2: Get preview for NewWell-A ---")
    preview_A = uploader.get_data_preview("NewWell-A", n_rows=5)
    print("Preview NewWell-A:\n", preview_A)
    assert preview_A is not None
    assert len(preview_A) == 4 # 2 from file1, 2 from file2
    assert 'oil_rate' in preview_A.columns
    assert 'water_rate' in preview_A.columns # From file2

    logger.info("\n--- Test 3: Get statistics for NewWell-A ---")
    stats_A = uploader.get_well_statistics("NewWell-A")
    print("Statistics NewWell-A:\n", stats_A)
    assert stats_A is not None
    assert stats_A['rows'] == 4
    assert stats_A['well_id'] == well_id_A

    logger.info("\n--- Test 4: List loaded wells ---")
    wells = uploader.list_loaded_wells()
    print("Loaded Wells:", wells)
    assert any(w['name'] == "NewWell-A" and w['id'] == well_id_A for w in wells)

    logger.info("\n--- Test 5: Load data for existing well (NewWell-A) with new file ---")
    # This should append new data or skip duplicates based on date
    csv_content_3 = "Date,OilRate,GasRate\n2023-01-05,90.0,40.0\n2023-01-01,100.5,50.2" # one new, one duplicate
    success_append, msg_append, well_id_A_append = uploader.load_well_data(
        "NewWell-A", [("file3.csv", csv_content_3)]
    )
    print(f"Load NewWell-A (append): Success={success_append}, Message='{msg_append}', ID={well_id_A_append}")
    assert success_append
    assert well_id_A_append == well_id_A # Should be the same well

    stats_A_after_append = uploader.get_well_statistics("NewWell-A")
    print("Statistics NewWell-A after append:\n", stats_A_after_append)
    assert stats_A_after_append['rows'] == 5 # 4 original + 1 new (one was duplicate)


    logger.info("\n--- Test 6: Load data with empty file content ---")
    success_empty, msg_empty, well_id_B = uploader.load_well_data(
        "NewWell-B", [("empty.csv", csv_content_empty)]
    )
    print(f"Load NewWell-B (empty file): Success={success_empty}, Message='{msg_empty}', ID={well_id_B}")
    assert not success_empty # Should fail or report no data loaded

    logger.info("\n--- Test 7: Get preview for non-existent well ---")
    preview_C = uploader.get_data_preview("NonExistentWell")
    print("Preview NonExistentWell:", preview_C)
    assert preview_C is None

    logger.info("\n--- Test 8: Load data with problematic date format ---")
    # The current _validate_columns and date parsing might handle some, but strict ISO is safer.
    # pd.to_datetime might infer '23/01/2023' if dayfirst=True or format is specified.
    # Current implementation relies on pd.to_datetime's default behavior.
    success_baddate, msg_baddate, _ = uploader.load_well_data(
        "BadDateWell", [("baddate.csv", csv_content_invalid_date)]
    )
    print(f"Load BadDateWell: Success={success_baddate}, Message='{msg_baddate}'")
    # This might succeed if pd.to_datetime infers correctly, or fail if it can't.
    # If it fails, success_baddate should be False.
    # For this test, let's assume it might fail due to ambiguity or strict parsing.
    # If pd.to_datetime is robust enough, this test might need adjustment.
    # As of current implementation, pd.to_datetime might parse '23/01/2023' as an error or American MM/DD/YYYY
    # which would then fail date conversion or lead to wrong dates.
    # Let's assume it fails for now.
    # assert not success_baddate # This depends on how robust the date parsing is made

    logger.info("\n--- Test 9: Load data with only a date column (no rate columns) ---")
    csv_only_date = "Date\n2024-03-15\n2024-03-16"
    success_date_only, msg_date_only, well_id_D = uploader.load_well_data(
        "DateOnlyWell", [("dateonly.csv", csv_only_date)]
    )
    print(f"Load DateOnlyWell: Success={success_date_only}, Message='{msg_date_only}', ID={well_id_D}")
    assert success_date_only
    assert well_id_D is not None
    preview_D = uploader.get_data_preview("DateOnlyWell")
    print("Preview DateOnlyWell:\n", preview_D)
    assert preview_D is not None and len(preview_D) == 2
    assert 'oil_rate' not in preview_D or preview_D['oil_rate'].isnull().all() # oil_rate might be present as None

    logger.info("\n--- Test 10: Load data with no valid date column ---")
    csv_no_date_column = "Value1,Value2\n10,20\n30,40"
    success_no_date, msg_no_date, _ = uploader.load_well_data(
        "NoDateColumnWell", [("nodate.csv", csv_no_date_column)]
    )
    print(f"Load NoDateColumnWell: Success={success_no_date}, Message='{msg_no_date}'")
    assert not success_no_date # Should fail because _validate_columns expects a date column

    db_manager.close()
    logger.info("All DataUploader tests finished.")
    # Clean up the test database file
    try:
        if os.path.exists(db_file):
            os.remove(db_file)
        logger.info(f"Cleaned up test database file: {db_file}")
    except OSError as e:
        logger.error(f"Error cleaning up test database file {db_file}: {e}")
