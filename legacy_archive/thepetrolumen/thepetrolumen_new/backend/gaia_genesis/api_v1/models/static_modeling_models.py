from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union, Tuple, Literal


# --- Grid Definition (Potentially implicit or part of a session) ---
class GridDefinition(BaseModel):
    nx: int
    ny: int
    nz: int
    dx: float
    dy: float
    dz: float


# --- Well Data for Static Modeling ---
class WellPropertyData(BaseModel):
    md: List[float] = Field(..., description="Measured depths")
    values: List[float] = Field(..., description="Property values at corresponding MDs")


class StaticWellDataRequest(BaseModel):
    well_name: str
    x_coord: float
    y_coord: float
    properties: Dict[
        str, WellPropertyData
    ]  # e.g., {"Porosity": WellPropertyData(...), "Perm": WellPropertyData(...)}


# --- Variogram Models ---
class VariogramCalculationRequest(BaseModel):
    property_name: str = Field(
        ...,
        description=(
            "Name of the well property to analyze (must be loaded via "
            "StaticWellDataRequest first or available through other means)."
        ),
    )
    # Assuming well data is already loaded and associated with property_name.
    # If data needs to be passed directly:
    # locations: List[Tuple[float,float,float]] # x,y,z coordinates
    # values: List[float] # property values
    variogram_model_type: str = Field(
        default="spherical",
        description="Type of variogram model ('spherical', 'exponential', 'gaussian')",
    )
    direction: Optional[str] = Field(
        default="omnidirectional",
        description=(
            "Direction of variogram (e.g., 'omnidirectional', '0_degrees', "
            "'90_degrees') - currently only omni is fully supported in core."
        ),
    )
    max_lag_distance: Optional[float] = Field(
        None,
        description=(
            "Maximum lag distance. If None, defaults to half max distance between points."
        ),
    )
    number_of_lags: int = Field(
        default=10, description="Number of lags for the experimental variogram."
    )


class VariogramPoint(BaseModel):
    lag: float
    gamma: float
    num_pairs: int


class VariogramResponse(BaseModel):
    property_name: str
    experimental_variogram: List[VariogramPoint]
    fitted_model_type: str
    fitted_model_parameters: Dict[
        str, float
    ]  # e.g., {'c0': nugget, 'c1': sill-nugget, 'a': range}
    fitted_model_values: Optional[List[float]] = Field(
        None,
        description="Gamma values from the fitted model curve at experimental lag points",
    )


# --- Kriging Interpolation Models ---
class KrigingRequest(BaseModel):
    property_name: str = Field(
        ..., description="Name of the well property to interpolate."
    )
    # Assumes grid and variogram for this property are already defined/calculated in
    # the StaticModeling instance.
    # variogram_model: Optional[str] = Field(default='spherical', description=(
    # "Variogram model to use if not already fitted for the property."
    # ))
    # For simplicity, kriging will use the existing fitted variogram for the property
    # or raise error. Grid for interpolation target is assumed to be the one set in
    # StaticModeling instance.


class KrigingResponse(BaseModel):
    property_name: str
    interpolated_grid_values: List[List[float]]  # Assuming 2D grid for now (nx, ny)
    kriging_std_dev_grid_values: Optional[List[List[float]]] = (
        None  # Standard deviation map
    )
    grid_dimensions: Optional[Tuple[int, int]] = Field(
        None, description="(nx, ny) dimensions of the returned grid"
    )


# --- Rock Physics Models ---
class RockPhysicsRequestBase(BaseModel):
    model_type: str = Field(
        ..., description="Rock physics model type (e.g., 'gassmann', 'hertz_mindlin')"
    )
    porosity: float = Field(..., ge=0, le=1, description="Porosity (fraction)")
    # Other parameters will be specific to the model type


class GassmannRequest(RockPhysicsRequestBase):
    model_type: Literal["gassmann"] = "gassmann"
    k_dry: float = Field(..., description="Dry rock bulk modulus (GPa)")
    k_matrix: float = Field(..., description="Matrix (grain) bulk modulus (GPa)")
    k_fluid: float = Field(..., description="Fluid bulk modulus (GPa)")
    g_matrix: float = Field(
        ..., description="Matrix (grain) shear modulus (GPa) - used to estimate G_dry"
    )
    # rho_matrix: float = Field(default=2.65, description="Matrix density (g/cm³)")
    # rho_fluid: float = Field(default=1.0, description="Fluid density (g/cm³)")


class HertzMindlinRequest(RockPhysicsRequestBase):
    model_type: Literal["hertz_mindlin"] = "hertz_mindlin"
    g_matrix: float = Field(..., description="Matrix (grain) shear modulus (GPa)")
    k_matrix: float = Field(
        ..., description="Matrix (grain) bulk modulus (GPa)"
    )  # Added K_matrix for consistency
    critical_porosity: float = Field(
        default=0.4, description="Critical porosity (fraction)"
    )
    effective_pressure: float = Field(
        default=20.0, description="Effective pressure (MPa)"
    )
    poisson_ratio_matrix: float = Field(
        default=0.25, description="Poisson's ratio of the matrix material"
    )
    # rho_matrix: float = Field(default=2.65, description="Matrix density (g/cm³)")
    # rho_fluid: float = Field(default=1.0, description="Fluid density (g/cm³)")


class RockPhysicsResponse(BaseModel):
    model_type: str
    k_saturated: float = Field(description="Saturated bulk modulus (GPa)")
    g_saturated: float = Field(description="Saturated shear modulus (GPa)")
    vp: float = Field(description="P-wave velocity (km/s)")
    vs: float = Field(description="S-wave velocity (km/s)")
    rho_bulk: float = Field(description="Bulk density (g/cm³)")


# --- NMR Analysis Models ---
class NMRAnalysisRequest(BaseModel):
    well_name: str  # To associate results, though StaticModeling class stores it under well_name
    t2_distribution: List[float] = Field(..., description="T2 distribution amplitudes")
    t2_times: List[float] = Field(..., description="Corresponding T2 times (ms)")


class NMRAnalysisResponse(BaseModel):
    well_name: str
    t2_log_mean: float = Field(description="Logarithmic mean of T2 distribution (ms)")
    bulk_volume_irreducible: float = Field(
        description="Bulk Volume Irreducible water (BVI) (fraction of total porosity)"
    )
    free_fluid_volume: float = Field(
        description="Free Fluid Volume (FFV) (fraction of total porosity)"
    )
    pore_sizes_microns: Optional[List[float]] = Field(
        None, description="Estimated pore sizes (microns)"
    )
    permeability_coates_md: Optional[float] = Field(
        None, description="Permeability from Coates model (mD)"
    )
    permeability_sdr_md: Optional[float] = Field(
        None, description="Permeability from SDR model (mD)"
    )
    capillary_pressure_psi_proxy: Optional[List[float]] = Field(
        None,
        description="Proxy capillary pressure curve (psi), values correspond to T2 amplitudes",
    )
    t2_distribution_echo: List[float]  # Echo back input for context
    t2_times_echo: List[float]  # Echo back input for context


RockPhysicsModels = Union[GassmannRequest, HertzMindlinRequest]
