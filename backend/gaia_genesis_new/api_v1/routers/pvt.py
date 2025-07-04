from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session # For potential future DB interaction with PVT models
from typing import List, Dict, Any, Tuple # Tuple was missing

# Assuming service.py is in backend.gaia_genesis_new.pvt
# and schemas.py is in backend.gaia_genesis_new.api_v1
from backend.gaia_genesis_new.pvt.service import pvt_service_global_instance as pvt_service # Use the global instance
from backend.gaia_genesis_new.api_v1 import schemas as api_schemas
from backend.gaia_genesis_new.logger import logger
from backend.database import get_db # If PVT models were to be stored in DB

router = APIRouter()

@router.post("/black-oil-model", status_code=status.HTTP_201_CREATED)
def create_black_oil_model_endpoint( # Renamed for clarity
    request: api_schemas.BlackOilModelCreateRequest
    # db: Session = Depends(get_db) # If saving model definition to DB
):
    """
    Create a new Black Oil PVT model.
    The model is stored in-memory for the current server instance.
    """
    logger.info(f"Received request to create black oil model: {request.name}")
    success = pvt_service.create_black_oil_model(request.name, request.pvt_data)
    if not success:
        # This could be due to name conflict or invalid pvt_data dict structure
        logger.error(f"Failed to create black oil model '{request.name}'. It might already exist or data is invalid.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, # Or 400 if data validation failed in service
            detail=f"Black oil model with name '{request.name}' already exists or input data is invalid."
        )
    return {"status": "success", "model_name": request.name, "model_type": "black_oil"}

@router.post("/compositional-model", status_code=status.HTTP_201_CREATED)
def create_compositional_model_endpoint( # Renamed for clarity
    request: api_schemas.CompositionalModelCreateRequest
    # db: Session = Depends(get_db) # If saving model definition to DB
):
    """
    Create a new Compositional PVT model with a list of fluid components.
    The model is stored in-memory for the current server instance.
    """
    logger.info(f"Received request to create compositional model: {request.name} with {len(request.components)} components.")
    try:
        # The components in request are already FluidComponentSchema instances
        success = pvt_service.create_compositional_model(request.name, request.components)
        if not success:
            logger.error(f"Failed to create compositional model '{request.name}'. It might already exist or component data is invalid.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, # Or 400
                detail=f"Compositional model with name '{request.name}' already exists or component data is invalid."
            )
        return {"status": "success", "model_name": request.name, "model_type": "compositional"}
    except ValueError as ve: # Catch specific errors like sum of mole fractions != 1
        logger.error(f"Validation error creating compositional model '{request.name}': {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.post("/calculate", response_model=api_schemas.PVTResult)
def calculate_pvt_properties_endpoint( # Renamed for clarity
    request: api_schemas.PVTCalculationRequest
):
    """
    Calculate PVT properties for a given model, pressure, and temperature.
    """
    logger.info(f"Calculating PVT properties for model: {request.model_name}, P: {request.pressure}, T: {request.temperature}")
    try:
        result = pvt_service.calculate_pvt_properties(
            request.model_name,
            request.pressure,
            request.temperature
        )
        if result is None:
            # This implies an internal calculation error or flash non-convergence
            logger.error(f"PVT calculation returned None for model '{request.model_name}'. Possible internal error or non-convergence.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not calculate PVT properties for model '{request.model_name}'. Possible non-convergence or internal error."
            )
        return result
    except ValueError as e: # Handles model not found from PVTService
        logger.warning(f"ValueError during PVT calculation for model '{request.model_name}': {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during PVT calculation for model '{request.model_name}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during PVT calculation.")

@router.post("/generate-table", response_model=List[api_schemas.PVTResult])
def generate_pvt_table_endpoint( # Renamed for clarity
    request: api_schemas.PVTTableRequest
):
    """
    Generate a table of PVT properties over a range of pressures at a fixed temperature.
    """
    logger.info(f"Generating PVT table for model: {request.model_name}, T: {request.temperature}, P_range: {request.pressure_range}")
    # Convert tuple pressure_range to a list of pressure points
    # Assuming pressure_range is (start, stop, step)
    try:
        p_start, p_stop, p_step = request.pressure_range
        if p_step <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pressure step must be positive.")
        if p_start > p_stop:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start pressure cannot be greater than stop pressure.")

        # Generate pressure points using numpy.arange for float steps if needed, or simple range
        # Be careful with float steps and exact number of points.
        pressure_points = list(p for p in 상태(p_start, p_stop + p_step / 2, p_step)) # Ensure endpoint is included if step aligns
        if not pressure_points: # Handle case where range is too small for step
            pressure_points = [p_start] if p_start <= p_stop else []


        results = pvt_service.generate_pvt_table(
            request.model_name,
            pressure_points, # Pass the list of pressures
            request.temperature
        )
        if not results and pressure_points: # If points were expected but no results (e.g. all calcs failed)
            logger.warning(f"PVT table generation for '{request.model_name}' yielded no results for given pressures.")
            # Depending on desired behavior, could raise 500 or return empty list.
            # Returning empty list is acceptable if some points might fail calculation.
        return results
    except ValueError as e: # Handles model not found from PVTService
        logger.warning(f"ValueError during PVT table generation for model '{request.model_name}': {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during PVT table generation for model '{request.model_name}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during PVT table generation.")

@router.post("/phase-envelope", response_model=List[api_schemas.PhaseEnvelopePoint])
def generate_phase_envelope_endpoint( # Renamed for clarity
    request: api_schemas.PhaseEnvelopeRequest
):
    """
    Generate phase envelope data points for a compositional PVT model.
    """
    logger.info(f"Generating phase envelope for model: {request.model_name}")
    try:
        # PhaseEnvelopeRequest has Optional fields for range/pressure, service needs to handle defaults if not provided
        envelope = pvt_service.generate_phase_envelope(
            request.model_name,
            num_points_curve=request.temperature_range[2] if request.temperature_range and len(request.temperature_range)==3 else 20, # approx from step
            p_min_psia=14.7, # Example default
            p_max_psia=request.max_pressure if request.max_pressure else 10000
            # The service's generate_phase_envelope should ideally take the T-range tuple directly
        )
        if not envelope:
            logger.warning(f"Phase envelope generation for '{request.model_name}' returned no points.")
            # This could be normal if conditions don't form an envelope, or an error.
        return envelope
    except ValueError as e: # Handles model not found or not compositional from PVTService
        logger.warning(f"ValueError during phase envelope generation for model '{request.model_name}': {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) # Or 400 if model type wrong
    except Exception as e:
        logger.error(f"Unexpected error during phase envelope generation for model '{request.model_name}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during phase envelope generation.")

@router.get("/models", response_model=Dict[str, List[str]])
def list_pvt_models():
    """
    List all available (in-memory) PVT models.
    """
    return pvt_service.list_available_models()

# Helper for generating pressure points for table (could be in a utils file)
# This is a simple range, np.linspace or np.arange might be better for float steps.
def 상태(start, stop, step): # Renamed from range to avoid conflict with built-in
    current = start
    while current <= stop:
        yield current
        current += step
