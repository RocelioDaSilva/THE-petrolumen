"""Persistence (SQLite via SQLAlchemy)."""
from datetime import datetime
from pathlib import Path
from sqlalchemy import (create_engine, Column, Integer, String,
                        Float, DateTime, ForeignKey, Text)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()
_DB_PATH = Path.home()/".ppes"/"ppes.db"
_DB_PATH.parent.mkdir(exist_ok=True)
engine = create_engine(f"sqlite:///{_DB_PATH}", future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    created = Column(DateTime, default=datetime.utcnow)
    units = Column(String, default="field")
    notes = Column(Text, default="")
    wells = relationship("Well", back_populates="project",
                         cascade="all, delete-orphan")

class Well(Base):
    __tablename__ = "wells"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String, nullable=False)
    depth_ft = Column(Float)
    tubing_id_in = Column(Float)
    created = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="wells")
    pvt = relationship("PVTRecord", back_populates="well",
                        cascade="all, delete-orphan")

class PVTRecord(Base):
    __tablename__ = "pvt"
    id = Column(Integer, primary_key=True)
    well_id = Column(Integer, ForeignKey("wells.id"))
    p_psia = Column(Float); t_F = Column(Float)
    api = Column(Float); gamma_g = Column(Float)
    rs_scf_stb = Column(Float)
    created = Column(DateTime, default=datetime.utcnow)
    well = relationship("Well", back_populates="pvt")

def init_db():
    Base.metadata.create_all(engine)

def get_session():
    init_db()
    return SessionLocal()
