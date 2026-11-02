from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    ForeignKey,
    UniqueConstraint,
    Boolean,
)
from sqlalchemy.orm import relationship, declarative_base
import datetime

Base = declarative_base()


class Well(Base):
    __tablename__ = "wells"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    field = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(Date, default=datetime.date.today)

    production_data = relationship(
        "ProductionData", back_populates="well", cascade="all, delete-orphan"
    )

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

    well = relationship("Well", back_populates="production_data")

    __table_args__ = (UniqueConstraint("well_id", "date", name="_well_date_uc"),)

    def __repr__(self):
        return f"<ProductionData(id={self.id}, well_id={self.well_id}, date='{self.date}', oil={self.oil_rate})>"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(Date, default=datetime.date.today)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
