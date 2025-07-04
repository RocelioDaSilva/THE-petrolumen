from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List
import numpy as np
import pandas as pd # Though not directly used, good to have if inputs become more complex

# Models from the new reservoir_analysis_models.py
from backend.gaia_genesis.api_v1.models.reservoir_analysis_models import (
    OGIPRequest, OGIPResponse,
    STOIIPRequest, STOIIPResponse,
    BuildupTestAnalysisRequest, WellTestAnalysisResponse, # Re-using WellTestAnalysisResponse for Drawdown
    DrawdownTestAnalysisRequest,
    EURCalculationRequest, EURCalculationResponse
)

# Core logic classes from reservoir_engineering.py
from backend.gaia_genesis.reservoir_engineering import MaterialBalance, WellTesting, DeclineAnalysis

# Auth dependency
from backend.main import get_current_active_user, UserResponse # Assuming UserResponse is the model for current_user

router = APIRouter()

# Instantiate tools
mbal_calculator = MaterialBalance()
well_test_analyzer = WellTesting()
dca_tool = DeclineAnalysis() # For EUR calculation

# --- Material Balance Endpoints ---
@router.post("/material-balance/ogip", response_model=OGIPResponse, tags=["Reservoir Analysis Tools", "Material Balance"])
async def calculate_ogip(
    request_data: OGIPRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Calculates Original Gas In Place (OGIP) using the Havlena-Odeh method.
    Requires historical pressure and cumulative gas production data.
    """
    try:
        # Convert lists to numpy arrays as expected by the MaterialBalance class
        pressure_history_np = np.array(request_data.pressure_history)
        production_history_np = np.array(request_data.production_history)

        if len(pressure_history_np) != len(production_history_np) or len(pressure_history_np) < 2:
            raise ValueError("Pressure and production history arrays must have the same length and at least 2 data points.")

        ogip = mbal_calculator.calculate_ogip(
            pressure=pressure_history_np,
            production=production_history_np,
            temperature=request_data.temperature,
            gas_specific_gravity=request_data.gas_specific_gravity
        )
        if ogip is None or np.isnan(ogip) or np.isinf(ogip):
            raise ValueError("OGIP calculation resulted in an invalid value. Check input data and correlations.")
        return OGIPResponse(ogip=ogip)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=500, detail=f"Error calculating OGIP: {str(e)}")

@router.post("/material-balance/stoiip", response_model=STOIIPResponse, tags=["Reservoir Analysis Tools", "Material Balance"])
async def calculate_stoiip(
    request_data: STOIIPRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Calculates Original Oil In Place (STOIIP) using the Havlena-Odeh method.
    Requires historical pressure and cumulative oil production data, along with PVT properties.
    Note: The underlying `MaterialBalance.calculate_stoiip` method might require additional parameters
    (like initial Bo, Rs, Bg, Bw, compressibilities) which are not fully exposed in this simplified request.
    This endpoint may need refinement based on how these are handled by the core class.
    """
    try:
        pressure_history_np = np.array(request_data.pressure_history)
        production_history_np = np.array(request_data.production_history)

        if len(pressure_history_np) != len(production_history_np) or len(pressure_history_np) < 2:
            raise ValueError("Pressure and production history arrays must have the same length and at least 2 data points.")

        # The MaterialBalance class's calculate_stoiip might need more parameters for rock_properties
        # For now, we pass what's available in the request. This might be insufficient.
        # A more robust implementation might require a rock_properties dict in the request,
        # or the MaterialBalance class needs to handle missing ones with defaults/internal calculations.

        # Placeholder for rock_properties that might be needed by the core function
        # These should ideally come from the request or be fetched/calculated.
        mock_rock_properties = {
            'Bo_initial': request_data.bo_initial if request_data.bo_initial is not None else 1.2, # Example default
            'Rs_initial': request_data.rs_initial if request_data.rs_initial is not None else 500, # Example default
            'Bg_initial': 0.005, # Example default, ideally derived
            'Bw_initial': 1.0,   # Example default
            'cw': 3e-6,          # Example default
            'cf': 4e-6           # Example default
        }


        stoiip = mbal_calculator.calculate_stoiip(
            pressure=pressure_history_np,
            production=production_history_np,
            temperature=request_data.temperature,
            api_gravity=request_data.api_gravity,
            gas_specific_gravity=request_data.gas_specific_gravity
            # The current calculate_stoiip in reservoir_engineering.py does not take rock_properties
            # It re-calculates PVT internally. This might need alignment.
        )
        if stoiip is None or np.isnan(stoiip) or np.isinf(stoiip):
            raise ValueError("STOIIP calculation resulted in an invalid value. Check input data and correlations.")
        return STOIIPResponse(stoiip=stoiip)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating STOIIP: {str(e)}")

# --- Well Testing Endpoints ---
@router.post("/well-testing/analyze-buildup", response_model=WellTestAnalysisResponse, tags=["Reservoir Analysis Tools", "Well Testing"])
async def analyze_buildup_test(
    request_data: BuildupTestAnalysisRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Analyzes pressure buildup test data using Horner plot method.
    """
    try:
        time_data_np = np.array(request_data.time_data)
        pressure_data_np = np.array(request_data.pressure_data)

        if len(time_data_np) != len(pressure_data_np) or len(time_data_np) < 2:
            raise ValueError("Time and pressure data arrays must have the same length and at least 2 data points.")

        results = well_test_analyzer.analyze_buildup(
            time=time_data_np,
            pressure=pressure_data_np,
            rate=request_data.production_rate,
            viscosity=request_data.fluid_viscosity,
            compressibility=request_data.total_compressibility,
            porosity=request_data.formation_porosity,
            wellbore_radius=request_data.wellbore_radius
            # formation_thickness is not used by the current analyze_buildup,
            # so permeability result is effectively k (absolute permeability).
        )
        return WellTestAnalysisResponse(**results)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing buildup test: {str(e)}")

@router.post("/well-testing/analyze-drawdown", response_model=WellTestAnalysisResponse, tags=["Reservoir Analysis Tools", "Well Testing"])
async def analyze_drawdown_test(
    request_data: DrawdownTestAnalysisRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Analyzes pressure drawdown test data using semilog plot method.
    """
    try:
        time_data_np = np.array(request_data.time_data)
        pressure_data_np = np.array(request_data.pressure_data)

        if len(time_data_np) != len(pressure_data_np) or len(time_data_np) < 2:
            raise ValueError("Time and pressure data arrays must have the same length and at least 2 data points.")

        results = well_test_analyzer.analyze_drawdown(
            time=time_data_np,
            pressure=pressure_data_np,
            rate=request_data.production_rate,
            viscosity=request_data.fluid_viscosity,
            compressibility=request_data.total_compressibility,
            porosity=request_data.formation_porosity,
            wellbore_radius=request_data.wellbore_radius
            # formation_thickness is not used by the current analyze_drawdown
        )
        return WellTestAnalysisResponse(**results)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing drawdown test: {str(e)}")

# --- EUR Calculation Endpoint ---
@router.post("/decline-curve/calculate-eur", response_model=EURCalculationResponse, tags=["Reservoir Analysis Tools", "Decline Curve Analysis"])
async def calculate_eur_from_dca_params(
    request_data: EURCalculationRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Calculates Estimated Ultimate Recovery (EUR) from Arps decline curve parameters.
    The underlying calculation uses a 30-year forecast period by default.
    """
    try:
        # The DeclineAnalysis class needs parameters in a specific dict format
        dca_params = {
            'qi': request_data.qi,
            'di': request_data.Di,
            'b': request_data.b,
            'method': request_data.method_type # Ensure this matches 'exponential', 'harmonic', 'hyperbolic'
        }
        if request_data.method_type not in ['exponential', 'harmonic', 'hyperbolic']:
            raise ValueError("Invalid method_type. Must be 'exponential', 'harmonic', or 'hyperbolic'.")

        eur = dca_tool.calculate_eur(params=dca_params)
        if eur is None or np.isnan(eur) or np.isinf(eur):
            raise ValueError("EUR calculation resulted in an invalid value. Check input parameters.")
        return EURCalculationResponse(eur=eur)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating EUR: {str(e)}")
