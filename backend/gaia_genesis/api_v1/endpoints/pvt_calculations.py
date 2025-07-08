from fastapi import APIRouter, HTTPException, Body, Depends
import logging

# Imports adjusted for typical project structure where 'backend/' is in PYTHONPATH
# or when running tests from 'backend/' directory.
try:
    # Relative import for models within the same 'api_v1' structure
    from ..models.pvt_models import (
        ZFactorRequest,
        ZFactorResponse,
        FormationVolumeFactorRequest,
        FormationVolumeFactorResponse,
        ViscosityRequest,
        ViscosityResponse,
        SolutionGasRatioRequest,
        SolutionGasRatioResponse,
    )

    # Import from other modules within the 'gaia_genesis' package or top-level 'backend'
    from gaia_genesis.reservoir_engineering import PVTProperties
    from main import (
        get_current_active_user,
        UserResponse,
    )  # Assuming main.py is in backend/
except ImportError as e:
    # Using f-string for better readability and direct variable insertion
    error_message = (
        f"Could not import dependencies for PVT calculations router: {e}. "
        "Check PYTHONPATH and file structure. Ensure main.py defines "
        "get_current_active_user and UserResponse, and "
        "gaia_genesis.reservoir_engineering.PVTProperties is accessible."
    )
    logging.error(error_message)  # Use logging
    raise ImportError(error_message)


router = APIRouter()
logger = logging.getLogger(__name__)  # Initialize logger for this module

pvt_calculator = PVTProperties()


@router.post("/calculate_z_factor", response_model=ZFactorResponse)
async def calculate_z_factor_endpoint(
    request_data: ZFactorRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Calculates the Gas Compressibility Factor (Z-Factor). Requires authentication.
    - **pressure**: Pressure in psia
    - **temperature**: Temperature in Fahrenheit (°F)
    - **gas_specific_gravity**: Specific gravity of the gas (e.g., 0.65 for typical
      natural gas)
    """
    try:
        z = pvt_calculator.calculate_z_factor(
            pressure=request_data.pressure,
            temperature=request_data.temperature,
            gas_specific_gravity=request_data.gas_specific_gravity,
        )
        return ZFactorResponse(z_factor=z)
    except Exception as e:
        logger.error(f"Error in /calculate_z_factor: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error calculating Z-Factor: {str(e)}"
        )


@router.post(
    "/calculate_formation_volume_factor", response_model=FormationVolumeFactorResponse
)
async def calculate_fvf_endpoint(
    request_data: FormationVolumeFactorRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Calculates the Formation Volume Factor (FVF) for oil (Bo) or gas (Bg).
    Requires authentication.
    - **pressure**: Pressure in psia
    - **temperature**: Temperature in Fahrenheit (°F)
    - **fluid_type**: 'oil' or 'gas'
    - **api_gravity**: API gravity of the oil (required if fluid_type is 'oil')
    - **gas_specific_gravity**: Specific gravity of the gas (required for both oil
      and gas calculations)
    """
    if request_data.fluid_type == "oil" and request_data.api_gravity is None:
        raise HTTPException(
            status_code=400, detail="api_gravity is required for fluid_type 'oil'"
        )
    if request_data.gas_specific_gravity is None:
        raise HTTPException(status_code=400, detail="gas_specific_gravity is required")

    try:
        fvf = pvt_calculator.calculate_formation_volume_factor(
            pressure=request_data.pressure,
            temperature=request_data.temperature,
            fluid_type=request_data.fluid_type,
            api_gravity=request_data.api_gravity,
            gas_specific_gravity=request_data.gas_specific_gravity,
        )
        return FormationVolumeFactorResponse(fvf=fvf)
    except Exception as e:
        logger.error(f"Error in /calculate_formation_volume_factor: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error calculating FVF: {str(e)}")


@router.post("/calculate_viscosity", response_model=ViscosityResponse)
async def calculate_viscosity_endpoint(
    request_data: ViscosityRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Calculates fluid viscosity for oil or gas. Requires authentication.
    - **pressure**: Pressure in psia
    - **temperature**: Temperature in Fahrenheit (°F)
    - **fluid_type**: 'oil' or 'gas'
    - **api_gravity**: API gravity of the oil (required if fluid_type is 'oil')
    - **gas_specific_gravity**: Specific gravity of the gas (required for both 'oil'
      and 'gas')
    """
    if request_data.fluid_type == "oil" and request_data.api_gravity is None:
        raise HTTPException(
            status_code=400, detail="api_gravity is required for fluid_type 'oil'"
        )
    if request_data.gas_specific_gravity is None:
        raise HTTPException(status_code=400, detail="gas_specific_gravity is required")

    try:
        viscosity = pvt_calculator.calculate_viscosity(
            pressure=request_data.pressure,
            temperature=request_data.temperature,
            fluid_type=request_data.fluid_type,
            api_gravity=request_data.api_gravity,
            gas_specific_gravity=request_data.gas_specific_gravity,
        )
        return ViscosityResponse(viscosity=viscosity)
    except Exception as e:
        logger.error(f"Error in /calculate_viscosity: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error calculating viscosity: {str(e)}"
        )


@router.post("/calculate_solution_gas_ratio", response_model=SolutionGasRatioResponse)
async def calculate_rs_endpoint(
    request_data: SolutionGasRatioRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Calculates the Solution Gas-Oil Ratio (Rs). Requires authentication.
    - **pressure**: Pressure in psia
    - **temperature**: Temperature in Fahrenheit (°F)
    - **api_gravity**: API gravity of the oil
    - **gas_specific_gravity**: Specific gravity of the gas
    """
    try:
        rs = pvt_calculator.calculate_solution_gas_ratio(
            pressure=request_data.pressure,
            temperature=request_data.temperature,
            api_gravity=request_data.api_gravity,
            gas_specific_gravity=request_data.gas_specific_gravity,
        )
        return SolutionGasRatioResponse(rs=rs)
    except Exception as e:
        logger.error(f"Error in /calculate_solution_gas_ratio: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating Solution Gas-Oil Ratio: {str(e)}",
        )
