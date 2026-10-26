import uuid
import datetime
from sqlalchemy import (
    Column,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Boolean,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


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

    def __repr__(self):
        return f"<Well(id={self.id}, name='{self.name}')>"


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

    def __repr__(self):
        return f"<ProductionData(id={self.id}, well_id={self.well_id}, date='{self.date}', oil={self.oil_rate})>"


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
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(String, nullable=False, default="pending")
    result = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    user = relationship("User", back_populates="jobs")

    def __repr__(self):
        return f"<Job(id={self.id}, user_id={self.user_id}, status='{self.status}')>"
