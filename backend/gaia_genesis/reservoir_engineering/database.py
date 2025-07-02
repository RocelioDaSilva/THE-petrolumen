import psycopg2 # PostgreSQL adapter
from psycopg2 import sql, extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pandas as pd
from typing import Optional, List, Dict, Any

# Note: For TimescaleDB, specific functions or data types might be used for time-series data,
# e.g., hypertable creation. This basic example focuses on PostgreSQL compatibility.

class DatabaseManager:
    def __init__(self, db_name: str = "petrolumen_db", user: str = "user", password: str = "password", host: str = "localhost", port: str = "5432"):
        self.db_name = db_name
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = None
        self.cursor = None
        # Cache for query results (simple implementation)
        self._query_cache = {}

    def _ensure_db_exists(self):
        """Ensures the target database exists, creating it if necessary."""
        try:
            # Connect to the default 'postgres' database to check/create the target DB
            conn_temp = psycopg2.connect(dbname='postgres', user=self.user, password=self.password, host=self.host, port=self.port)
            conn_temp.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur_temp = conn_temp.cursor()

            cur_temp.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), (self.db_name,))
            exists = cur_temp.fetchone()

            if not exists:
                print(f"Database '{self.db_name}' does not exist. Creating...")
                cur_temp.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.db_name)))
                print(f"Database '{self.db_name}' created successfully.")
            else:
                # print(f"Database '{self.db_name}' already exists.")
                pass

            cur_temp.close()
            conn_temp.close()
        except psycopg2.Error as e:
            print(f"Error while ensuring database existence: {e}")
            # If connection to 'postgres' db fails, we might not be able to create the db.
            # The main connect method will then likely fail if db_name doesn't exist.

    def connect(self, ensure_db_exists=True) -> bool:
        """Establishes a connection to the PostgreSQL database."""
        if self.conn and self.conn.closed == 0:
            print("Already connected.")
            return True

        if ensure_db_exists:
            self._ensure_db_exists() # Try to create DB if it doesn't exist

        try:
            self.conn = psycopg2.connect(
                dbname=self.db_name,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            self.cursor = self.conn.cursor(cursor_factory=extras.RealDictCursor) # Use RealDictCursor for dict-like rows
            print(f"Successfully connected to database '{self.db_name}'.")
            return True
        except psycopg2.Error as e:
            print(f"Error connecting to database '{self.db_name}': {e}")
            self.conn = None
            self.cursor = None
            return False

    def close(self):
        """Closes the database connection."""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None
        print("Database connection closed.")

    def execute_query(self, query: str, params: Optional[tuple] = None, fetch: bool = False, use_cache: bool = False, cache_key: Optional[str] = None):
        """Executes a given SQL query."""
        if not self.conn or self.conn.closed != 0:
            print("Not connected to the database. Call connect() first.")
            if not self.connect(): # Try to reconnect
                return None

        if use_cache and cache_key and cache_key in self._query_cache:
            print(f"Returning cached result for key: {cache_key}")
            return self._query_cache[cache_key]

        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            if fetch:
                result = self.cursor.fetchall()
                if use_cache and cache_key:
                    self._query_cache[cache_key] = result
                return result
            return True # For non-select queries or when fetch is False
        except psycopg2.Error as e:
            print(f"Error executing query: {e}")
            self.conn.rollback() # Rollback on error
            return None
        except Exception as ex: # Catch other potential errors, e.g. with cursor
            print(f"An unexpected error occurred during query execution: {ex}")
            if self.conn and self.conn.closed == 0 : self.conn.rollback()
            return None


    def create_tables(self):
        """Creates necessary database tables/schema if they don't exist."""
        # Note: For TimescaleDB, production data table would be a hypertable.
        # Example: SELECT create_hypertable('production_data', 'timestamp_column_name');
        # This needs to be run after table creation.

        well_table_sql = """
        CREATE TABLE IF NOT EXISTS wells (
            well_id SERIAL PRIMARY KEY,
            well_name VARCHAR(255) UNIQUE NOT NULL,
            field_name VARCHAR(255),
            latitude DECIMAL(9, 6),
            longitude DECIMAL(9, 6),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """

        production_data_table_sql = """
        CREATE TABLE IF NOT EXISTS production_data (
            prod_id SERIAL PRIMARY KEY,
            well_id INTEGER NOT NULL REFERENCES wells(well_id) ON DELETE CASCADE,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            oil_rate REAL,
            gas_rate REAL,
            water_rate REAL,
            pressure REAL,
            -- Add other relevant production columns here
            UNIQUE (well_id, timestamp) -- Ensure unique data points per well per timestamp
        );
        """
        # Example for TimescaleDB (run this command separately after table creation via psql or another execute)
        # hypertable_sql = "SELECT create_hypertable('production_data', 'timestamp', if_not_exists => TRUE);"

        if self.execute_query(well_table_sql) and self.execute_query(production_data_table_sql):
            print("Tables 'wells' and 'production_data' ensured to exist.")
            # After creating 'production_data', if using TimescaleDB, you'd convert it to a hypertable.
            # self.execute_query(hypertable_sql) # This might need special handling or permissions
            # print("Attempted to ensure 'production_data' is a hypertable (if TimescaleDB is used).")
        else:
            print("Failed to create one or more tables.")


    def insert_well(self, well_name: str, field_name: Optional[str] = None,
                    latitude: Optional[float] = None, longitude: Optional[float] = None) -> Optional[int]:
        """Inserts well metadata. Returns the new well_id or None on failure."""
        query = sql.SQL("""
            INSERT INTO wells (well_name, field_name, latitude, longitude)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (well_name) DO NOTHING
            RETURNING well_id;
        """)
        # ON CONFLICT DO NOTHING means if well_name exists, it won't insert and won't raise error.
        # If it inserts, it returns well_id. If conflict, returns nothing.

        result = self.execute_query(query, (well_name, field_name, latitude, longitude), fetch=True)
        if result:
            return result[0]['well_id']
        else: # Could be conflict or error
            # If it was a conflict, we might want to fetch the existing ID
            existing = self.get_well_id_by_name(well_name)
            if existing:
                print(f"Well '{well_name}' already exists with ID {existing}.")
                return existing
            return None

    def get_well_id_by_name(self, well_name: str) -> Optional[int]:
        query = sql.SQL("SELECT well_id FROM wells WHERE well_name = %s;")
        result = self.execute_query(query, (well_name,), fetch=True)
        return result[0]['well_id'] if result else None

    def insert_production_data(self, well_id: int, data: List[Dict[str, Any]]) -> bool:
        """
        Inserts production data for a well.
        'data' is a list of dicts, e.g., [{'timestamp': '2023-01-01T00:00:00Z', 'oil_rate': 100.5}, ...]
        """
        if not data: return False

        # Using executemany for batch inserts is more efficient
        query = sql.SQL("""
            INSERT INTO production_data (well_id, timestamp, oil_rate, gas_rate, water_rate, pressure)
            VALUES (%(well_id)s, %(timestamp)s, %(oil_rate)s, %(gas_rate)s, %(water_rate)s, %(pressure)s)
            ON CONFLICT (well_id, timestamp) DO UPDATE SET
                oil_rate = EXCLUDED.oil_rate,
                gas_rate = EXCLUDED.gas_rate,
                water_rate = EXCLUDED.water_rate,
                pressure = EXCLUDED.pressure;
        """)
        # ON CONFLICT updates if record for same well_id and timestamp exists.

        # Prepare data for executemany: list of dicts is fine for psycopg2 v2.8+ with extras.execute_values or similar
        # For basic executemany, it expects a list of tuples.
        # Let's adapt for common executemany by ensuring all keys are present.

        records_to_insert = []
        for record in data:
            records_to_insert.append({
                'well_id': well_id,
                'timestamp': record.get('timestamp'),
                'oil_rate': record.get('oil_rate'),
                'gas_rate': record.get('gas_rate'),
                'water_rate': record.get('water_rate'),
                'pressure': record.get('pressure')
            })

        if not self.conn or self.conn.closed != 0:
            print("Not connected. Call connect() first.")
            if not self.connect(): return False
        try:
            # For batch, extras.execute_values is often better, but executemany with dicts works too
            extras.execute_batch(self.cursor, query.as_string(self.conn), records_to_insert) # Use execute_batch
            self.conn.commit()
            print(f"Successfully inserted/updated {len(records_to_insert)} production records for well_id {well_id}.")
            return True
        except psycopg2.Error as e:
            print(f"Error inserting production data: {e}")
            self.conn.rollback()
            return False
        except Exception as ex:
            print(f"An unexpected error occurred during batch insert: {ex}")
            if self.conn and self.conn.closed == 0 : self.conn.rollback()
            return False


    def get_well_data(self, well_name: str, start_date: Optional[str] = None, end_date: Optional[str] = None,
                      use_cache: bool = False) -> Optional[pd.DataFrame]:
        """Queries production data for a well within a date range. Returns a DataFrame."""
        well_id = self.get_well_id_by_name(well_name)
        if not well_id:
            print(f"Well '{well_name}' not found.")
            return None

        cache_key = f"well_data_{well_name}_{start_date}_{end_date}"

        base_query = sql.SQL("SELECT timestamp, oil_rate, gas_rate, water_rate, pressure FROM production_data WHERE well_id = %s")
        params = [well_id]

        if start_date:
            base_query += sql.SQL(" AND timestamp >= %s")
            params.append(start_date)
        if end_date:
            base_query += sql.SQL(" AND timestamp <= %s")
            params.append(end_date)

        base_query += sql.SQL(" ORDER BY timestamp ASC;")

        result_dicts = self.execute_query(base_query, tuple(params), fetch=True, use_cache=use_cache, cache_key=cache_key)

        if result_dicts is not None:
            return pd.DataFrame(result_dicts) if result_dicts else pd.DataFrame()
        return None

    def clear_cache(self, cache_key: Optional[str] = None):
        """Clears the query cache. If key is provided, clears only that entry."""
        if cache_key:
            if cache_key in self._query_cache:
                del self._query_cache[cache_key]
                print(f"Cache entry for '{cache_key}' cleared.")
            else:
                print(f"Cache key '{cache_key}' not found.")
        else:
            self._query_cache.clear()
            print("All query cache cleared.")


# Example Usage (requires a running PostgreSQL instance)
if __name__ == '__main__':
    # IMPORTANT: Replace with your actual DB credentials and desired DB name
    # For this example to run, you need PostgreSQL running and the user 'testuser'
    # with password 'testpass' needs permission to create databases or connect to 'petrolumen_test_db'.
    # You might need to create the user and grant permissions in PostgreSQL first:
    # CREATE USER testuser WITH PASSWORD 'testpass';
    # ALTER USER testuser CREATEDB; (or grant connect on a pre-existing db)

    db_manager = DatabaseManager(
        db_name="petrolumen_test_db",
        user="your_db_user",  # Replace with your PostgreSQL username
        password="your_db_password", # Replace with your PostgreSQL password
        host="localhost",
        port="5432"
    )

    if db_manager.connect(): # This will also try to create the database if it doesn't exist
        db_manager.create_tables()

        # Insert a well
        well_id_1 = db_manager.insert_well(well_name="WellAlpha", field_name="Alpha Field", latitude=30.123, longitude=-95.456)
        if well_id_1:
            print(f"Inserted/found WellAlpha with ID: {well_id_1}")

            # Insert some production data for WellAlpha
            prod_data_1 = [
                {'timestamp': '2023-01-01T10:00:00Z', 'oil_rate': 120.5, 'gas_rate': 50.2, 'water_rate': 10.0, 'pressure': 3000},
                {'timestamp': '2023-01-02T10:00:00Z', 'oil_rate': 118.2, 'gas_rate': 49.8, 'water_rate': 10.5, 'pressure': 2980},
            ]
            db_manager.insert_production_data(well_id_1, prod_data_1)

            # Insert another well and its data
            well_id_2 = db_manager.insert_well(well_name="WellBeta", field_name="Beta Field")
            if well_id_2:
                print(f"Inserted/Found WellBeta with ID: {well_id_2}")
                prod_data_2 = [
                    {'timestamp': '2023-02-01T12:00:00Z', 'oil_rate': 200.0, 'gas_rate': 150.7}, # Missing some fields, will be NULL
                ]
                db_manager.insert_production_data(well_id_2, prod_data_2)

        # Retrieve data for WellAlpha
        print("\nData for WellAlpha:")
        well_alpha_df = db_manager.get_well_data("WellAlpha", use_cache=True)
        if well_alpha_df is not None:
            print(well_alpha_df)

        # Retrieve data again, should use cache
        print("\nData for WellAlpha (from cache):")
        well_alpha_df_cached = db_manager.get_well_data("WellAlpha", use_cache=True)
        if well_alpha_df_cached is not None:
            print(well_alpha_df_cached)

        db_manager.clear_cache("well_data_WellAlpha_None_None")
        print("\nData for WellAlpha (after cache clear for this key):")
        well_alpha_df_refetched = db_manager.get_well_data("WellAlpha", use_cache=True) # Will re-fetch and re-cache
        if well_alpha_df_refetched is not None:
            print(well_alpha_df_refetched)


        # Example of trying to insert duplicate well name
        print("\nTrying to insert WellAlpha again:")
        well_id_duplicate = db_manager.insert_well(well_name="WellAlpha", field_name="Alpha Field New Info")
        print(f"Result of trying to insert duplicate well: ID {well_id_duplicate} (should be existing ID)")


        # Clean up: Drop tables (optional, for testing)
        # db_manager.execute_query("DROP TABLE IF EXISTS production_data CASCADE;")
        # db_manager.execute_query("DROP TABLE IF EXISTS wells CASCADE;")
        # print("\nDropped tables for cleanup.")

        db_manager.close()
    else:
        print("Could not connect to the database. Please check your PostgreSQL setup and credentials.")
        print("If 'petrolumen_test_db' does not exist, the user needs rights to create it,")
        print("or you need to create it manually before running.")

```
