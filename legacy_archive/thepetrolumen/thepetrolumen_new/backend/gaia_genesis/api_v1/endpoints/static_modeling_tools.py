from fastapi import APIRouter, HTTPException, Depends, Body
import numpy as np
import logging

# Models
# Imports adjusted for typical project structure
try:
    from ..models.static_modeling_models import (  # Relative import
        GridDefinition,
        StaticWellDataRequest,
        VariogramCalculationRequest,
        VariogramResponse,
        VariogramPoint,
        KrigingRequest,
        KrigingResponse,
        # RockPhysicsRequestBase, # Unused
        # GassmannRequest, # Unused
        # HertzMindlinRequest, # Unused
        RockPhysicsResponse,
        RockPhysicsModels,
        NMRAnalysisRequest,
        NMRAnalysisResponse,
    )

    # Core logic class
    from gaia_genesis.static_modeling import StaticModeling

    # Auth dependency
    from main import get_current_active_user, UserResponse
except ImportError as e:
    error_message = (
        f"Could not import dependencies for Static Modeling Tools router: {e}."
    )
    logging.error(error_message, exc_info=True)
    raise ImportError(error_message)

router = APIRouter()
logger = logging.getLogger(__name__)  # Initialize logger for this module

# Global instance of StaticModeling tool.
# WARNING: This shares state across all users/requests.
static_model_analyzer = StaticModeling()


