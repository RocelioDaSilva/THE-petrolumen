from fastapi import APIRouter, HTTPException, Depends, Body
import numpy as np
import logging

# Models from the new reservoir_analysis_models.py
# Imports adjusted for typical project structure
try:
    from ..models.reservoir_analysis_models import (  # Relative import
        OGIPRequest,
        OGIPResponse,
        STOIIPRequest,
        STOIIPResponse,
        BuildupTestAnalysisRequest,
        WellTestAnalysisResponse,
        DrawdownTestAnalysisRequest,
        EURCalculationRequest,
        EURCalculationResponse,
    )

    # Core logic classes from reservoir_engineering.py
    from gaia_genesis.reservoir_engineering import (
        MaterialBalance,
        WellTesting,
        DeclineAnalysis,
    )

    # Auth dependency
    from main import get_current_active_user, UserResponse
except ImportError as e:
    error_message = (
        f"Could not import dependencies for Reservoir Analysis Tools router: {e}."
    )
    logging.error(error_message, exc_info=True)  # Log with exc_info for more details
    raise ImportError(error_message)


router = APIRouter()
logger = logging.getLogger(__name__)  # Initialize logger

# Instantiate tools
mbal_calculator = MaterialBalance()
well_test_analyzer = WellTesting()
dca_tool = DeclineAnalysis()  # For EUR calculation


