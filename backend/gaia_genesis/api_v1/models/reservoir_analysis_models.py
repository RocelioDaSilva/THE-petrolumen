from pydantic import BaseModel, Field
from typing import List, Optional

# --- Material Balance Models ---


class MaterialBalanceInputBase(BaseModel):
    pressure_history: List[float] = Field(
        ..., description="Array of historical reservoir pressures (psia)"
    )
    production_history: List[float] = Field(
        ...,
        description="Array of historical cumulative production (oil in STB, gas in SCF)",
    )
    temperature: float = Field(..., description="Reservoir temperature (°F)")
    # Common PVT properties needed by MaterialBalance class methods
    # These might be simplified if the backend MaterialBalance class fetches detailed
    # PVT itself. For now, assuming these are direct inputs as per the class methods.


class OGIPRequest(MaterialBalanceInputBase):
    gas_specific_gravity: float = Field(..., description="Specific gravity of the gas")


class OGIPResponse(BaseModel):
    ogip: float = Field(description="Estimated Original Gas In Place (SCF)")
    # Could also include F and Eg arrays if useful for plotting/validation by frontend


class STOIIPRequest(MaterialBalanceInputBase):
    api_gravity: float = Field(..., description="API gravity of the oil")
    gas_specific_gravity: float = Field(
        ..., description="Specific gravity of the solution gas"
    )
    # The MaterialBalance class in reservoir_engineering.py also uses Bo_initial,
    # Rs_initial, Bg_initial, Bw_initial, cw, cf. These are passed as
    # 'rock_properties' or calculated from initial conditions. For simplicity, these
    # could be added here, or the backend endpoint could assume some defaults/derive them.
    # Let's add a few critical ones, assuming others might be defaulted or handled by
    # the class.
    bo_initial: Optional[float] = Field(
        None, description="Initial oil formation volume factor (rb/STB)"
    )
    rs_initial: Optional[float] = Field(
        None, description="Initial solution gas-oil ratio (SCF/STB)"
    )
    # For a more complete model, water influx parameters (We) and rock/connate water
    # compressibility (cw, cf) would be needed. The current MaterialBalance class
    # calculates Eo, Ew, Ef. Ew and Ef implicitly use compressibilities.


class STOIIPResponse(BaseModel):
    stoiip: float = Field(description="Estimated Original Oil In Place (STB)")
    # Could also include F, Eo, Ew, Ef arrays


# --- Well Testing Models ---


class WellTestInputBase(BaseModel):
    time_data: List[float] = Field(
        ..., description="Array of time data (e.g., hours for buildup/drawdown)"
    )
    pressure_data: List[float] = Field(
        ..., description="Array of pressure data (psia) corresponding to time_data"
    )
    production_rate: float = Field(
        ...,
        description=(
            "Production rate before shut-in (for buildup) or constant rate during "
            "test (for drawdown) (STB/day or SCF/day)"
        ),
    )
    fluid_viscosity: float = Field(
        ..., description="Viscosity of the flowing fluid (cp)"
    )
    total_compressibility: float = Field(
        ..., description="Total system compressibility (psi^-1)"
    )
    formation_porosity: float = Field(..., description="Formation porosity (fraction)")
    wellbore_radius: float = Field(..., description="Wellbore radius (ft)")
    # Optional: Formation thickness (h) is often needed for permeability-thickness (kh)
    formation_thickness: Optional[float] = Field(
        None,
        description=(
            "Net pay thickness (ft), if permeability (k) is desired instead of kh."
        ),
    )


class BuildupTestAnalysisRequest(WellTestInputBase):
    # tp: Optional[float] = Field(None, description=(
    # "Producing time before shut-in (hours). If not provided, assumed last "
    # "time_data point."
    # ))
    # The WellTesting class calculates tp from time[-1], so not strictly needed here
    # as input.
    pass


class WellTestAnalysisResponse(BaseModel):
    permeability: float = Field(
        description=(
            "Estimated formation permeability (md). If h not provided, this might be "
            "kh/h."
        )
    )
    skin_factor: float = Field(description="Estimated skin factor")
    slope: Optional[float] = Field(
        None, description="Slope of the Horner/semilog plot line (psi/cycle)"
    )
    intercept: Optional[float] = Field(
        None, description="Intercept of the Horner/semilog plot line (psi)"
    )
    # Could add other results like wellbore storage coefficient, radius of
    # investigation if calculated.


class DrawdownTestAnalysisRequest(WellTestInputBase):
    pass


# --- Decline Curve Analysis - EUR Calculation Model ---
# Based on DeclineAnalysis class in reservoir_engineering.py


class EURCalculationRequest(BaseModel):
    qi: float = Field(..., description="Initial production rate")
    Di: float = Field(
        ...,
        description=(
            "Initial decline rate (e.g., per day or per month, consistent with "
            "time unit used for EUR calculation)"
        ),
    )
    b: float = Field(
        ...,
        description=(
            "Arps b-factor (0 for exponential, 1 for harmonic, 0-1 for hyperbolic)"
        ),
    )
    method_type: str = Field(
        ..., description="Decline method type ('exponential', 'harmonic', 'hyperbolic')"
    )
    # The EUR calculation in DeclineAnalysis has a hardcoded 30-year limit.
    # We could make the forecast limit or abandonment rate an input if more
    # flexibility is needed.


class EURCalculationResponse(BaseModel):
    eur: float = Field(
        description="Estimated Ultimate Recovery (units consistent with qi and Di)"
    )
