from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# ----- Base Schemas (for creation and updates) -----

class ReservoirBase(BaseModel):
    name: str = Field(..., example="North Sea Field")
    location: Optional[str] = Field(None, example="Block 30/2a")
    formation_type: Optional[str] = Field(None, example="Sandstone")
    initial_pressure: Optional[float] = Field(None, example=3500.0) # psi
    temperature: Optional[float] = Field(None, example=180.0) # °F
    porosity: Optional[float] = Field(None, example=0.22)
    permeability: Optional[float] = Field(None, example=150.0) # mD

class WellBase(BaseModel):
    name: str = Field(..., example="Well-A1")
    well_type: Optional[str] = Field("producer", example="producer") # producer/injector/observation
    status: Optional[str] = Field("active", example="active") # active/inactive/abandoned
    depth: Optional[float] = Field(None, example=10000.0) # ft
    reservoir_id: int

class ProductionDataBase(BaseModel):
    well_id: int
    date: date
    oil_rate: Optional[float] = Field(None, example=1200.5) # bbl/day
    gas_rate: Optional[float] = Field(None, example=850.0)  # Mcf/day (thousand cubic feet)
    water_rate: Optional[float] = Field(None, example=300.0) # bbl/day
    bottomhole_pressure: Optional[float] = Field(None, example=2800.0) # psi

class PVTDataBase(BaseModel):
    well_id: int
    pressure: float = Field(..., example=3000.0) # psi
    temperature: float = Field(..., example=180.0) # °F
    oil_fvf: Optional[float] = Field(None, example=1.25)  # Oil Formation Volume Factor (rb/STB)
    gas_fvf: Optional[float] = Field(None, example=0.005)  # Gas Formation Volume Factor (rcf/scf)
    oil_viscosity: Optional[float] = Field(None, example=0.8) # cp
    gas_viscosity: Optional[float] = Field(None, example=0.015) # cp
    solution_gor: Optional[float] = Field(None, example=750.0)  # Solution Gas-Oil Ratio (scf/STB)

class SimulationBase(BaseModel):
    reservoir_id: int
    name: str = Field(..., example="Base Case Simulation")
    type: Optional[str] = Field("black-oil", example="black-oil") # black-oil, compositional, etc.
    parameters: Optional[Dict[str, Any]] = Field(None, example={"grid_cells_x": 50, "time_step_days": 30}) # JSON-encoded simulation parameters

# ----- Create Schemas (for POST requests, inherits from Base) -----

class ReservoirCreate(ReservoirBase):
    pass

class WellCreate(WellBase):
    pass

class ProductionDataCreate(ProductionDataBase):
    pass

class PVTDataCreate(PVTDataBase):
    pass

class SimulationCreate(SimulationBase):
    pass

# ----- Update Schemas (for PUT requests, all fields optional) -----
# Pydantic models for PUT should have all fields optional.
# You can create these by iterating over FooBase.__fields__ and making them Optional.
# For simplicity, we'll define them explicitly if needed or rely on .dict(exclude_unset=True)

class ReservoirUpdate(ReservoirBase):
    name: Optional[str] = None # Allow name updates, ensure uniqueness in DataManager
    # All other fields are already Optional in ReservoirBase or become optional here

class WellUpdate(WellBase):
    name: Optional[str] = None
    reservoir_id: Optional[int] = None # Allow moving well to different reservoir
    # All other fields are already Optional in WellBase or become optional here

# ProductionData and PVTData are often immutable or time-series; updates might be deletions + new entries.
# If direct updates are needed, create specific Update schemas.

class SimulationUpdate(SimulationBase):
    reservoir_id: Optional[int] = None
    name: Optional[str] = None
    status: Optional[str] = Field(None, example="completed") # To update simulation status
    results_path: Optional[str] = Field(None, example="/sim_results/final_run.dat")


# ----- Response Schemas (for GET requests, includes ID and timestamps) -----

class Reservoir(ReservoirBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Well(WellBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ProductionData(ProductionDataBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class PVTData(PVTDataBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class Simulation(SimulationBase):
    id: int
    run_date: datetime # This comes from the model's server_default
    status: Optional[str] = Field(None, example="completed")
    results_path: Optional[str] = Field(None, example="/sim_results/final_run.dat")

    class Config:
        orm_mode = True

# ----- Schemas with Relationships (for richer GET responses) -----

class WellWithDetails(Well):
    production_data: List[ProductionData] = []
    pvt_data: List[PVTData] = []

class ReservoirWithDetails(Reservoir):
    wells: List[Well] = [] # Could be WellWithDetails for even more nesting
    simulations: List[Simulation] = []

# For PVT Module
class FluidComponent(BaseModel):
    name: str = Field(..., example="Methane")
    molecular_weight: float = Field(..., example=16.04)
    critical_pressure: float = Field(..., example=667.8)  # psi
    critical_temperature: float = Field(..., example=343.0)  # °R
    acentric_factor: float = Field(..., example=0.008)
    critical_volume: float = Field(..., example=1.59) # ft³/lb-mol
    parachor: float = Field(..., example=77.0) # For surface tension calculation
    mole_fraction: float = Field(0.0, example=0.75, ge=0, le=1)

class PVTResult(BaseModel):
    pressure: float  # psi
    temperature: float  # °F
    oil_fvf: Optional[float] = None # rb/STB
    gas_fvf: Optional[float] = None # rcf/scf
    solution_gor: Optional[float] = None # scf/STB
    oil_viscosity: Optional[float] = None # cp
    gas_viscosity: Optional[float] = None # cp
    oil_density: Optional[float] = None # lb/ft³
    gas_density: Optional[float] = None # lb/ft³
    surface_tension: Optional[float] = None # dynes/cm
    # You might also include Z-factors for liquid and vapor if needed for display
    # z_liquid: Optional[float] = None
    # z_vapor: Optional[float] = None

class BlackOilModelCreateRequest(BaseModel):
    name: str = Field(..., example="DefaultBlackOil")
    pvt_data: Dict[str, float] = Field(..., example={
        "pb": 2500, "co": 1.8e-5, "rsb": 750, "bob": 1.42,
        "muob": 0.85, "muod": 3.2, "cg": 3.2e-4,
        "gamma_g": 0.78, "gamma_o": 0.86, "temperature": 180
    })

class CompositionalModelCreateRequest(BaseModel):
    name: str = Field(..., example="RichGasCondensate")
    components: List[FluidComponent]

class PVTCalculationRequest(BaseModel):
    model_name: str
    pressure: float
    temperature: float

class PVTTableRequest(BaseModel):
    model_name: str
    pressure_range: Tuple[float, float, float] = Field(..., example=(500, 5000, 500)) # (start, stop, step)
    temperature: float

class PhaseEnvelopeRequest(BaseModel):
    model_name: str
    temperature_range: Optional[Tuple[float, float, float]] = Field((50, 300, 10), example=(50, 350, 20))
    max_pressure: Optional[float] = Field(10000, example=10000.0)

class PhaseEnvelopePoint(BaseModel):
    temperature: float
    pressure: float
    type: str # "bubble" or "dew" or "critical"
