import copy
from typing import List, Dict, Any, Optional
import structlog

from .evaluator import (
    EconomicsEvaluator,
    EconomicParameters,
    ProductionForecast,
    EconomicResult,
)

logger = structlog.get_logger(__name__)


class EconomicSensitivityAnalyzer:
    """
    Sensitivity Analysis module for economic evaluations in PetroLúmen.
    Provides 1D variation, 2D matrix grids, and Tornado diagram data.
    """

    PARAM_DISPLAY_NAMES = {
        "oil_price": "Oil Price ($/bbl)",
        "gas_price": "Gas Price ($/Mcf)",
        "capex": "CAPEX ($)",
        "opex_var_oil": "Variable OPEX ($/bbl)",
        "opex_fixed_monthly": "Fixed OPEX ($/mo)",
        "discount_rate_annual": "Discount Rate (%)",
        "royalty_rate": "Royalty Rate (%)",
    }

    @classmethod
    def run_1d_sensitivity(
        cls,
        base_params: EconomicParameters,
        forecast: ProductionForecast,
        parameter_name: str,
        percentage_steps: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Varies a single parameter by percentage steps (e.g., [-30, -20, -10, 0, 10, 20, 30])
        and returns resulting economic metrics (NPV, IRR, Payout, ROI).
        """
        if percentage_steps is None:
            percentage_steps = [-30.0, -20.0, -10.0, 0.0, 10.0, 20.0, 30.0]

        if not hasattr(base_params, parameter_name):
            raise ValueError(f"Invalid economic parameter name: '{parameter_name}'")

        base_value = getattr(base_params, parameter_name)
        results = []

        for pct in percentage_steps:
            mod_params = copy.deepcopy(base_params)
            new_val = base_value * (1.0 + pct / 100.0)
            setattr(mod_params, parameter_name, new_val)

            res: EconomicResult = EconomicsEvaluator.evaluate(mod_params, forecast)

            results.append({
                "percentage_change": pct,
                "parameter_value": new_val,
                "npv": res.npv,
                "irr": res.irr,
                "payout_months": res.payout_months,
                "roi": res.return_on_investment,
            })

        return results

    @classmethod
    def run_2d_sensitivity(
        cls,
        base_params: EconomicParameters,
        forecast: ProductionForecast,
        param_x: str,
        steps_x: List[float],
        param_y: str,
        steps_y: List[float],
    ) -> Dict[str, Any]:
        """
        Runs a 2D matrix grid sensitivity varying two parameters (e.g. Oil Price vs CAPEX).
        Returns matrix data suitable for heatmap visualization.
        """
        if not hasattr(base_params, param_x) or not hasattr(base_params, param_y):
            raise ValueError(f"Invalid parameters for 2D sensitivity: {param_x}, {param_y}")

        base_x = getattr(base_params, param_x)
        base_y = getattr(base_params, param_y)

        matrix_npv = []
        matrix_irr = []

        for pct_y in steps_y:
            row_npv = []
            row_irr = []
            for pct_x in steps_x:
                mod_params = copy.deepcopy(base_params)
                setattr(mod_params, param_x, base_x * (1.0 + pct_x / 100.0))
                setattr(mod_params, param_y, base_y * (1.0 + pct_y / 100.0))

                res = EconomicsEvaluator.evaluate(mod_params, forecast)
                row_npv.append(res.npv)
                row_irr.append(res.irr)

            matrix_npv.append(row_npv)
            matrix_irr.append(row_irr)

        return {
            "param_x": param_x,
            "param_x_label": cls.PARAM_DISPLAY_NAMES.get(param_x, param_x),
            "steps_x": steps_x,
            "param_y": param_y,
            "param_y_label": cls.PARAM_DISPLAY_NAMES.get(param_y, param_y),
            "steps_y": steps_y,
            "matrix_npv": matrix_npv,
            "matrix_irr": matrix_irr,
        }

    @classmethod
    def generate_tornado_data(
        cls,
        base_params: EconomicParameters,
        forecast: ProductionForecast,
        parameters_to_test: Optional[List[str]] = None,
        variation_pct: float = 20.0,
    ) -> List[Dict[str, Any]]:
        """
        Generates data for a Tornado Diagram evaluating NPV impact of +/- variation_pct.
        """
        if parameters_to_test is None:
            parameters_to_test = ["oil_price", "capex", "opex_var_oil", "discount_rate_annual"]

        base_res = EconomicsEvaluator.evaluate(base_params, forecast)
        base_npv = base_res.npv

        tornado_items = []

        for param in parameters_to_test:
            if not hasattr(base_params, param):
                continue

            base_val = getattr(base_params, param)

            # High (+variation_pct)
            params_high = copy.deepcopy(base_params)
            setattr(params_high, param, base_val * (1.0 + variation_pct / 100.0))
            res_high = EconomicsEvaluator.evaluate(params_high, forecast)

            # Low (-variation_pct)
            params_low = copy.deepcopy(base_params)
            setattr(params_low, param, base_val * (1.0 - variation_pct / 100.0))
            res_low = EconomicsEvaluator.evaluate(params_low, forecast)

            low_npv = res_low.npv
            high_npv = res_high.npv
            swing = abs(high_npv - low_npv)

            tornado_items.append({
                "parameter": param,
                "label": cls.PARAM_DISPLAY_NAMES.get(param, param),
                "base_npv": base_npv,
                "low_npv": low_npv,
                "high_npv": high_npv,
                "swing": swing,
                "low_pct": -variation_pct,
                "high_pct": variation_pct,
            })

        # Sort descending by NPV swing width
        tornado_items.sort(key=lambda x: x["swing"], reverse=True)
        return tornado_items
