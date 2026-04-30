import uuid
import datetime
from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    Boolean,
    Date,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    well_data_records = relationship("WellDataRecord", back_populates="user")


class Well(Base):
    __tablename__ = "wells"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    field = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    production_data = relationship(
        "ProductionData", back_populates="well", cascade="all, delete-orphan"
    )


class ProductionData(Base):
    __tablename__ = "production_data"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    well_id = Column(UUID(as_uuid=True), ForeignKey("wells.id"), nullable=False)
    date = Column(Date, nullable=False)
    oil_rate = Column(Float, nullable=True)
    gas_rate = Column(Float, nullable=True)
    water_rate = Column(Float, nullable=True)
    well = relationship("Well", back_populates="production_data")
    __table_args__ = (UniqueConstraint("well_id", "date", name="_well_date_uc"),)


class WellDataRecord(Base):
    __tablename__ = "well_data_records"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    well_name = Column(String, nullable=False)
    uploaded_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    data = Column(
        JSON, nullable=False
    )  # list of dicts with time, oil_rate, gas_rate, water_rate, pressure
    user = relationship("User", back_populates="well_data_records")
    analyses = relationship(
        "AnalysisResult",
        back_populates="well_data_record",
        cascade="all, delete-orphan",
    )


class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    well_data_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("well_data_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    analysis_type = Column(String, nullable=False, default="DCA")
    parameters = Column(JSON)  # e.g. DCA, PVT, simulation, AI, economics, RTA, nodal
    forecast = Column(JSON)  # list of dicts or time series
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    well_data_record = relationship("WellDataRecord", back_populates="analyses")