# --- Material Balance Endpoints ---
@router.post(
    "/material-balance/ogip",
    response_model=OGIPResponse,
    tags=["Reservoir Analysis Tools", "Material Balance"],
)
async def calculate_ogip(
    request_data: OGIPRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Calculates Original Gas In Place (OGIP) using the Havlena-Odeh method.
    Requires historical pressure and cumulative gas production data.
    """
    try:
        pressure_history_np = np.array(request_data.pressure_history)
        production_history_np = np.array(request_data.production_history)

        if (
            len(pressure_history_np) != len(production_history_np)
            or len(pressure_history_np) < 2
        ):
            raise ValueError(
                "Pressure and production history arrays must have the same length "
                "and at least 2 data points."
            )

        ogip = mbal_calculator.calculate_ogip(
            pressure=pressure_history_np,
            production=production_history_np,
            temperature=request_data.temperature,
            gas_specific_gravity=request_data.gas_specific_gravity,
        )
        if ogip is None or np.isnan(ogip) or np.isinf(ogip):
            raise ValueError(
                "OGIP calculation resulted in an invalid value. Check input data and "
                "correlations."
            )
        return OGIPResponse(ogip=ogip)
    except ValueError as ve:
        logger.warning(f"ValueError in OGIP calculation: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error calculating OGIP: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error calculating OGIP: {str(e)}")


@router.post(
    "/material-balance/stoiip",
    response_model=STOIIPResponse,
    tags=["Reservoir Analysis Tools", "Material Balance"],
)
async def calculate_stoiip(
    request_data: STOIIPRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Calculates Original Oil In Place (STOIIP) using the Havlena-Odeh method.
    Requires historical pressure and cumulative oil production data, along with PVT
    properties.
    """
    try:
        pressure_history_np = np.array(request_data.pressure_history)
        production_history_np = np.array(request_data.production_history)

        if (
            len(pressure_history_np) != len(production_history_np)
            or len(pressure_history_np) < 2
        ):
            raise ValueError(
                "Pressure and production history arrays must have the same length "
                "and at least 2 data points."
            )

        stoiip = mbal_calculator.calculate_stoiip(
            pressure=pressure_history_np,
            production=production_history_np,
            temperature=request_data.temperature,
            api_gravity=request_data.api_gravity,
            gas_specific_gravity=request_data.gas_specific_gravity,
        )
        if stoiip is None or np.isnan(stoiip) or np.isinf(stoiip):
            raise ValueError(
                "STOIIP calculation resulted in an invalid value. Check input data "
                "and correlations."
            )
        return STOIIPResponse(stoiip=stoiip)
    except ValueError as ve:
        logger.warning(f"ValueError in STOIIP calculation: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error calculating STOIIP: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error calculating STOIIP: {str(e)}"
        )


# --- Well Testing Endpoints ---
@router.post(
    "/well-testing/analyze-buildup",
    response_model=WellTestAnalysisResponse,
    tags=["Reservoir Analysis Tools", "Well Testing"],
)
async def analyze_buildup_test(
    request_data: BuildupTestAnalysisRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Analyzes pressure buildup test data using Horner plot method.
    """
    try:
        time_data_np = np.array(request_data.time_data)
        pressure_data_np = np.array(request_data.pressure_data)

        if len(time_data_np) != len(pressure_data_np) or len(time_data_np) < 2:
            raise ValueError(
                "Time and pressure data arrays must have the same length and at "
                "least 2 data points."
            )

        results = well_test_analyzer.analyze_buildup(
            time=time_data_np,
            pressure=pressure_data_np,
            rate=request_data.production_rate,
            viscosity=request_data.fluid_viscosity,
            compressibility=request_data.total_compressibility,
            porosity=request_data.formation_porosity,
            wellbore_radius=request_data.wellbore_radius,
        )
        return WellTestAnalysisResponse(**results)
    except ValueError as ve:
        logger.warning(f"ValueError in buildup test analysis: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error analyzing buildup test: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error analyzing buildup test: {str(e)}"
        )


@router.post(
    "/well-testing/analyze-drawdown",
    response_model=WellTestAnalysisResponse,
    tags=["Reservoir Analysis Tools", "Well Testing"],
)
async def analyze_drawdown_test(
    request_data: DrawdownTestAnalysisRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Analyzes pressure drawdown test data using semilog plot method.
    """
    try:
        time_data_np = np.array(request_data.time_data)
        pressure_data_np = np.array(request_data.pressure_data)

        if len(time_data_np) != len(pressure_data_np) or len(time_data_np) < 2:
            raise ValueError(
                "Time and pressure data arrays must have the same length and at "
                "least 2 data points."
            )

        results = well_test_analyzer.analyze_drawdown(
            time=time_data_np,
            pressure=pressure_data_np,
            rate=request_data.production_rate,
            viscosity=request_data.fluid_viscosity,
            compressibility=request_data.total_compressibility,
            porosity=request_data.formation_porosity,
            wellbore_radius=request_data.wellbore_radius,
        )
        return WellTestAnalysisResponse(**results)
    except ValueError as ve:
        logger.warning(f"ValueError in drawdown test analysis: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error analyzing drawdown test: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error analyzing drawdown test: {str(e)}"
        )


# --- EUR Calculation Endpoint ---
@router.post(
    "/decline-curve/calculate-eur",
    response_model=EURCalculationResponse,
    tags=["Reservoir Analysis Tools", "Decline Curve Analysis"],
)
async def calculate_eur_from_dca_params(
    request_data: EURCalculationRequest = Body(...),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Calculates Estimated Ultimate Recovery (EUR) from Arps decline curve parameters.
    The underlying calculation uses a 30-year forecast period by default.
    """
    try:
        dca_params = {
            "qi": request_data.qi,
            "di": request_data.Di,
            "b": request_data.b,
            "method": request_data.method_type,
        }
        if request_data.method_type not in ["exponential", "harmonic", "hyperbolic"]:
            raise ValueError(
                "Invalid method_type. Must be 'exponential', 'harmonic', or "
                "'hyperbolic'."
            )

        eur = dca_tool.calculate_eur(params=dca_params)
        if eur is None or np.isnan(eur) or np.isinf(eur):
            raise ValueError(
                "EUR calculation resulted in an invalid value. Check input parameters."
            )
        return EURCalculationResponse(eur=eur)
    except ValueError as ve:
        logger.warning(f"ValueError in EUR calculation: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error calculating EUR: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error calculating EUR: {str(e)}")
