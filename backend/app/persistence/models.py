"""SQLAlchemy 2.0 ORM models absorbed from the legacy Gaia Genesis backend.

Consolidates the legacy ``core/database_models.py`` (``Well``, ``ProductionData``,
``User``) with the petrophysical ``WellPropertyData`` entity used by the
reservoir-engineering package, so future modules share one schema.
"""

from __future__ import annotations

import datetime

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base shared by every persistence model."""


class Well(Base):
    __tablename__ = "wells"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    field: Mapped[str | None] = mapped_column(String, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime.date] = mapped_column(Date, default=datetime.date.today)

    production_data: Mapped[list["ProductionData"]] = relationship(
        back_populates="well", cascade="all, delete-orphan"
    )
    properties: Mapped[list["WellPropertyData"]] = relationship(
        back_populates="well", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Well(id={self.id}, name='{self.name}')>"


class ProductionData(Base):
    __tablename__ = "production_data"
    __table_args__ = (UniqueConstraint("well_id", "date", name="_well_date_uc"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    well_id: Mapped[int] = mapped_column(ForeignKey("wells.id"), nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    oil_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    gas_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    water_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    well: Mapped["Well"] = relationship(back_populates="production_data")


class WellPropertyData(Base):
    """A single log-curve sample (property vs measured depth) for a well."""

    __tablename__ = "well_property_data"
    __table_args__ = (
        UniqueConstraint("well_id", "property_name", "measured_depth", name="_well_prop_md_uc"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    well_id: Mapped[int] = mapped_column(ForeignKey("wells.id"), nullable=False)
    property_name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    measured_depth: Mapped[float] = mapped_column(Float, nullable=False)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)

    well: Mapped["Well"] = relationship(back_populates="properties")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime.date] = mapped_column(Date, default=datetime.date.today)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