# --- Grid and Data Setup Endpoints ---
@router.post(
    "/static-modeling/grid", status_code=201, tags=["Static Modeling Tools", "Setup"]
)
async def define_static_grid(
    grid_data: GridDefinition = Body(...),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Defines the 3D grid dimensions for the current static model in the shared analyzer.
    WARNING: Modifies a shared global instance of the static model analyzer.
    Not concurrency-safe.
    """
    try:
        static_model_analyzer.create_3d_grid(
            nx=grid_data.nx,
            ny=grid_data.ny,
            nz=grid_data.nz,
            dx=grid_data.dx,
            dy=grid_data.dy,
            dz=grid_data.dz,
        )
        logger.info(
            f"User {current_user.username} defined static grid: {grid_data.model_dump()}"
        )
        return {
            "message": "Grid defined successfully in shared static model analyzer.",
            "grid_definition": grid_data,
        }
    except Exception as e:
        logger.error(f"Error defining static grid: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error defining grid: {str(e)}")


@router.post(
    "/static-modeling/well-data",
    status_code=201,
    tags=["Static Modeling Tools", "Setup"],
)
async def add_static_well_data(
    well_data_request: StaticWellDataRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Adds well data to the shared static model analyzer.
    WARNING: Modifies a shared global instance. Not concurrency-safe.
    """
    try:
        properties_for_class = {}
        # Ensure md values are present and consistent before creating numpy array
        md_values = None
        if well_data_request.properties:
            first_prop_key = next(iter(well_data_request.properties))
            md_values = np.array(well_data_request.properties[first_prop_key].md)
        else:  # No properties provided, which might be an issue for some operations
            logger.warning("No properties provided in StaticWellDataRequest.")
            # Depending on requirements, might raise error or proceed if only coords are
            # needed for some step. For now, proceed but StaticModeling class might
            # fail later if it expects properties.

        for prop_name, prop_data in well_data_request.properties.items():
            properties_for_class[prop_name] = np.array(prop_data.values)
            # Could add a check here:
            # if np.array(prop_data.md).tolist() != md_values.tolist():
            # raise ValueError("MD mismatch")

        static_model_analyzer.add_well_data(
            well_name=well_data_request.well_name,
            x=well_data_request.x_coord,
            y=well_data_request.y_coord,
            md=(
                md_values if md_values is not None else np.array([])
            ),  # Pass empty array if no properties
            properties=properties_for_class,
        )
        logger.info(
            f"User {current_user.username} added well data for "
            f"{well_data_request.well_name}."
        )
        return {
            "message": f"Well data for '{well_data_request.well_name}' added successfully."
        }
    except ValueError as ve:  # Catch specific errors like MD mismatch if added
        logger.error(
            f"ValueError adding well data for {well_data_request.well_name}: {ve}",
            exc_info=True,
        )
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(
            f"Error adding well data for {well_data_request.well_name}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Error adding well data: {str(e)}")


# --- Geostatistical Analysis Endpoints ---
@router.post(
    "/static-modeling/variogram",
    response_model=VariogramResponse,
    tags=["Static Modeling Tools", "Geostatistics"],
)
async def calculate_property_variogram(
    request_data: VariogramCalculationRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Calculates and fits a variogram for a specified well property.
    """
    try:
        static_model_analyzer.calculate_variogram(
            property_name=request_data.property_name,
            variogram_model=request_data.variogram_model_type,
            direction=request_data.direction,
            max_lag=request_data.max_lag_distance,
            n_lags=request_data.number_of_lags,
        )

        variogram_data = static_model_analyzer.variograms.get(
            request_data.property_name
        )
        if not variogram_data:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Variogram for property '{request_data.property_name}' "
                    "could not be generated or found."
                ),
            )

        experimental_points = [
            VariogramPoint(lag=lag_val, gamma=g, num_pairs=int(n))
            for lag_val, g, n in zip(
                variogram_data["experimental"]["lags"],
                variogram_data["experimental"]["gamma"],
                variogram_data["experimental"]["n_pairs"],
            )
        ]

        model_fit_values = variogram_data.get("model_fit")
        if isinstance(model_fit_values, np.ndarray):
            model_fit_values = model_fit_values.tolist()

        return VariogramResponse(
            property_name=request_data.property_name,
            experimental_variogram=experimental_points,
            fitted_model_type=variogram_data["model_type"],
            fitted_model_parameters=variogram_data["parameters"],
            fitted_model_values=model_fit_values,
        )
    except ValueError as ve:
        logger.warning(
            f"ValueError in variogram calculation for {request_data.property_name}: {ve}"
        )
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(
            f"Error calculating variogram for {request_data.property_name}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Error calculating variogram: {str(e)}"
        )


@router.post(
    "/static-modeling/kriging",
    response_model=KrigingResponse,
    tags=["Static Modeling Tools", "Geostatistics"],
)
async def perform_kriging_interpolation(
    request_data: KrigingRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Performs 2D kriging interpolation for a specified property.
    """
    try:
        if not static_model_analyzer.grid:
            raise ValueError(
                "Grid not defined in static model analyzer. Please define grid first."
            )

        prop_found_in_wells = any(
            request_data.property_name in well.get("properties", {})
            for well_name, well in static_model_analyzer.well_data.items()
        )
        if not prop_found_in_wells:
            raise ValueError(
                f"No well data found for property '{request_data.property_name}'. "
                "Please add well data first."
            )

        static_model_analyzer.kriging_interpolation(
            property_name=request_data.property_name
        )

        interpolated_values = static_model_analyzer.properties.get(
            request_data.property_name
        )
        std_dev_values = static_model_analyzer.properties.get(
            f"{request_data.property_name}_kriging_std"
        )

        if interpolated_values is None:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Kriging failed or produced no output for property "
                    f"'{request_data.property_name}'."
                ),
            )

        interpolated_list = (
            interpolated_values.tolist()
            if isinstance(interpolated_values, np.ndarray)
            else interpolated_values
        )
        std_dev_list = (
            std_dev_values.tolist()
            if isinstance(std_dev_values, np.ndarray)
            else std_dev_values
        )
        grid_dims = (
            (static_model_analyzer.grid["nx"], static_model_analyzer.grid["ny"])
            if static_model_analyzer.grid
            else None
        )

        return KrigingResponse(
            property_name=request_data.property_name,
            interpolated_grid_values=interpolated_list,
            kriging_std_dev_grid_values=std_dev_list,
            grid_dimensions=grid_dims,
        )
    except ValueError as ve:
        logger.warning(f"ValueError in kriging for {request_data.property_name}: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(
            f"Error performing kriging for {request_data.property_name}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Error performing kriging: {str(e)}"
        )


