"""DatabaseManager — SQLAlchemy engine/session management and CRUD helpers.

Absorbed from the legacy ``core/database_manager.py`` and cleaned up:

* sessions are exposed through a context manager instead of caller-managed
  ``session.close()`` in a ``finally`` block;
* SQLite gets ``check_same_thread=False``;
* a module-level default database URL is taken from the environment so tests
  and deployments can point at their own file.
"""

from __future__ import annotations

import datetime
import logging
from contextlib import contextmanager
from typing import Any, Generator

from sqlalchemy import create_engine, inspect, or_, select, text
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .models import (
    Base,
    ProductionData,
    SAVED_SIMULATION_OWNER_CREATED_INDEX,
    SavedSimulation,
    User,
    Well,
)

logger = logging.getLogger(__name__)

DEFAULT_DATABASE_URL = "sqlite:///./petrolumen.db"


class DatabaseManager:
    """Owns the engine/session factory for the persistence layer."""

    def __init__(self, db_url: str | None = None):
        self.db_url = db_url or DEFAULT_DATABASE_URL
        self.engine: Engine | None = None
        self._SessionLocal: sessionmaker[Session] | None = None

    def connect(self) -> bool:
        try:
            connect_args = {"check_same_thread": False} if self.db_url.startswith("sqlite") else {}
            self.engine = create_engine(self.db_url, connect_args=connect_args)
            self._SessionLocal = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)
            with self.engine.connect():
                pass
            logger.info("Connected to database: %s", self.db_url)
            return True
        except SQLAlchemyError as exc:
            logger.error("Failed to connect to database %s: %s", self.db_url, exc)
            self.engine = None
            self._SessionLocal = None
            return False

    def create_all(self) -> bool:
        if self.engine is None:
            raise ConnectionError("Database not connected; call connect() first.")
        Base.metadata.create_all(bind=self.engine)
        self._ensure_well_owner_column()
        SAVED_SIMULATION_OWNER_CREATED_INDEX.create(
            bind=self.engine,
            checkfirst=True,
        )
        logger.info("Database tables created (or already present).")
        return True

    def _ensure_well_owner_column(self) -> None:
        if self.engine is None:
            raise ConnectionError("Database not connected; call connect() first.")

        columns = {
            column["name"] for column in inspect(self.engine).get_columns("wells")
        }
        if "owner_id" not in columns:
            with self.engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE wells ADD COLUMN owner_id "
                        "INTEGER REFERENCES users (id)"
                    )
                )
            logger.info("Added nullable owner_id to the existing wells table.")

        owner_index = next(
            index
            for index in Well.__table__.indexes
            if index.name == "ix_wells_owner_id"
        )
        owner_index.create(bind=self.engine, checkfirst=True)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        if self._SessionLocal is None:
            raise ConnectionError("Database not connected; call connect() first.")
        s = self._SessionLocal()
        try:
            yield s
        finally:
            s.close()

    def close(self) -> None:
        if self.engine is not None:
            self.engine.dispose()
            self.engine = None
            self._SessionLocal = None

    # --- Well ---------------------------------------------------------------
    def insert_well(
        self,
        name: str,
        field: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        owner_id: int | None = None,
    ) -> int | None:
        with self.session() as s:
            try:
                well = Well(
                    name=name,
                    field=field,
                    latitude=latitude,
                    longitude=longitude,
                    owner_id=owner_id,
                )
                s.add(well)
                s.commit()
                return well.id
            except IntegrityError:
                s.rollback()
                statement = select(Well).where(Well.name == name)
                if owner_id is not None:
                    statement = statement.where(Well.owner_id == owner_id)
                existing = s.scalar(statement)
                return existing.id if existing else None

    def get_well_by_name(self, name: str) -> Well | None:
        with self.session() as s:
            return s.scalar(select(Well).where(Well.name == name))

    def list_wells(self, owner_id: int | None = None) -> list[dict[str, Any]]:
        with self.session() as s:
            statement = select(Well)
            if owner_id is not None:
                statement = statement.where(Well.owner_id == owner_id)
            wells = s.scalars(statement.order_by(Well.name)).all()
            return [
                {
                    "id": w.id,
                    "name": w.name,
                    "field": w.field,
                    "latitude": w.latitude,
                    "longitude": w.longitude,
                }
                for w in wells
            ]

    def get_field_data(
        self,
        field_name: str,
        start_date: datetime.date | datetime.datetime | None = None,
        end_date: datetime.date | datetime.datetime | None = None,
    ) -> list[dict[str, Any]]:
        if not field_name.strip():
            raise ValueError("Field name must not be empty.")
        start = _coerce_date(start_date) if start_date is not None else None
        end = _coerce_date(end_date) if end_date is not None else None
        if start_date is not None and start is None:
            raise ValueError("Invalid start date.")
        if end_date is not None and end is None:
            raise ValueError("Invalid end date.")
        if start is not None and end is not None and start > end:
            raise ValueError("Start date must not be after end date.")

        statement = (
            select(ProductionData, Well.name, Well.field)
            .join(Well, ProductionData.well_id == Well.id)
            .where(Well.field == field_name)
        )
        if start is not None:
            statement = statement.where(ProductionData.date >= start)
        if end is not None:
            statement = statement.where(ProductionData.date <= end)

        with self.session() as s:
            rows = s.execute(statement.order_by(Well.name, ProductionData.date)).all()
            return [
                {
                    "well_id": production.well_id,
                    "well_name": well_name,
                    "field_name": field,
                    "date": production.date,
                    "oil_rate": production.oil_rate,
                    "gas_rate": production.gas_rate,
                    "water_rate": production.water_rate,
                }
                for production, well_name, field in rows
            ]

    def update_well(
        self,
        well_id: int,
        field: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> bool:
        with self.session() as s:
            well = s.get(Well, well_id)
            if well is None:
                return False
            if field is not None:
                well.field = field
            if latitude is not None:
                well.latitude = latitude
            if longitude is not None:
                well.longitude = longitude
            s.commit()
            return True

    def insert_production_data(self, well_id: int, records: list[dict[str, Any]]) -> int:
        """Insert production rows, skipping duplicates on (well_id, date).

        Returns the number of new rows inserted.
        """
        inserted = 0
        with self.session() as s:
            for record in records:
                date = _coerce_date(record.get("date"))
                if date is None:
                    continue
                exists = s.scalar(
                    select(ProductionData.id).where(
                        ProductionData.well_id == well_id, ProductionData.date == date
                    )
                )
                if exists:
                    continue
                s.add(
                    ProductionData(
                        well_id=well_id,
                        date=date,
                        oil_rate=_float_or_none(record.get("oil_rate")),
                        gas_rate=_float_or_none(record.get("gas_rate")),
                        water_rate=_float_or_none(record.get("water_rate")),
                    )
                )
                inserted += 1
            s.commit()
        return inserted

    def import_production_records(
        self, owner_id: int, records: list[dict[str, Any]]
    ) -> tuple[int, int, int]:
        """Create missing wells and insert production rows, skipping duplicates.

        Each record must include ``well_name``, ``date``, and optional rate
        values. The well and production rows are committed in one transaction.
        Returns ``(inserted_rows, duplicate_rows, created_wells)``.
        """
        if not records:
            return 0, 0, 0

        unique_records: list[dict[str, Any]] = []
        seen_records: set[tuple[str, datetime.date]] = set()
        for record in records:
            key = (record["well_name"], record["date"])
            if key not in seen_records:
                seen_records.add(key)
                unique_records.append(record)

        well_names = list(dict.fromkeys(record["well_name"] for record in unique_records))
        inserted = 0
        created_wells = 0

        with self.session() as s:
            dialect = s.get_bind().dialect.name
            existing_wells: dict[str, int] = {}
            conflicting_names: set[str] = set()
            for offset in range(0, len(well_names), 500):
                name_batch = well_names[offset : offset + 500]
                wells = s.scalars(select(Well).where(Well.name.in_(name_batch))).all()
                for well in wells:
                    if well.owner_id == owner_id:
                        existing_wells[well.name] = well.id
                    else:
                        conflicting_names.add(well.name)

            if conflicting_names:
                raise ValueError(
                    "One or more well names are unavailable for this account."
                )

            missing_names = [
                name for name in well_names if name not in existing_wells
            ]
            if missing_names and dialect == "sqlite":
                result = s.execute(
                    sqlite_insert(Well)
                    .values(
                        [
                            {"name": name, "owner_id": owner_id}
                            for name in missing_names
                        ]
                    )
                    .on_conflict_do_nothing(index_elements=["name"])
                )
                created_wells = max(result.rowcount or 0, 0)
            elif missing_names:
                s.add_all(
                    Well(name=name, owner_id=owner_id) for name in missing_names
                )
                s.flush()
                created_wells = len(missing_names)

            well_ids: dict[str, int] = {}
            for offset in range(0, len(well_names), 500):
                name_batch = well_names[offset : offset + 500]
                wells = s.scalars(
                    select(Well).where(
                        Well.name.in_(name_batch), Well.owner_id == owner_id
                    )
                ).all()
                well_ids.update({well.name: well.id for well in wells})

            if len(well_ids) != len(well_names):
                raise ValueError(
                    "One or more well names are unavailable for this account."
                )

            records_by_well: dict[int, list[dict[str, Any]]] = {}
            for record in unique_records:
                well_id = well_ids[record["well_name"]]
                records_by_well.setdefault(well_id, []).append(
                    {
                        "well_id": well_id,
                        "date": record["date"],
                        "oil_rate": record.get("oil_rate"),
                        "gas_rate": record.get("gas_rate"),
                        "water_rate": record.get("water_rate"),
                    }
                )

            for well_id, well_records in records_by_well.items():
                for offset in range(0, len(well_records), 100):
                    batch = well_records[offset : offset + 100]
                    if dialect == "sqlite":
                        result = s.execute(
                            sqlite_insert(ProductionData)
                            .values(batch)
                            .on_conflict_do_nothing(
                                index_elements=["well_id", "date"]
                            )
                        )
                        inserted += max(result.rowcount or 0, 0)
                        continue

                    dates = [record["date"] for record in batch]
                    existing_dates = set(
                        s.scalars(
                            select(ProductionData.date).where(
                                ProductionData.well_id == well_id,
                                ProductionData.date.in_(dates),
                            )
                        ).all()
                    )
                    new_records = [
                        ProductionData(**record)
                        for record in batch
                        if record["date"] not in existing_dates
                    ]
                    s.add_all(new_records)
                    inserted += len(new_records)

            s.commit()

        return inserted, len(records) - inserted, created_wells

    # --- User ---------------------------------------------------------------
    def create_user(
        self,
        username: str,
        email: str,
        hashed_password: str,
        full_name: str | None = None,
        role: str = "user",
        is_active: bool = True,
    ) -> User | None:
        with self.session() as s:
            try:
                user = User(
                    username=username,
                    email=email,
                    hashed_password=hashed_password,
                    full_name=full_name,
                    role=role,
                    is_active=is_active,
                )
                s.add(user)
                s.commit()
                return user
            except IntegrityError:
                s.rollback()
                return None

    def get_user_by_username(self, username: str) -> User | None:
        with self.session() as s:
            return s.scalar(select(User).where(User.username == username))

    def get_user_by_email(self, email: str) -> User | None:
        with self.session() as s:
            return s.scalar(select(User).where(User.email == email))

    def list_users(self) -> list[User]:
        with self.session() as s:
            return list(s.scalars(select(User)).all())

    def delete_user(self, username: str) -> bool:
        with self.session() as s:
            user = s.scalar(select(User).where(User.username == username))
            if user is None:
                return False
            s.delete(user)
            s.commit()
            return True

    # --- Saved simulations --------------------------------------------------
    def save_simulation(
        self,
        owner_id: int,
        name: str,
        simulation_type: str,
        input_data: dict[str, Any],
        result_data: dict[str, Any],
    ) -> dict[str, Any]:
        with self.session() as s:
            record = SavedSimulation(
                owner_id=owner_id,
                name=name,
                simulation_type=simulation_type,
                input_data=input_data,
                result_data=result_data,
            )
            s.add(record)
            s.commit()
            s.refresh(record)
            return _saved_simulation_data(record, include_payload=True)

    def list_saved_simulations(
        self, owner_id: int, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        with self.session() as s:
            records = s.scalars(
                select(SavedSimulation)
                .where(SavedSimulation.owner_id == owner_id)
                .order_by(SavedSimulation.created_at.desc(), SavedSimulation.id.desc())
                .limit(limit)
                .offset(offset)
            ).all()
            return [_saved_simulation_data(record) for record in records]

    def get_saved_simulation(
        self, simulation_id: int, owner_id: int
    ) -> dict[str, Any] | None:
        with self.session() as s:
            record = s.scalar(
                select(SavedSimulation).where(
                    SavedSimulation.id == simulation_id,
                    SavedSimulation.owner_id == owner_id,
                )
            )
            if record is None:
                return None
            return _saved_simulation_data(record, include_payload=True)

    def delete_saved_simulation(self, simulation_id: int, owner_id: int) -> bool:
        with self.session() as s:
            record = s.scalar(
                select(SavedSimulation).where(
                    SavedSimulation.id == simulation_id,
                    SavedSimulation.owner_id == owner_id,
                )
            )
            if record is None:
                return False
            s.delete(record)
            s.commit()
            return True


def _coerce_date(value: Any) -> datetime.date | None:
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        try:
            return datetime.datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _saved_simulation_data(
    record: SavedSimulation, include_payload: bool = False
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": record.id,
        "name": record.name,
        "simulation_type": record.simulation_type,
        "created_at": record.created_at,
    }
    if include_payload:
        result["input_data"] = record.input_data
        result["result_data"] = record.result_data
    return result
