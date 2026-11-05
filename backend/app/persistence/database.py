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
from typing import Any, Iterator

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, ProductionData, User, Well

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
        logger.info("Database tables created (or already present).")
        return True

    @contextmanager
    def session(self) -> Iterator[Session]:
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
    ) -> int | None:
        with self.session() as s:
            try:
                well = Well(name=name, field=field, latitude=latitude, longitude=longitude)
                s.add(well)
                s.commit()
                return well.id
            except IntegrityError:
                s.rollback()
                existing = s.scalar(select(Well).where(Well.name == name))
                return existing.id if existing else None

    def get_well_by_name(self, name: str) -> Well | None:
        with self.session() as s:
            return s.scalar(select(Well).where(Well.name == name))

    def list_wells(self) -> list[dict[str, Any]]:
        with self.session() as s:
            wells = s.scalars(select(Well)).all()
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