# --- Rock Physics Endpoints ---
@router.post(
    "/static-modeling/rock-physics",
    response_model=RockPhysicsResponse,
    tags=["Static Modeling Tools", "Rock Physics"],
)
async def calculate_rock_physics_properties(
    request_data: RockPhysicsModels = Body(...),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Calculates saturated rock physics properties using Gassmann or Hertz-Mindlin models.
    """
    try:
        # This section needs careful alignment with how
        # StaticModeling.rock_physics_modeling is implemented and what parameters it
        # truly expects and how it returns results. The current StaticModeling class
        # uses hardcoded values mostly. For a functional endpoint, StaticModeling
        # class needs to be refactored.

        # Placeholder: Log the intent and the limitation
        logger.info(
            f"Received rock physics calculation request for model: "
            f"{request_data.model_type}. Note: Current "
            "StaticModeling.rock_physics_modeling uses internal defaults and may not "
            "fully utilize all request parameters."
        )

        # Call the method (it might use its internal defaults or a mix)
        static_model_analyzer.rock_physics_modeling(
            property_name=f"output_{request_data.model_type}",  # Dummy name for now
            model_type=request_data.model_type,
            # Pass actual parameters if StaticModeling class is updated:
            # **request_data.model_dump()
            # if isinstance(request_data, (GassmannRequest, HertzMindlinRequest))
            # else {}
        )

        # Attempt to retrieve results based on how StaticModeling might store them
        result_key_specific = (
            f"output_{request_data.model_type}_{request_data.model_type}"
        )
        result_key_generic = f"output_{request_data.model_type}"

        result_data = static_model_analyzer.properties.get(result_key_specific)
        if result_data is None:
            result_data = static_model_analyzer.properties.get(result_key_generic)

        if result_data is None or not isinstance(result_data, dict):
            logger.error(
                f"Rock physics calculation for '{request_data.model_type}' did not "
                f"produce expected dictionary output. Found: {result_data}"
            )
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Rock physics calculation for '{request_data.model_type}' did "
                    "not store results as expected or result is not a dictionary."
                ),
            )

        return RockPhysicsResponse(
            model_type=request_data.model_type,
            k_saturated=result_data.get("K_sat", 0.0),  # Provide defaults
            g_saturated=result_data.get("G_sat", 0.0),
            vp=result_data.get("Vp", 0.0),
            vs=result_data.get("Vs", 0.0),
            rho_bulk=result_data.get("rho_bulk", 0.0),
        )
    except ValueError as ve:
        logger.warning(
            f"ValueError in rock physics calculation for {request_data.model_type}: {ve}"
        )
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(
            f"Error in rock physics calculation for {request_data.model_type}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Error in rock physics calculation: {str(e)}"
        )


# --- NMR Analysis Endpoint ---
@router.post(
    "/static-modeling/nmr-analysis",
    response_model=NMRAnalysisResponse,
    tags=["Static Modeling Tools", "NMR"],
)
async def perform_nmr_analysis(
    request_data: NMRAnalysisRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Performs NMR T2 data analysis for a specified well.
    """
    try:
        static_model_analyzer.analyze_nmr_data(
            well_name=request_data.well_name,
            t2_distribution=np.array(request_data.t2_distribution),
            t2_times=np.array(request_data.t2_times),
        )

        nmr_results = static_model_analyzer.nmr_data.get(request_data.well_name)
        if not nmr_results:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"NMR analysis for well '{request_data.well_name}' failed or "
                    "produced no results."
                ),
            )

        return NMRAnalysisResponse(
            well_name=request_data.well_name,
            t2_log_mean=nmr_results.get("t2_ml", 0.0),
            bulk_volume_irreducible=nmr_results.get("bvi", 0.0),
            free_fluid_volume=nmr_results.get("ffv", 0.0),
            pore_sizes_microns=nmr_results.get("pore_sizes", []),
            permeability_coates_md=nmr_results.get("k_coates", 0.0),
            permeability_sdr_md=nmr_results.get("k_sdr", 0.0),
            capillary_pressure_psi_proxy=nmr_results.get("pc", []),
            t2_distribution_echo=nmr_results.get("t2_distribution", []),
            t2_times_echo=nmr_results.get("t2_times", []),
        )
    except ValueError as ve:
        logger.warning(f"ValueError in NMR analysis for {request_data.well_name}: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(
            f"Error in NMR analysis for {request_data.well_name}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Error in NMR analysis: {str(e)}")
