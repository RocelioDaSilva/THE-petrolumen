from typing import List, Any, Dict, Optional
import datetime
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session  # Added Session for type hinting
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# Import Base and models from database_models.py
from .database_models import Base, Well, ProductionData, User

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_url: str = "sqlite:///./default_reservoir_data.db"):
        self.db_url = db_url
        self.engine = None
        self.SessionLocal = None
        logger.info(f"DatabaseManager initialized for DB URL: {self.db_url}")

    def connect(self) -> bool:
        try:
            self.engine = create_engine(
                self.db_url,
                connect_args=(
                    {"check_same_thread": False} if "sqlite" in self.db_url else {}
                ),
            )
            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )
            # Test connection by trying to connect
            with self.engine.connect():  # Variable 'connection' was unused
                logger.info(f"Successfully connected to database: {self.db_url}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to connect to database {self.db_url}: {e}")
            self.engine = None
            self.SessionLocal = None
            return False

    def create_tables(self) -> bool:
        if not self.engine:
            logger.error(
                "Cannot create tables: Database engine not initialized. Call connect() first."
            )
            return False
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info(
                "Database tables (Well, ProductionData, User) created successfully (or already exist)."
            )
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error creating database tables: {e}")
            return False

    def get_session(self) -> Session:  # Changed from Any to Session
        if not self.SessionLocal:
            logger.error("SessionLocal not initialized. Call connect() first.")
            raise ConnectionError("Database not connected. Cannot get session.")
        return self.SessionLocal()

    def insert_well(
        self,
        well_name: str,
        field_name: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Optional[int]:
        session = self.get_session()
        try:
            new_well = Well(
                name=well_name, field=field_name, latitude=latitude, longitude=longitude
            )
            session.add(new_well)
            session.commit()
            session.refresh(new_well)
            logger.info(f"Well '{well_name}' inserted with ID {new_well.id}.")
            return new_well.id
        except IntegrityError:
            session.rollback()
            logger.warning(
                f"Well with name '{well_name}' already exists. Querying existing."
            )
            existing_well = session.query(Well).filter(Well.name == well_name).first()
            return existing_well.id if existing_well else None
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error inserting well '{well_name}': {e}")
            return None
        finally:
            session.close()

    def insert_production_data(self, well_id: int, data: List[Dict[str, Any]]) -> bool:
        session = self.get_session()
        try:
            well = session.query(Well).filter(Well.id == well_id).first()
            if not well:
                logger.error(
                    f"Cannot insert production data: Well with ID {well_id} not found."
                )
                return False

            db_production_data_list = []
            for record in data:
                record_date_str = record.get("date")
                record_date = None
                if isinstance(record_date_str, str):
                    try:
                        record_date = datetime.datetime.strptime(
                            record_date_str, "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        logger.warning(
                            f"Invalid date format for record: {record}. Skipping."
                        )
                        continue
                elif isinstance(record_date_str, datetime.date):
                    record_date = record_date_str
                else:
                    logger.warning(f"Invalid date type for record: {record}. Skipping.")
                    continue

                exists = (
                    session.query(ProductionData)
                    .filter_by(well_id=well_id, date=record_date)
                    .first()
                )
                if exists:
                    logger.debug(
                        f"Production data for well ID {well_id} on date {record_date} already exists. Skipping."
                    )
                    continue

                db_production_data = ProductionData(
                    well_id=well_id,
                    date=record_date,
                    oil_rate=record.get("oil_rate"),
                    gas_rate=record.get("gas_rate"),
                    water_rate=record.get("water_rate"),
                )
                db_production_data_list.append(db_production_data)

            if not db_production_data_list:
                logger.info(f"No new production data to insert for well ID {well_id}.")
                return True

            session.add_all(db_production_data_list)
            session.commit()
            logger.info(
                f"Inserted {len(db_production_data_list)} production records for well ID {well_id}."
            )
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

    def get_well_production_data(
        self,
        well_id: int,
        start_date: Optional[datetime.date] = None,
        end_date: Optional[datetime.date] = None,
    ) -> List[Dict[str, Any]]:
        session = self.get_session()
        try:
            query = session.query(ProductionData).filter(
                ProductionData.well_id == well_id
            )
            if start_date:
                query = query.filter(ProductionData.date >= start_date)
            if end_date:
                query = query.filter(ProductionData.date <= end_date)
            results = query.order_by(ProductionData.date).all()
            return [
                {
                    "date": r.date.isoformat(),
                    "oil_rate": r.oil_rate,
                    "gas_rate": r.gas_rate,
                    "water_rate": r.water_rate,
                }
                for r in results
            ]
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving production data for well ID {well_id}: {e}")
            return []
        finally:
            session.close()

    def create_db_user(
        self,
        username: str,
        email: str,
        hashed_password: str,
        full_name: Optional[str] = None,
        role: str = "user",
        is_active: bool = True,
    ) -> Optional[User]:
        session = self.get_session()
        try:
            new_user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                full_name=full_name,
                role=role,
                is_active=is_active,
            )
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            logger.info(
                f"User '{username}' created successfully in DB with ID {new_user.id}."
            )
            return new_user
        except IntegrityError:
            session.rollback()
            logger.warning(
                f"User creation failed: Username '{username}' or email '{email}' already exists."
            )
            return None
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error creating user '{username}' in DB: {e}")
            return None
        finally:
            session.close()

    def get_db_user_by_username(self, username: str) -> Optional[User]:
        session = self.get_session()
        try:
            return session.query(User).filter(User.username == username).first()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching user '{username}' by username from DB: {e}")
            return None
        finally:
            session.close()

    def get_db_user_by_email(self, email: str) -> Optional[User]:
        session = self.get_session()
        try:
            return session.query(User).filter(User.email == email).first()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching user by email '{email}' from DB: {e}")
            return None
        finally:
            session.close()

    def get_all_db_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        session = self.get_session()
        try:
            return session.query(User).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching all users from DB: {e}")
            return []
        finally:
            session.close()

    def update_db_user(self, username: str, updates: Dict[str, Any]) -> Optional[User]:
        session = self.get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                logger.warning(f"User '{username}' not found for update.")
                return None
            for key, value in updates.items():
                if hasattr(user, key) and key not in [
                    "username",
                    "id",
                    "hashed_password",
                ]:  # Protect critical fields
                    setattr(user, key, value)
            session.commit()
            session.refresh(user)
            logger.info(f"User '{username}' updated successfully.")
            return user
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating user '{username}' in DB: {e}")
            return None
        finally:
            session.close()

    def delete_db_user(self, username: str) -> bool:
        session = self.get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                logger.warning(f"User '{username}' not found for deletion.")
                return False
            session.delete(user)
            session.commit()
            logger.info(f"User '{username}' deleted successfully.")
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error deleting user '{username}' from DB: {e}")
            return False
        finally:
            session.close()

    def close(self) -> None:
        if self.engine:
            self.engine.dispose()
            logger.info("Database engine disposed.")
