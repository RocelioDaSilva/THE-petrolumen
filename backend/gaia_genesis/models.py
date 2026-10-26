import uuid
import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from gaia_genesis.core.database_models import Base, ProductionData, User, Well


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


User.well_data_records = relationship("WellDataRecord", back_populates="user")


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
