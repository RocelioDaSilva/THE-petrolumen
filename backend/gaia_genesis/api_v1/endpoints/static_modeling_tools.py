from fastapi import APIRouter, HTTPException, Depends, Body, Query
from typing import List, Dict, Optional, Union

# Models
from backend.gaia_genesis.api_v1.models.static_modeling_models import (
    GridDefinition, StaticWellDataRequest,
    VariogramCalculationRequest, VariogramResponse, VariogramPoint,
    KrigingRequest, KrigingResponse,
    RockPhysicsRequestBase, GassmannRequest, HertzMindlinRequest, RockPhysicsResponse, RockPhysicsModels, # Added RockPhysicsModels
    NMRAnalysisRequest, NMRAnalysisResponse
)

# Core logic class
from backend.gaia_genesis.static_modeling import StaticModeling

# Auth dependency
from backend.main import get_current_active_user, UserResponse, logger # Assuming UserResponse is the model for current_user

router = APIRouter()

# Global instance of StaticModeling tool.
# WARNING: This shares state across all users/requests.
# For production, state management (per user/session/project) would be needed.
static_model_analyzer = StaticModeling()

# --- Grid and Data Setup Endpoints ---
@router.post("/static-modeling/grid", status_code=201, tags=["Static Modeling Tools", "Setup"])
async def define_static_grid(
    grid_data: GridDefinition = Body(...),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Defines the 3D grid dimensions for the current static model in the shared analyzer.
    This grid will be used for subsequent operations like kriging.
    WARNING: Modifies a shared global instance of the static model analyzer. Not concurrency-safe.
    """
    try:
        static_model_analyzer.create_3d_grid(
            nx=grid_data.nx, ny=grid_data.ny, nz=grid_data.nz,
            dx=grid_data.dx, dy=grid_data.dy, dz=grid_data.dz
        )
        logger.info(f"User {current_user.username} defined static grid: {grid_data.model_dump()}")
        return {"message": "Grid defined successfully in shared static model analyzer.", "grid_definition": grid_data}
    except Exception as e:
        logger.error(f"Error defining static grid: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error defining grid: {str(e)}")

@router.post("/static-modeling/well-data", status_code=201, tags=["Static Modeling Tools", "Setup"])
async def add_static_well_data(
    well_data_request: StaticWellDataRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Adds well data (coordinates and properties like porosity, permeability logs)
    to the shared static model analyzer.
    WARNING: Modifies a shared global instance. Not concurrency-safe.
    """
    try:
        # Convert Pydantic model to dict format expected by StaticModeling class
        properties_for_class = {}
        for prop_name, prop_data in well_data_request.properties.items():
            properties_for_class[prop_name] = np.array(prop_data.values) # StaticModeling expects numpy array for values

        static_model_analyzer.add_well_data(
            well_name=well_data_request.well_name,
            x=well_data_request.x_coord,
            y=well_data_request.y_coord,
            md=np.array(next(iter(well_data_request.properties.values())).md), # Assume all properties share same MD
            properties=properties_for_class
        )
        logger.info(f"User {current_user.username} added well data for {well_data_request.well_name}.")
        return {"message": f"Well data for '{well_data_request.well_name}' added successfully."}
    except Exception as e:
        logger.error(f"Error adding well data for {well_data_request.well_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error adding well data: {str(e)}")

# --- Geostatistical Analysis Endpoints ---
@router.post("/static-modeling/variogram", response_model=VariogramResponse, tags=["Static Modeling Tools", "Geostatistics"])
async def calculate_property_variogram(
    request_data: VariogramCalculationRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Calculates and fits a variogram for a specified well property.
    Assumes well data for the property has already been loaded.
    """
    try:
        static_model_analyzer.calculate_variogram(
            property_name=request_data.property_name,
            variogram_model=request_data.variogram_model_type,
            direction=request_data.direction,
            max_lag=request_data.max_lag_distance,
            n_lags=request_data.number_of_lags
        )

        variogram_data = static_model_analyzer.variograms.get(request_data.property_name)
        if not variogram_data:
            raise HTTPException(status_code=404, detail=f"Variogram for property '{request_data.property_name}' could not be generated or found.")

        experimental_points = [
            VariogramPoint(lag=l, gamma=g, num_pairs=int(n)) # Ensure num_pairs is int
            for l, g, n in zip(variogram_data['experimental']['lags'], variogram_data['experimental']['gamma'], variogram_data['experimental']['n_pairs'])
        ]

        return VariogramResponse(
            property_name=request_data.property_name,
            experimental_variogram=experimental_points,
            fitted_model_type=variogram_data['model_type'],
            fitted_model_parameters=variogram_data['parameters'],
            fitted_model_values=variogram_data['model_fit'].tolist() if isinstance(variogram_data.get('model_fit'), np.ndarray) else variogram_data.get('model_fit')
        )
    except ValueError as ve:
        logger.error(f"ValueError in variogram calculation: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error calculating variogram for {request_data.property_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error calculating variogram: {str(e)}")

@router.post("/static-modeling/kriging", response_model=KrigingResponse, tags=["Static Modeling Tools", "Geostatistics"])
async def perform_kriging_interpolation(
    request_data: KrigingRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Performs 2D kriging interpolation for a specified property.
    Assumes grid, well data, and variogram for the property are already set/calculated.
    """
    try:
        if not static_model_analyzer.grid:
            raise ValueError("Grid not defined in static model analyzer. Please define grid first.")
        if request_data.property_name not in static_model_analyzer.well_data and \
           request_data.property_name not in static_model_analyzer.properties: # check if property exists from wells
             # Check if the property exists in any well data
            prop_found_in_wells = any(request_data.property_name in well.get('properties', {}) for well in static_model_analyzer.well_data.values())
            if not prop_found_in_wells:
                raise ValueError(f"No well data found for property '{request_data.property_name}'. Please add well data first.")

        # Kriging might implicitly use a variogram if previously calculated by StaticModeling class
        # The class uses sklearn GPR which handles variogram internally via kernel
        static_model_analyzer.kriging_interpolation(
            property_name=request_data.property_name
            # variogram_model parameter is not directly used by current kriging_interpolation method
            # which uses GaussianProcessRegressor. The kernel choice in GPR implies a variogram model.
        )

        interpolated_values = static_model_analyzer.properties.get(request_data.property_name)
        std_dev_values = static_model_analyzer.properties.get(f"{request_data.property_name}_kriging_std")

        if interpolated_values is None:
            raise HTTPException(status_code=500, detail=f"Kriging failed or produced no output for property '{request_data.property_name}'.")

        # Convert numpy arrays to lists for Pydantic model
        interpolated_list = interpolated_values.tolist() if isinstance(interpolated_values, np.ndarray) else interpolated_values
        std_dev_list = std_dev_values.tolist() if isinstance(std_dev_values, np.ndarray) else std_dev_values

        grid_dims = (static_model_analyzer.grid['nx'], static_model_analyzer.grid['ny']) if static_model_analyzer.grid else None

        return KrigingResponse(
            property_name=request_data.property_name,
            interpolated_grid_values=interpolated_list,
            kriging_std_dev_grid_values=std_dev_list,
            grid_dimensions=grid_dims
        )
    except ValueError as ve:
        logger.error(f"ValueError in kriging: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error performing kriging for {request_data.property_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error performing kriging: {str(e)}")

# --- Rock Physics Endpoints ---
@router.post("/static-modeling/rock-physics", response_model=RockPhysicsResponse, tags=["Static Modeling Tools", "Rock Physics"])
async def calculate_rock_physics_properties(
    # Using a Union of specific request models for discriminated union behavior if needed by frontend
    request_data: RockPhysicsModels = Body(...), # FastAPI will try to match one of them
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Calculates saturated rock physics properties using Gassmann or Hertz-Mindlin models.
    Input parameters depend on the chosen model_type.
    """
    try:
        # The StaticModeling class's rock_physics_modeling method takes property_name as first arg
        # which seems to be for naming the output. We can use a generic name or derive from model_type.
        # Let's use a generic name for the purpose of calling the method.
        # The actual parameters are passed via **request_data.model_dump() after model_type

        # The StaticModeling().rock_physics_modeling method needs to be adapted
        # to take parameters like k_dry, k_matrix etc. from the request, not hardcoded.
        # For now, this endpoint acts as a placeholder until StaticModeling class is refactored
        # to accept these inputs directly.

        # This is a conceptual call, the StaticModeling.rock_physics_modeling method
        # needs to be updated to accept these detailed parameters from the request.
        # For now, it uses hardcoded values primarily.

        # Let's assume we pass the dict of the specific model (GassmannRequest or HertzMindlinRequest)
        # to a refactored rock_physics_modeling method.
        # For now, we'll call it with the model_type and it will use its internal defaults mostly.
        # This needs to be improved in StaticModeling class.

        if request_data.model_type == "gassmann":
            # Manually pass parameters for Gassmann to the method if it were refactored
            # For now, we rely on the existing structure and it will use its defaults mostly.
            # This is a known limitation of the current StaticModeling class method.
            static_model_analyzer.rock_physics_modeling(
                property_name=f"output_{request_data.model_type}", # Dummy name
                model_type=request_data.model_type
                # TODO: Refactor StaticModeling.rock_physics_modeling to accept:
                # k_dry=request_data.k_dry, k_matrix=request_data.k_matrix, etc.
            )
        elif request_data.model_type == "hertz_mindlin":
            static_model_analyzer.rock_physics_modeling(
                property_name=f"output_{request_data.model_type}", # Dummy name
                model_type=request_data.model_type
                # TODO: Refactor for HertzMindlin specific params
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported rock physics model type: {request_data.model_type}")

        # Retrieve results (these are based on the output structure of StaticModeling)
        # The naming convention in StaticModeling is f'{property_name}_{model_type}'
        result_key = f"output_{request_data.model_type}_{request_data.model_type}" # e.g. output_gassmann_gassmann

        # A better way would be for rock_physics_modeling to return the dict directly
        # For now, trying to retrieve from self.properties
        if result_key not in static_model_analyzer.properties:
             # Fallback if the specific key isn't there, maybe it's just named output_gassmann
            simple_result_key = f"output_{request_data.model_type}"
            if simple_result_key not in static_model_analyzer.properties:
                raise HTTPException(status_code=500, detail=f"Rock physics calculation for '{request_data.model_type}' did not store results as expected.")
            result_data = static_model_analyzer.properties[simple_result_key]
        else:
            result_data = static_model_analyzer.properties[result_key]


        return RockPhysicsResponse(
            model_type=request_data.model_type,
            k_saturated=result_data.get('K_sat', 0),
            g_saturated=result_data.get('G_sat', 0),
            vp=result_data.get('Vp', 0),
            vs=result_data.get('Vs', 0),
            rho_bulk=result_data.get('rho_bulk', 0)
        )
    except ValueError as ve:
        logger.error(f"ValueError in rock physics calculation: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in rock physics calculation for {request_data.model_type}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error in rock physics calculation: {str(e)}")


# --- NMR Analysis Endpoint ---
@router.post("/static-modeling/nmr-analysis", response_model=NMRAnalysisResponse, tags=["Static Modeling Tools", "NMR"])
async def perform_nmr_analysis(
    request_data: NMRAnalysisRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Performs NMR T2 data analysis for a specified well.
    """
    try:
        static_model_analyzer.analyze_nmr_data(
            well_name=request_data.well_name,
            t2_distribution=np.array(request_data.t2_distribution),
            t2_times=np.array(request_data.t2_times)
        )

        nmr_results = static_model_analyzer.nmr_data.get(request_data.well_name)
        if not nmr_results:
            raise HTTPException(status_code=404, detail=f"NMR analysis for well '{request_data.well_name}' failed or produced no results.")

        return NMRAnalysisResponse(
            well_name=request_data.well_name,
            t2_log_mean=nmr_results.get('t2_ml', 0),
            bulk_volume_irreducible=nmr_results.get('bvi', 0),
            free_fluid_volume=nmr_results.get('ffv', 0),
            pore_sizes_microns=nmr_results.get('pore_sizes'),
            permeability_coates_md=nmr_results.get('k_coates'),
            permeability_sdr_md=nmr_results.get('k_sdr'),
            capillary_pressure_psi_proxy=nmr_results.get('pc'),
            t2_distribution_echo=nmr_results.get('t2_distribution', []), # Echo back inputs
            t2_times_echo=nmr_results.get('t2_times', [])
        )
    except ValueError as ve:
        logger.error(f"ValueError in NMR analysis: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in NMR analysis for {request_data.well_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error in NMR analysis: {str(e)}")

# Helper for numpy array usage in StaticModeling class (internal, not an endpoint)
import numpy as np
