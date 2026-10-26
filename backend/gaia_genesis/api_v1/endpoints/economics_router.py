from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import numpy as np
import structlog

from auth_utils import get_current_active_user
from ...economics import (
    EconomicsEvaluator,
    EconomicParameters,
    ProductionForecast,
    EconomicSensitivityAnalyzer,
)
from gaia_genesis.reservoir_engineering import DeclineAnalysis

logger = structlog.get_logger(__name__)
router = APIRouter()
dca_tool = DeclineAnalysis()


# Request Models
class ForecastInputModel(BaseModel):
    time: List[float] = Field(..., description="Time period sequence (e.g. months [1, 2, 3...])")
    oil_rate: List[float] = Field(..., description="Oil production rates or volumes")
    gas_rate: Optional[List[float]] = Field(None, description="Gas production rates or volumes")
    water_rate: Optional[List[float]] = Field(None, description="Water production rates or volumes")
    rates_are_daily: bool = Field(False, description="True if rates are daily (STB/d), False if period total volumes")


class EconomicsEvaluateRequest(BaseModel):
    forecast: ForecastInputModel
    capex: float = Field(..., description="Initial Capital Expenditure ($)")
    capex_schedule: Optional[List[float]] = Field(None, description="Optional period-by-period CAPEX schedule")
    oil_price: float = Field(70.0, description="Oil price ($/bbl)")
    gas_price: float = Field(3.0, description="Gas price ($/Mcf)")
    price_escalation_annual: float = Field(0.0, description="Annual price escalation fraction (e.g. 0.02)")
    opex_fixed_monthly: float = Field(1000.0, description="Fixed monthly OPEX ($)")
    opex_var_oil: float = Field(5.0, description="Variable OPEX per bbl oil ($/bbl)")
    opex_var_gas: float = Field(0.5, description="Variable OPEX per Mcf gas ($/Mcf)")
    opex_var_water: float = Field(1.0, description="Variable OPEX per bbl water ($/bbl)")
    royalty_rate: float = Field(0.125, description="Royalty fraction (e.g. 0.125)")
    severance_tax_rate: float = Field(0.05, description="Severance tax fraction (e.g. 0.05)")
    income_tax_rate: float = Field(0.21, description="Income tax fraction (e.g. 0.21)")
    discount_rate: float = Field(0.10, description="Annual discount rate fraction (e.g. 0.10)")
    period_frequency: str = Field("monthly", description="'monthly' or 'annual'")


class SensitivityRequest(BaseModel):
    evaluate_request: EconomicsEvaluateRequest
    sensitivity_type: str = Field("tornado", description="'1d', '2d', or 'tornado'")
    parameter_1d: Optional[str] = Field("oil_price", description="Parameter name for 1D sensitivity")
    percentage_steps_1d: Optional[List[float]] = Field(None, description="Percentage variation steps e.g. [-20, -10, 0, 10, 20]")
    parameter_2d_x: Optional[str] = Field("oil_price", description="X Parameter for 2D matrix")
    steps_2d_x: Optional[List[float]] = Field(None, description="Percentage steps for X parameter")
    parameter_2d_y: Optional[str] = Field("capex", description="Y Parameter for 2D matrix")
    steps_2d_y: Optional[List[float]] = Field(None, description="Percentage steps for Y parameter")
    tornado_parameters: Optional[List[str]] = Field(None, description="List of parameters for tornado diagram")
    tornado_variation_pct: float = Field(20.0, description="Variation percentage for tornado diagram")


class DCAEconomicsRequest(BaseModel):
    dca_params: Dict[str, Any] = Field(..., description="DCA parameters: qi, di, b, method ('exponential'/'hyperbolic'/'harmonic')")
    months_to_forecast: int = Field(60, description="Number of months to forecast")
    capex: float = Field(1000000.0)
    oil_price: float = Field(70.0)
    gas_price: float = Field(3.0)
    opex_fixed_monthly: float = Field(1000.0)
    opex_var_oil: float = Field(5.0)
    discount_rate: float = Field(0.10)
    royalty_rate: float = Field(0.125)
    income_tax_rate: float = Field(0.21)


# Legacy Request Models for backwards compatibility
class LegacyAnalysisRequest(BaseModel):
    forecast: List[Dict[str, Any]]
    oil_price: float
    opex_fixed: float
    opex_var: float
    capex: float
    tax_rate: Optional[float] = 0.2
    discount_rate: Optional[float] = 0.1


