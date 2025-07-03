from fastapi import APIRouter, HTTPException, Body, Depends # Added Depends
from typing import Optional

# Assuming pvt_models.py is in ../models/ relative to this file
# Adjust if the gaia_genesis structure means it's directly importable
# For now, assuming direct import from the new structure if PYTHONPATH is set up
# This will likely need adjustment based on actual file structure and Python path
try:
    from backend.gaia_genesis.api_v1.models.pvt_models import (
        ZFactorRequest, ZFactorResponse,
        FormationVolumeFactorRequest, FormationVolumeFactorResponse,
        ViscosityRequest, ViscosityResponse,
        SolutionGasRatioRequest, SolutionGasRatioResponse
    )
    from backend.gaia_genesis.reservoir_engineering import PVTProperties
    # Import authentication dependencies from backend.main
    # This creates a slight coupling but is necessary if get_current_active_user is defined in main.py
    # Ideally, auth utilities would be in their own module.
    from backend.main import get_current_active_user, UserResponse
except ImportError as e: # Catch specific error
    # Fallback for local testing if paths are different, or if structure isn't a package yet
    # This is a common issue when developing modules that are part of a larger app
    # For the agent's environment, the full path import should work if backend is in sys.path
    error_message = f"Could not import dependencies for PVT calculations router: {e}. Check PYTHONPATH and file structure. Ensure backend.main defines get_current_active_user and UserResponse."
    print(error_message) # Print to console for debugging
    raise ImportError(error_message)


router = APIRouter()

pvt_calculator = PVTProperties()

@router.post("/calculate_z_factor", response_model=ZFactorResponse)
async def calculate_z_factor_endpoint(
    request_data: ZFactorRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user) # Added authentication
):
    """
    Calculates the Gas Compressibility Factor (Z-Factor). Requires authentication.
    - **pressure**: Pressure in psia
    - **temperature**: Temperature in Fahrenheit (°F)
    - **gas_specific_gravity**: Specific gravity of the gas (e.g., 0.65 for typical natural gas)
    """
    try:
        # The PVTProperties.calculate_z_factor method expects temperature in °F
        # and internally converts to Rankine.
        z = pvt_calculator.calculate_z_factor(
            pressure=request_data.pressure,
            temperature=request_data.temperature, # Assuming this is in °F as per PVTProperties
            gas_specific_gravity=request_data.gas_specific_gravity
        )
        return ZFactorResponse(z_factor=z)
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=500, detail=f"Error calculating Z-Factor: {str(e)}")

@router.post("/calculate_formation_volume_factor", response_model=FormationVolumeFactorResponse)
async def calculate_fvf_endpoint(
    request_data: FormationVolumeFactorRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user) # Added authentication
):
    """
    Calculates the Formation Volume Factor (FVF) for oil (Bo) or gas (Bg). Requires authentication.
    - **pressure**: Pressure in psia
    - **temperature**: Temperature in Fahrenheit (°F)
    - **fluid_type**: 'oil' or 'gas'
    - **api_gravity**: API gravity of the oil (required if fluid_type is 'oil')
    - **gas_specific_gravity**: Specific gravity of the gas (required for both oil and gas calculations)
    """
    if request_data.fluid_type == 'oil' and request_data.api_gravity is None:
        raise HTTPException(status_code=400, detail="api_gravity is required for fluid_type 'oil'")
    if request_data.gas_specific_gravity is None:
         raise HTTPException(status_code=400, detail="gas_specific_gravity is required")

    try:
        fvf = pvt_calculator.calculate_formation_volume_factor(
            pressure=request_data.pressure,
            temperature=request_data.temperature, # Expects °F
            fluid_type=request_data.fluid_type,
            api_gravity=request_data.api_gravity,
            gas_specific_gravity=request_data.gas_specific_gravity
        )
        return FormationVolumeFactorResponse(fvf=fvf)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating FVF: {str(e)}")

@router.post("/calculate_viscosity", response_model=ViscosityResponse)
async def calculate_viscosity_endpoint(
    request_data: ViscosityRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user) # Added authentication
):
    """
    Calculates fluid viscosity for oil or gas. Requires authentication.
    - **pressure**: Pressure in psia
    - **temperature**: Temperature in Fahrenheit (°F)
    - **fluid_type**: 'oil' or 'gas'
    - **api_gravity**: API gravity of the oil (required if fluid_type is 'oil')
    - **gas_specific_gravity**: Specific gravity of the gas (required for both 'oil' and 'gas')
    """
    if request_data.fluid_type == 'oil' and request_data.api_gravity is None:
        raise HTTPException(status_code=400, detail="api_gravity is required for fluid_type 'oil'")
    if request_data.gas_specific_gravity is None:
        raise HTTPException(status_code=400, detail="gas_specific_gravity is required")

    try:
        viscosity = pvt_calculator.calculate_viscosity(
            pressure=request_data.pressure,
            temperature=request_data.temperature, # Expects °F
            fluid_type=request_data.fluid_type,
            api_gravity=request_data.api_gravity,
            gas_specific_gravity=request_data.gas_specific_gravity
        )
        return ViscosityResponse(viscosity=viscosity)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating viscosity: {str(e)}")

@router.post("/calculate_solution_gas_ratio", response_model=SolutionGasRatioResponse)
async def calculate_rs_endpoint(
    request_data: SolutionGasRatioRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user) # Added authentication
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
            temperature=request_data.temperature, # Expects °F
            api_gravity=request_data.api_gravity,
            gas_specific_gravity=request_data.gas_specific_gravity
        )
        return SolutionGasRatioResponse(rs=rs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating Solution Gas-Oil Ratio: {str(e)}")
