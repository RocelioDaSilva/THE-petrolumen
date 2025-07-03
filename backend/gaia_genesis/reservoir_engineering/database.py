from typing import List, Any, Dict, Optional
import datetime
import logging
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

logger = logging.getLogger(__name__)

Base = declarative_base()

# Define SQLAlchemy Models
class Well(Base):
    __tablename__ = "wells"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    field = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(Date, default=datetime.date.today)

    production_data = relationship("ProductionData", back_populates="well", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Well(id={self.id}, name='{self.name}')>"

class ProductionData(Base):
    __tablename__ = "production_data"

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=False)
    date = Column(Date, nullable=False)
    oil_rate = Column(Float, nullable=True)
    gas_rate = Column(Float, nullable=True)
    water_rate = Column(Float, nullable=True)
    # Other potential fields: pressure, choke_size, etc.

    well = relationship("Well", back_populates="production_data")

    __table_args__ = (UniqueConstraint('well_id', 'date', name='_well_date_uc'),)

    def __repr__(self):
        return f"<ProductionData(id={self.id}, well_id={self.well_id}, date='{self.date}', oil={self.oil_rate})>"

# User Model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="user", nullable=False) # e.g., "user", "admin"
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(Date, default=datetime.date.today)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class DatabaseManager:
    def __init__(self, db_url: str = "sqlite:///./reservoir_data.db"):
        """
        Constructor for database connection parameters using SQLAlchemy.
        db_url: SQLAlchemy database URL (e.g., "sqlite:///./reservoir_data.db" or "postgresql://user:pass@host/dbname")
        """
        # Ensure SENSITIVE_VALUE_DO_NOT_LOG is handled by logging configuration if db_url contains sensitive info
        self.db_url = db_url
        self.engine = None
        self.SessionLocal = None
        logger.info(f"DatabaseManager initialized for DB URL: {self.db_url}")

    def connect(self) -> bool:
        """Establishes a connection to the database using SQLAlchemy."""
        try:
            self.engine = create_engine(self.db_url, connect_args={"check_same_thread": False} if "sqlite" in self.db_url else {})
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            # Test connection - this will raise an exception if connection fails
            with self.engine.connect() as connection:
                logger.info(f"Successfully connected to database: {self.db_url}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to connect to database {self.db_url}: {e}")
            self.engine = None
            self.SessionLocal = None
            return False

    def create_tables(self) -> bool:
        """Creates necessary database tables/schema using SQLAlchemy Base.metadata."""
        if not self.engine:
            logger.error("Cannot create tables: Database engine not initialized. Call connect() first.")
            return False
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully (or already exist).")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error creating database tables: {e}")
            return False

    def get_session(self):
        """Provides a database session."""
        if not self.SessionLocal:
            logger.error("SessionLocal not initialized. Call connect() first.")
            # Optionally, try to connect here if desired, or raise an error
            # if not self.connect(): # Attempt to connect if not already
            raise ConnectionError("Database not connected. Cannot get session.")
        return self.SessionLocal()

    def insert_well(self, well_name: str, field_name: Optional[str] = None,
                    latitude: Optional[float] = None, longitude: Optional[float] = None) -> Optional[int]:
        """Inserts well metadata. Returns the ID of the inserted well or None on failure."""
        session = self.get_session()
        try:
            new_well = Well(name=well_name, field=field_name, latitude=latitude, longitude=longitude)
            session.add(new_well)
            session.commit()
            session.refresh(new_well)
            logger.info(f"Well '{well_name}' inserted with ID {new_well.id}.")
            return new_well.id
        except IntegrityError:
            session.rollback()
            logger.warning(f"Well with name '{well_name}' already exists (IntegrityError). Not updating metadata here.")
            # Query and return existing well's ID without attempting to update its metadata.
            # The test should ensure a clean state if it expects a new well or specific metadata.
            existing_well_after_integrity_error = session.query(Well).filter(Well.name == well_name).first()
            return existing_well_after_integrity_error.id if existing_well_after_integrity_error else None
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error inserting well '{well_name}': {e}")
            return None
        finally:
            session.close()

    def insert_production_data(self, well_id: int, data: List[Dict[str, Any]]) -> bool:
        """
        Inserts production data for a well. Data is a list of records (e.g., dicts).
        Each dict in data should have 'date' (datetime.date or YYYY-MM-DD string),
        and optionally 'oil_rate', 'gas_rate', 'water_rate'.
        """
        session = self.get_session()
        try:
            # Check if well exists
            well = session.query(Well).filter(Well.id == well_id).first()
            if not well:
                logger.error(f"Cannot insert production data: Well with ID {well_id} not found.")
                return False

            db_production_data_list = []
            for record in data:
                record_date = record.get('date')
                if isinstance(record_date, str):
                    try:
                        record_date = datetime.datetime.strptime(record_date, "%Y-%m-%d").date()
                    except ValueError:
                        logger.warning(f"Invalid date format for record: {record}. Skipping.")
                        continue
                elif not isinstance(record_date, datetime.date):
                    logger.warning(f"Invalid date type for record: {record}. Skipping.")
                    continue

                # Check for existing record for this well and date to avoid duplicates (due to UniqueConstraint)
                exists = session.query(ProductionData).filter_by(well_id=well_id, date=record_date).first()
                if exists:
                    logger.debug(f"Production data for well ID {well_id} on date {record_date} already exists. Skipping.")
                    continue

                db_production_data = ProductionData(
                    well_id=well_id,
                    date=record_date,
                    oil_rate=record.get('oil_rate'),
                    gas_rate=record.get('gas_rate'),
                    water_rate=record.get('water_rate')
                )
                db_production_data_list.append(db_production_data)

            if not db_production_data_list:
                logger.info(f"No new production data to insert for well ID {well_id}.")
                return True # Or False if you consider it a failure that no data was inserted

            session.add_all(db_production_data_list)
            session.commit()
            logger.info(f"Inserted {len(db_production_data_list)} production records for well ID {well_id}.")
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error inserting production data for well ID {well_id}: {e}")
            return False
        finally:
            session.close()

    def get_well_by_name(self, well_name: str) -> Optional[Well]:
        session = self.get_session()
        try:
            well = session.query(Well).filter(Well.name == well_name).first()
            return well
        except SQLAlchemyError as e:
            logger.error(f"Error fetching well '{well_name}': {e}")
            return None
        finally:
            session.close()

    def get_well_production_data(self, well_id: int, start_date: Optional[datetime.date] = None,
                               end_date: Optional[datetime.date] = None) -> List[Dict[str, Any]]:
        """Queries production data for a specific well ID within a date range."""
        session = self.get_session()
        try:
            query = session.query(ProductionData).filter(ProductionData.well_id == well_id)
            if start_date:
                query = query.filter(ProductionData.date >= start_date)
            if end_date:
                query = query.filter(ProductionData.date <= end_date)

            results = query.order_by(ProductionData.date).all()

            data_list = [
                {
                    "date": r.date.isoformat(),
                    "oil_rate": r.oil_rate,
                    "gas_rate": r.gas_rate,
                    "water_rate": r.water_rate,
                    "id": r.id,
                    "well_id": r.well_id
                } for r in results
            ]
            logger.info(f"Retrieved {len(data_list)} production records for well ID {well_id}.")
            return data_list
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving production data for well ID {well_id}: {e}")
            return []
        finally:
            session.close()

    # --- User Management Methods ---
    def create_db_user(self, username: str, email: str, hashed_password: str,
                       full_name: Optional[str] = None, role: str = "user", is_active: bool = True) -> Optional[User]:
        """Creates a new user in the database."""
        session = self.get_session()
        try:
            new_user = User(
                username=username,
                email=email,
                hashed_password=hashed_password, # Password should already be hashed
                full_name=full_name,
                role=role,
                is_active=is_active
            )
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            logger.info(f"User '{username}' created successfully in DB with ID {new_user.id}.")
            return new_user
        except IntegrityError: # Handles unique constraint violation for username or email
            session.rollback()
            logger.warning(f"User creation failed: Username '{username}' or email '{email}' already exists in DB.")
            return None
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error creating user '{username}' in DB: {e}")
            return None
        finally:
            session.close()

    def get_db_user_by_username(self, username: str) -> Optional[User]:
        """Retrieves a user by username from the database."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            if user:
                logger.debug(f"User '{username}' found in DB.")
            else:
                logger.debug(f"User '{username}' not found in DB.")
            return user
        except SQLAlchemyError as e:
            logger.error(f"Error fetching user '{username}' from DB: {e}")
            return None
        finally:
            session.close()

    def get_db_user_by_email(self, email: str) -> Optional[User]:
        """Retrieves a user by email from the database."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.email == email).first()
            return user
        except SQLAlchemyError as e:
            logger.error(f"Error fetching user by email '{email}' from DB: {e}")
            return None
        finally:
            session.close()

    def get_all_db_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Retrieves all users from the database with pagination."""
        session = self.get_session()
        try:
            users = session.query(User).offset(skip).limit(limit).all()
            return users
        except SQLAlchemyError as e:
            logger.error(f"Error fetching all users from DB: {e}")
            return []
        finally:
            session.close()

    def update_db_user(self, username: str, updates: Dict[str, Any]) -> Optional[User]:
        """Updates a user's details in the database. 'username' cannot be changed via this method."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                logger.warning(f"User '{username}' not found for update.")
                return None

            for key, value in updates.items():
                if hasattr(user, key) and key != "username" and key != "id": # Protect username and id
                    setattr(user, key, value)

            session.commit()
            session.refresh(user)
            logger.info(f"User '{username}' updated successfully in DB.")
            return user
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating user '{username}' in DB: {e}")
            return None
        finally:
            session.close()

    def delete_db_user(self, username: str) -> bool:
        """Deletes a user from the database by username."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                logger.warning(f"User '{username}' not found for deletion.")
                return False

            session.delete(user)
            session.commit()
            logger.info(f"User '{username}' deleted successfully from DB.")
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error deleting user '{username}' from DB: {e}")
            return False
        finally:
            session.close()

    def close(self) -> None:
        """Closes the database engine (important for some DBs or applications)."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database engine disposed.")
        else:
            logger.info("No active database engine to dispose.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    # Use an in-memory SQLite database for example, or specify a file path
    db_manager = DatabaseManager(db_url="sqlite:///./test_reservoir_main.db")
    # db_manager = DatabaseManager(db_url="sqlite:///:memory:")


    if db_manager.connect():
        logger.info("Main: Connected to DB.")
        if db_manager.create_tables():
            logger.info("Main: Tables created.")

            # Test inserting a well
            well_id_1 = db_manager.insert_well(well_name="Well-Alpha-01", field_name="Alpha Field", latitude=30.123, longitude=-95.456)
            if well_id_1:
                logger.info(f"Main: Well-Alpha-01 created with ID: {well_id_1}")

                # Test inserting duplicate well name (should return existing ID or handle gracefully)
                well_id_1_dup = db_manager.insert_well(well_name="Well-Alpha-01", field_name="Alpha Field")
                logger.info(f"Main: Attempt to re-insert Well-Alpha-01, got ID: {well_id_1_dup}")
                assert well_id_1 == well_id_1_dup

                # Test inserting production data
                prod_data_1 = [
                    {"date": "2023-01-01", "oil_rate": 120.5, "gas_rate": 60.0, "water_rate": 15.0},
                    {"date": datetime.date(2023, 1, 2), "oil_rate": 118.2, "gas_rate": 58.5, "water_rate": 16.2},
                    {"date": "2023-01-03", "oil_rate": 115.0, "gas_rate": 55.1, "water_rate": 17.0}
                ]
                if db_manager.insert_production_data(well_id=well_id_1, data=prod_data_1):
                    logger.info(f"Main: Production data inserted for Well ID {well_id_1}")

                    # Test inserting duplicate production data (should be skipped)
                    db_manager.insert_production_data(well_id=well_id_1, data=[{"date": "2023-01-01", "oil_rate": 999}])


                # Test retrieving production data
                retrieved_data_1 = db_manager.get_well_production_data(well_id=well_id_1, start_date=datetime.date(2023,1,2))
                logger.info(f"\nMain: Retrieved Production Data for Well ID {well_id_1} (from 2023-01-02):")
                for row in retrieved_data_1:
                    print(row)
                assert len(retrieved_data_1) == 2

            well_id_2 = db_manager.insert_well(well_name="Well-Beta-02", field_name="Beta Field")
            if well_id_2:
                logger.info(f"Main: Well-Beta-02 created with ID: {well_id_2}")
                prod_data_2 = [
                     {"date": "2023-02-01", "oil_rate": 200.0, "gas_rate": 100.0, "water_rate": 25.0},
                ]
                db_manager.insert_production_data(well_id=well_id_2, data=prod_data_2)
                retrieved_beta = db_manager.get_well_production_data(well_id_2)
                logger.info(f"\nMain: Retrieved Production Data for Well ID {well_id_2}:")
                for row in retrieved_beta:
                    print(row)
                assert len(retrieved_beta) == 1


            # Test fetching well by name
            well_obj = db_manager.get_well_by_name("Well-Alpha-01")
            if well_obj:
                logger.info(f"Main: Fetched well object for Well-Alpha-01: ID {well_obj.id}, Lat {well_obj.latitude}")
                # Now use this well_obj.id to get its production data
                data_for_alpha_by_name = db_manager.get_well_production_data(well_obj.id)
                logger.info(f"Main: Production data for {well_obj.name}: {len(data_for_alpha_by_name)} records")
                assert len(data_for_alpha_by_name) == 3

            non_existent_well = db_manager.get_well_by_name("GhostWell-99")
            assert non_existent_well is None
            logger.info(f"Main: Tried fetching non_existent_well, result: {non_existent_well}")

        else:
            logger.error("Main: Failed to create tables.")

        db_manager.close()
        logger.info("Main: Database manager closed.")
    else:
        logger.error("Main: Failed to connect to the database.")