class LegacyRunRequest(BaseModel):
    forecast_time: List[float]
    forecast_rate: List[float]
    oil_price: float
    opex_fixed: float
    opex_var: float
    capex: float
    tax_rate: Optional[float] = 0.2
    discount_rate: Optional[float] = 0.1


@router.post("/evaluate", tags=["Gaia - Economics"])
async def evaluate_economics(
    request: EconomicsEvaluateRequest,
    user=Depends(get_current_active_user),
):
    """
    Runs comprehensive period-by-period economic evaluation.
    Calculates Net Present Value (NPV), Internal Rate of Return (IRR), Payout Time,
    Cumulative Cash Flows, and Profitability Index.
    """
    try:
        econ_params = EconomicParameters(
            capex=request.capex,
            capex_schedule=request.capex_schedule,
            oil_price=request.oil_price,
            gas_price=request.gas_price,
            price_escalation_annual=request.price_escalation_annual,
            opex_fixed_monthly=request.opex_fixed_monthly,
            opex_var_oil=request.opex_var_oil,
            opex_var_gas=request.opex_var_gas,
            opex_var_water=request.opex_var_water,
            royalty_rate=request.royalty_rate,
            severance_tax_rate=request.severance_tax_rate,
            income_tax_rate=request.income_tax_rate,
            discount_rate_annual=request.discount_rate,
            period_frequency=request.period_frequency,
        )

        prod_forecast = ProductionForecast(
            time_periods=request.forecast.time,
            oil_rates=request.forecast.oil_rate,
            gas_rates=request.forecast.gas_rate,
            water_rates=request.forecast.water_rate,
            rates_are_daily=request.forecast.rates_are_daily,
        )

        result = EconomicsEvaluator.evaluate(econ_params, prod_forecast)
        return result.to_dict()
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error("Error evaluating economics", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Economic evaluation failed: {str(e)}",
        )


@router.post("/sensitivity", tags=["Gaia - Economics"])
async def run_sensitivity_analysis(
    request: SensitivityRequest,
    user=Depends(get_current_active_user),
):
    """
    Executes 1D, 2D matrix, or Tornado Diagram economic sensitivity analyses.
    """
    try:
        eval_req = request.evaluate_request
        econ_params = EconomicParameters(
            capex=eval_req.capex,
            capex_schedule=eval_req.capex_schedule,
            oil_price=eval_req.oil_price,
            gas_price=eval_req.gas_price,
            price_escalation_annual=eval_req.price_escalation_annual,
            opex_fixed_monthly=eval_req.opex_fixed_monthly,
            opex_var_oil=eval_req.opex_var_oil,
            opex_var_gas=eval_req.opex_var_gas,
            opex_var_water=eval_req.opex_var_water,
            royalty_rate=eval_req.royalty_rate,
            severance_tax_rate=eval_req.severance_tax_rate,
            income_tax_rate=eval_req.income_tax_rate,
            discount_rate_annual=eval_req.discount_rate,
            period_frequency=eval_req.period_frequency,
        )

        prod_forecast = ProductionForecast(
            time_periods=eval_req.forecast.time,
            oil_rates=eval_req.forecast.oil_rate,
            gas_rates=eval_req.forecast.gas_rate,
            water_rates=eval_req.forecast.water_rate,
            rates_are_daily=eval_req.forecast.rates_are_daily,
        )

        stype = request.sensitivity_type.lower()
        if stype == "1d":
            results = EconomicSensitivityAnalyzer.run_1d_sensitivity(
                econ_params,
                prod_forecast,
                parameter_name=request.parameter_1d or "oil_price",
                percentage_steps=request.percentage_steps_1d,
            )
            return {"type": "1d", "parameter": request.parameter_1d, "results": results}

        elif stype == "2d":
            steps_x = request.steps_2d_x or [-20.0, -10.0, 0.0, 10.0, 20.0]
            steps_y = request.steps_2d_y or [-20.0, -10.0, 0.0, 10.0, 20.0]
            matrix_res = EconomicSensitivityAnalyzer.run_2d_sensitivity(
                econ_params,
                prod_forecast,
                param_x=request.parameter_2d_x or "oil_price",
                steps_x=steps_x,
                param_y=request.parameter_2d_y or "capex",
                steps_y=steps_y,
            )
            return {"type": "2d", "matrix": matrix_res}

        else:  # "tornado"
            tornado_data = EconomicSensitivityAnalyzer.generate_tornado_data(
                econ_params,
                prod_forecast,
                parameters_to_test=request.tornado_parameters,
                variation_pct=request.tornado_variation_pct,
            )
            return {"type": "tornado", "tornado_data": tornado_data}

    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error("Error running economic sensitivity", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sensitivity analysis failed: {str(e)}",
        )


