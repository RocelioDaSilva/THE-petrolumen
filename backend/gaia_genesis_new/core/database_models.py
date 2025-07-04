from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Reservoir(Base):
    __tablename__ = 'reservoirs'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    location = Column(String(200), nullable=True)
    formation_type = Column(String(50), nullable=True)
    initial_pressure = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True) # Reservoir Temperature in °F
    porosity = Column(Float, nullable=True)
    permeability = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now()) # Ensure updated_at also has a default for creation

    wells = relationship("Well", back_populates="reservoir", cascade="all, delete-orphan")
    simulations = relationship("Simulation", back_populates="reservoir", cascade="all, delete-orphan")

class Well(Base):
    __tablename__ = 'wells'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    well_type = Column(String(20), nullable=True)  # producer/injector/observation
    status = Column(String(20), nullable=True)  # active/inactive/abandoned
    depth = Column(Float, nullable=True)
    reservoir_id = Column(Integer, ForeignKey('reservoirs.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    reservoir = relationship("Reservoir", back_populates="wells")
    production_data = relationship("ProductionData", back_populates="well", cascade="all, delete-orphan")
    pvt_data = relationship("PVTData", back_populates="well", cascade="all, delete-orphan")

class ProductionData(Base):
    __tablename__ = 'production_data'

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey('wells.id'), nullable=False)
    date = Column(Date, nullable=False)
    oil_rate = Column(Float, nullable=True)  # bbl/day
    gas_rate = Column(Float, nullable=True)  # mcf/day
    water_rate = Column(Float, nullable=True)  # bbl/day
    bottomhole_pressure = Column(Float, nullable=True)  # psi
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    well = relationship("Well", back_populates="production_data")

class PVTData(Base):
    __tablename__ = 'pvt_data'

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey('wells.id'), nullable=False)
    pressure = Column(Float, nullable=False) # psi
    temperature = Column(Float, nullable=False) # °F
    oil_fvf = Column(Float, nullable=True)  # Oil Formation Volume Factor (rb/STB)
    gas_fvf = Column(Float, nullable=True)  # Gas Formation Volume Factor (rcf/scf)
    oil_viscosity = Column(Float, nullable=True) # cp
    gas_viscosity = Column(Float, nullable=True) # cp
    solution_gor = Column(Float, nullable=True)  # Solution Gas-Oil Ratio (scf/STB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    well = relationship("Well", back_populates="pvt_data")

class Simulation(Base):
    __tablename__ = 'simulations'

    id = Column(Integer, primary_key=True, index=True)
    reservoir_id = Column(Integer, ForeignKey('reservoirs.id'), nullable=False)
    name = Column(String(100), nullable=True)
    type = Column(String(50), nullable=True)  # black-oil, compositional, etc.
    parameters = Column(Text, nullable=True)  # JSON-encoded simulation parameters
    results_path = Column(String(200), nullable=True)
    run_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), nullable=True)  # running/completed/failed

    reservoir = relationship("Reservoir", back_populates="simulations")
