from typing import List, Tuple, Dict, Optional, Any
import pandas as pd
import io
import logging
import datetime
from sqlalchemy.exc import SQLAlchemyError

# Import DatabaseManager from the new core location
from .database_manager import DatabaseManager
from .database_models import Well  # Assuming Well is in database_models

logger = logging.getLogger(__name__)


class DataUploader:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        # self.well_data_cache = {} # Removed, as DB is the source of truth

    def load_well_data(
        self,
        well_name: str,
        csv_files_content: List[Tuple[str, str]],  # List of (filename, content_string)
        field_name: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Loads well data from multiple CSV content strings, validates, and stores in the database.
        Creates or updates well metadata.
        """
        if not well_name:
            return False, "Well name cannot be empty.", None

        # Create or get well_id
        well = self.db_manager.get_well_by_name(well_name)
        if not well:
            well_id = self.db_manager.insert_well(
                well_name=well_name,
                field_name=field_name,
                latitude=latitude,
                longitude=longitude,
            )
            if well_id is None:
                return False, f"Failed to create well '{well_name}' in database.", None
            logger.info(f"Created new well '{well_name}' with ID {well_id}.")
        else:
            well_id = well.id
            # Optionally, update metadata if provided for an existing well
            if field_name or latitude is not None or longitude is not None:
                updates = {}
                if field_name:
                    updates["field"] = field_name
                if latitude is not None:
                    updates["latitude"] = latitude
                if longitude is not None:
                    updates["longitude"] = longitude
                self.db_manager.update_db_well_metadata(
                    well_id, updates
                )  # Assumes this method exists
            logger.info(f"Using existing well '{well_name}' with ID {well_id}.")

        all_records_for_db = []
        processed_filenames = []

        for filename, content_str in csv_files_content:
            try:
                df = pd.read_csv(io.StringIO(content_str))
            except Exception as e:
                logger.error(
                    f"Error parsing CSV content from {filename} for well {well_name}: {e}"
                )
                return False, f"Error parsing CSV {filename}: {e}", well_id

            # Basic validation (example: expects 'date' and at least one rate column)
            if "date" not in df.columns:
                return False, f"Missing 'date' column in {filename}.", well_id

            # Convert to list of dicts for DB insertion
            try:
                # Ensure date is in YYYY-MM-DD string format or datetime.date for DB
                df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
            except Exception as e:
                return (
                    False,
                    f"Error converting 'date' column to YYYY-MM-DD in {filename}: {e}",
                    well_id,
                )

            # Prepare records for database insertion
            for record_idx, row in df.iterrows():
                # Ensure that rates are float or None, not NaN
                oil_rate = row.get("oil_rate")
                gas_rate = row.get("gas_rate")
                water_rate = row.get("water_rate")

                all_records_for_db.append(
                    {
                        "date": row["date"],  # Already formatted
                        "oil_rate": float(oil_rate) if pd.notna(oil_rate) else None,
                        "gas_rate": float(gas_rate) if pd.notna(gas_rate) else None,
                        "water_rate": (
                            float(water_rate) if pd.notna(water_rate) else None
                        ),
                        # Add other relevant columns if they exist and are part of ProductionData model
                    }
                )
            processed_filenames.append(filename)

        if not all_records_for_db:
            return (
                True,
                "No new data records found in provided files.",
                well_id,
            )  # Or False if this is an error

        # Insert all collected data into the database
        success = self.db_manager.insert_production_data(well_id, all_records_for_db)
        if success:
            msg = f"Successfully loaded and stored data for well '{well_name}' from files: {', '.join(processed_filenames)}."
            logger.info(msg)
            return True, msg, well_id
        else:
            msg = f"Failed to store production data for well '{well_name}' in database."
            logger.error(msg)
            return False, msg, well_id

    def get_data_preview(
        self, well_name: str, n_rows: int = 5
    ) -> Optional[pd.DataFrame]:
        """Retrieves a preview of the data for a specific well from the database."""
        well = self.db_manager.get_well_by_name(well_name)
        if not well:
            logger.warning(f"Preview requested for non-existent well: {well_name}")
            return None

        data_dicts = self.db_manager.get_well_production_data(
            well.id
        )  # Limit handled by DB if implemented, or here
        if not data_dicts:
            return pd.DataFrame()  # Return empty DataFrame if no production data

        df = pd.DataFrame(data_dicts)
        return df.head(n_rows)

    def get_well_statistics(self, well_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves descriptive statistics for the data of a specific well."""
        well = self.db_manager.get_well_by_name(well_name)
        if not well:
            logger.warning(f"Statistics requested for non-existent well: {well_name}")
            return None

        data_dicts = self.db_manager.get_well_production_data(well.id)
        if not data_dicts:
            return {
                "message": "No production data found for this well to calculate statistics."
            }

        df = pd.DataFrame(data_dicts)
        # Convert rate columns to numeric, coercing errors for describe()
        for col in ["oil_rate", "gas_rate", "water_rate"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Convert date to datetime for time-series statistics
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])

        stats = df.describe(
            include="all", datetime_is_numeric=True
        ).to_dict()  # to_dict for JSON serializability
        # Pandas describe() with include='all' can produce NaNs for non-numeric types, which need handling for JSON.
        # A more robust approach would be to select numeric columns for describe() and handle others separately.
        # For simplicity, let's assume describe output is mostly numeric or can be converted.

        # Clean up stats for JSON serialization (e.g., convert NaNs, Timestamps)
        cleaned_stats = {}
        for col, col_stats in stats.items():
            cleaned_stats[col] = {}
            for stat_name, value in col_stats.items():
                if pd.isna(value):
                    cleaned_stats[col][stat_name] = None
                elif isinstance(value, (datetime.date, datetime.datetime)):
                    cleaned_stats[col][stat_name] = value.isoformat()
                else:
                    cleaned_stats[col][stat_name] = value
        return cleaned_stats

    def list_loaded_wells(self) -> List[Dict[str, Any]]:
        """Lists all wells that have data loaded, from the database."""
        # This method should query the 'wells' table from the database.
        session = self.db_manager.get_session()
        try:
            wells_orm = session.query(Well).all()
            wells_list = []
            for well_orm in wells_orm:
                wells_list.append(
                    {
                        "id": well_orm.id,
                        "name": well_orm.name,
                        "field": well_orm.field,
                        "latitude": well_orm.latitude,
                        "longitude": well_orm.longitude,
                        "created_at": (
                            well_orm.created_at.isoformat()
                            if well_orm.created_at
                            else None
                        ),
                    }
                )
            return wells_list
        except Exception as e:
            logger.error(f"Error listing wells from database: {e}")
            return []
        finally:
            session.close()

    # Placeholder for a method that might have been in the original DatabaseManager or a new one
    def update_db_well_metadata(self, well_id: int, updates: Dict[str, Any]) -> bool:
        """Updates metadata for an existing well."""
        session = self.db_manager.get_session()
        try:
            well = session.query(Well).filter(Well.id == well_id).first()
            if not well:
                logger.warning(f"Well ID {well_id} not found for metadata update.")
                return False

            for key, value in updates.items():
                if hasattr(well, key):
                    setattr(well, key, value)

            session.commit()
            logger.info(f"Metadata updated for well ID {well_id}.")
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating metadata for well ID {well_id}: {e}")
            return False
        finally:
            session.close()