@router.post("/dca-economics", tags=["Gaia - Economics"])
async def run_dca_economics(
    request: DCAEconomicsRequest,
    user=Depends(get_current_active_user),
):
    """
    Generates production profile forecast directly from DCA Arps parameters and performs economic evaluation.
    """
    try:
        time_months = np.arange(1, request.months_to_forecast + 1, dtype=float)
        dca_dict = {
            "qi": float(request.dca_params.get("qi", 1000.0)),
            "di": float(request.dca_params.get("di", 0.05)),
            "b": float(request.dca_params.get("b", 0.5)),
            "method": str(request.dca_params.get("method", "hyperbolic")),
        }

        forecast_rates = dca_tool.forecast_production(dca_dict, time_months)

        econ_params = EconomicParameters(
            capex=request.capex,
            oil_price=request.oil_price,
            gas_price=request.gas_price,
            opex_fixed_monthly=request.opex_fixed_monthly,
            opex_var_oil=request.opex_var_oil,
            royalty_rate=request.royalty_rate,
            income_tax_rate=request.income_tax_rate,
            discount_rate_annual=request.discount_rate,
            period_frequency="monthly",
        )

        prod_forecast = ProductionForecast(
            time_periods=time_months.tolist(),
            oil_rates=forecast_rates.tolist(),
            rates_are_daily=True,
        )

        res = EconomicsEvaluator.evaluate(econ_params, prod_forecast)
        return res.to_dict()

    except Exception as e:
        logger.error("Error running DCA economics", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"DCA economic evaluation failed: {str(e)}",
        )


# Legacy endpoints for backwards compatibility
@router.post("/analysis")
async def calculate_economics_legacy(
    data: LegacyAnalysisRequest, user=Depends(get_current_active_user)
):
    try:
        times = [float(entry.get("time", idx + 1)) for idx, entry in enumerate(data.forecast)]
        rates = [float(entry.get("rate", 0.0)) for entry in data.forecast]

        econ_params = EconomicParameters(
            capex=data.capex,
            oil_price=data.oil_price,
            opex_fixed_monthly=data.opex_fixed,
            opex_var_oil=data.opex_var,
            income_tax_rate=data.tax_rate or 0.2,
            discount_rate_annual=data.discount_rate or 0.1,
            period_frequency="monthly",
        )

        prod_forecast = ProductionForecast(
            time_periods=times,
            oil_rates=rates,
            rates_are_daily=True,
        )

        res = EconomicsEvaluator.evaluate(econ_params, prod_forecast)
        return {
            "npv": res.npv,
            "irr": res.irr,
            "payout_month": int(res.payout_months) if res.payout_months >= 0 else -1,
            "cash_flow_table": [p.net_cash_flow for p in res.cash_flow_periods],
            "cumulative_cash_flow": [p.cumulative_net_cash_flow for p in res.cash_flow_periods],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/run")
async def run_economics_test_legacy(
    data: LegacyRunRequest, user=Depends(get_current_active_user)
):
    try:
        econ_params = EconomicParameters(
            capex=data.capex,
            oil_price=data.oil_price,
            opex_fixed_monthly=data.opex_fixed,
            opex_var_oil=data.opex_var,
            income_tax_rate=data.tax_rate or 0.2,
            discount_rate_annual=data.discount_rate or 0.1,
            period_frequency="monthly",
        )

        prod_forecast = ProductionForecast(
            time_periods=data.forecast_time,
            oil_rates=data.forecast_rate,
            rates_are_daily=True,
        )

        res = EconomicsEvaluator.evaluate(econ_params, prod_forecast)
        return {
            "npv": res.npv,
            "irr": res.irr,
            "payout_month": int(res.payout_months) if res.payout_months >= 0 else -1,
            "cash_flow_table": [p.net_cash_flow for p in res.cash_flow_periods],
            "cumulative_cash_flow": [p.cumulative_net_cash_flow for p in res.cash_flow_periods],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
