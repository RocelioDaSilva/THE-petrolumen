"""Annual production economics with explicit cash-flow timing and tax handling."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

import numpy as np


class EconomicAnalysis:
    """Evaluate annual oil, gas, and water production economics.

    Production inputs are annual volumes (bbl/year for oil and water, Mscf/year
    for gas), not daily rates. CAPEX is treated as an initial year-zero
    investment; each OPEX entry is an annual cost. Water disposal cost is
    applied per barrel of produced water.
    """

    def __init__(self) -> None:
        self.economic_parameters: dict[str, Any] | None = None
        self.cash_flow: dict[str, Any] | None = None
        self._production_data: dict[str, np.ndarray] | None = None

    @staticmethod
    def _validate_scalar_parameters(parameters: Mapping[str, Any]) -> None:
        names = (
            "oil_price",
            "gas_price",
            "discount_rate",
            "tax_rate",
            "water_disposal_cost_per_bbl",
        )
        if not all(np.isfinite(parameters[name]) for name in names):
            raise ValueError("Economic parameters must all be finite.")
        if parameters["oil_price"] < 0 or parameters["gas_price"] < 0:
            raise ValueError("Oil and gas prices must be non-negative.")
        if parameters["discount_rate"] <= -100:
            raise ValueError("Discount rate must be greater than -100 percent.")
        if not 0 <= parameters["tax_rate"] <= 1:
            raise ValueError("tax rate must be a fraction between 0 and 1.")
        if parameters["water_disposal_cost_per_bbl"] < 0:
            raise ValueError("Water disposal cost must be non-negative.")

    @staticmethod
    def _finite_nonnegative_mapping(
        values: Mapping[str, float], name: str
    ) -> dict[str, float]:
        if not isinstance(values, Mapping):
            raise ValueError(f"{name} must be a mapping of names to finite costs.")
        normalized: dict[str, float] = {}
        for key, value in values.items():
            number = float(value)
            if not np.isfinite(number) or number < 0:
                raise ValueError(f"{name}[{key!r}] must be finite and non-negative.")
            normalized[str(key)] = number
        return normalized

    def set_economic_parameters(
        self,
        oil_price: float,
        gas_price: float,
        discount_rate: float,
        project_life: int,
        capex: Mapping[str, float],
        opex: Mapping[str, float],
        tax_rate: float = 0.34,
        water_disposal_cost_per_bbl: float = 0.0,
    ) -> None:
        """Set prices, annual project horizon, costs, and fractional tax rate."""
        scalars = {
            "oil_price": oil_price,
            "gas_price": gas_price,
            "discount_rate": discount_rate,
            "tax_rate": tax_rate,
            "water_disposal_cost_per_bbl": water_disposal_cost_per_bbl,
        }
        normalized = {name: float(value) for name, value in scalars.items()}
        self._validate_scalar_parameters(normalized)
        if (
            isinstance(project_life, bool)
            or not isinstance(project_life, int)
            or project_life <= 0
        ):
            raise ValueError("Project life must be a positive integer number of years.")

        self.economic_parameters = {
            **normalized,
            "project_life": project_life,
            "capex": self._finite_nonnegative_mapping(capex, "capex"),
            "opex": self._finite_nonnegative_mapping(opex, "opex"),
        }
        self.cash_flow = None
        self._production_data = None

    @staticmethod
    def _annual_volumes(values: Sequence[float], name: str, life: int) -> np.ndarray:
        annual = np.asarray(values, dtype=float)
        if annual.ndim != 1 or annual.size != life:
            raise ValueError(f"{name} must contain one annual volume for each project year.")
        if not np.all(np.isfinite(annual)) or np.any(annual < 0):
            raise ValueError(f"{name} volumes must be finite and non-negative.")
        return annual

    @staticmethod
    def _require_parameters(parameters: dict[str, Any] | None) -> dict[str, Any]:
        if parameters is None:
            raise ValueError("Economic parameters have not been set.")
        return parameters

    @staticmethod
    def _build_cash_flow(
        parameters: Mapping[str, Any], production: Mapping[str, np.ndarray]
    ) -> dict[str, Any]:
        life = int(parameters["project_life"])
        oil_revenue = production["oil"] * parameters["oil_price"]
        gas_revenue = production["gas"] * parameters["gas_price"]
        water_disposal_cost = (
            production["water"] * parameters["water_disposal_cost_per_bbl"]
        )
        total_revenue = oil_revenue + gas_revenue
        annual_opex = float(sum(parameters["opex"].values()))
        total_capex = float(sum(parameters["capex"].values()))
        depreciation = np.full(life, total_capex / life, dtype=float)

        ebitda = total_revenue - annual_opex - water_disposal_cost
        ebit = ebitda - depreciation
        taxes = np.maximum(ebit, 0.0) * parameters["tax_rate"]
        net_income = ebit - taxes
        operating_cash_flow = net_income + depreciation
        project_cash_flow = np.concatenate(([-total_capex], operating_cash_flow))

        return {
            "revenue": {
                "oil": oil_revenue,
                "gas": gas_revenue,
                "total": total_revenue,
            },
            "costs": {
                "opex": np.full(life, annual_opex, dtype=float),
                "water_disposal": water_disposal_cost,
                "total": np.full(life, annual_opex, dtype=float)
                + water_disposal_cost,
                "initial_capex": total_capex,
            },
            "depreciation": depreciation,
            "ebitda": ebitda,
            "ebit": ebit,
            "taxes": taxes,
            "net_income": net_income,
            "operating_cash_flow": operating_cash_flow,
            "cash_flow": project_cash_flow,
        }

    def calculate_cash_flow(
        self,
        oil_production: Sequence[float],
        gas_production: Sequence[float],
        water_production: Sequence[float],
    ) -> dict[str, Any]:
        """Build annual cash flows, including initial CAPEX at year zero."""
        parameters = self._require_parameters(self.economic_parameters)
        life = int(parameters["project_life"])
        production = {
            "oil": self._annual_volumes(oil_production, "oil_production", life),
            "gas": self._annual_volumes(gas_production, "gas_production", life),
            "water": self._annual_volumes(water_production, "water_production", life),
        }
        result = self._build_cash_flow(parameters, production)
        self._production_data = production
        self.cash_flow = result
        return result

    @staticmethod
    def _npv(cash_flows: np.ndarray, discount_rate: float) -> float:
        rate = discount_rate / 100.0
        years = np.arange(cash_flows.size, dtype=float)
        return float(np.sum(cash_flows / np.power(1.0 + rate, years)))

    def _require_cash_flow(self) -> tuple[dict[str, Any], dict[str, Any]]:
        parameters = self._require_parameters(self.economic_parameters)
        if self.cash_flow is None:
            raise ValueError("Calculate cash flow before requesting project metrics.")
        return parameters, self.cash_flow

    def calculate_npv(self) -> float:
        """Calculate NPV, discounting the year-zero investment at time zero."""
        parameters, cash_flow = self._require_cash_flow()
        return self._npv(cash_flow["cash_flow"], parameters["discount_rate"])

    def calculate_irr(self) -> float:
        """Calculate the unique IRR as a percentage; reject absent or multiple roots."""
        _, cash_flow = self._require_cash_flow()
        flows = np.asarray(cash_flow["cash_flow"], dtype=float)
        if not (np.any(flows < 0) and np.any(flows > 0)):
            raise ValueError("IRR requires at least one negative and one positive cash flow.")

        coefficients = flows.copy()
        while coefficients.size > 1 and coefficients[-1] == 0:
            coefficients = coefficients[:-1]
        roots = np.polynomial.polynomial.polyroots(coefficients)
        scale = max(float(np.sum(np.abs(coefficients))), 1.0)
        rates: list[float] = []
        for root in roots:
            if abs(float(root.imag)) > 1e-8 * max(1.0, abs(float(root.real))):
                continue
            x = float(root.real)
            if x <= 0:
                continue
            rate = 1.0 / x - 1.0
            if rate <= -1.0 or not np.isfinite(rate):
                continue
            residual = float(np.polynomial.polynomial.polyval(x, coefficients))
            if abs(residual) > 1e-7 * scale:
                continue
            if not any(abs(rate - existing) <= 1e-7 * max(1.0, abs(rate)) for existing in rates):
                rates.append(rate)

        if len(rates) != 1:
            raise ValueError(
                "Cash flows must have exactly one real IRR greater than -100 percent."
            )
        return rates[0] * 100.0

    def calculate_payback(self) -> float:
        """Return discounted-independent payback in years with linear interpolation."""
        _, cash_flow = self._require_cash_flow()
        flows = np.asarray(cash_flow["cash_flow"], dtype=float)
        cumulative = np.cumsum(flows)
        recovered = np.flatnonzero(cumulative >= 0)
        if recovered.size == 0:
            raise ValueError("Project does not recover its initial investment.")
        year_index = int(recovered[0])
        if year_index == 0:
            return 0.0
        previous_balance = float(cumulative[year_index - 1])
        annual_flow = float(flows[year_index])
        if annual_flow <= 0:
            raise ValueError("Payback cannot be interpolated across a non-positive cash flow.")
        return float((year_index - 1) + (-previous_balance / annual_flow))

    def calculate_roi(self) -> float:
        """Calculate undiscounted net project return divided by initial CAPEX."""
        parameters, cash_flow = self._require_cash_flow()
        investment = float(sum(parameters["capex"].values()))
        if investment <= 0:
            raise ValueError("ROI is undefined when initial CAPEX is zero.")
        return float(np.sum(cash_flow["cash_flow"]) / investment * 100.0)

    def sensitivity_analysis(
        self, parameter: str, range_values: Sequence[float]
    ) -> dict[float, float]:
        """Recalculate NPV over scalar economic assumptions without mutating state."""
        parameters = self._require_parameters(self.economic_parameters)
        if self._production_data is None:
            raise ValueError("Calculate cash flow before running sensitivity analysis.")
        if parameter not in {
            "oil_price",
            "gas_price",
            "discount_rate",
            "tax_rate",
            "water_disposal_cost_per_bbl",
        }:
            raise ValueError(f"Unsupported sensitivity parameter: {parameter}")

        results: dict[float, float] = {}
        for raw_value in range_values:
            value = float(raw_value)
            if not np.isfinite(value):
                raise ValueError("Sensitivity values must be finite.")
            trial = {**parameters, parameter: value}
            self._validate_scalar_parameters(trial)
            result = self._build_cash_flow(trial, self._production_data)
            results[value] = self._npv(result["cash_flow"], trial["discount_rate"])
        return results

    def monte_carlo_simulation(
        self,
        n_simulations: int,
        parameters: Mapping[str, tuple[Callable[..., float], ...]],
    ) -> dict[str, float]:
        """Sample scalar assumptions from callables and summarize simulated NPV."""
        base_parameters = self._require_parameters(self.economic_parameters)
        if self._production_data is None:
            raise ValueError("Calculate cash flow before running Monte Carlo analysis.")
        if isinstance(n_simulations, bool) or n_simulations <= 0:
            raise ValueError("n_simulations must be a positive integer.")
        if not isinstance(n_simulations, int):
            raise ValueError("n_simulations must be a positive integer.")
        if not parameters:
            raise ValueError("At least one sampled parameter distribution is required.")
        supported = {
            "oil_price",
            "gas_price",
            "discount_rate",
            "tax_rate",
            "water_disposal_cost_per_bbl",
        }
        if set(parameters) - supported:
            raise ValueError(
                f"Unsupported Monte Carlo parameters: {sorted(set(parameters) - supported)}"
            )

        npvs = np.empty(n_simulations, dtype=float)
        for index in range(n_simulations):
            trial = dict(base_parameters)
            for name, distribution in parameters.items():
                if not distribution or not callable(distribution[0]):
                    raise ValueError(
                        f"Distribution for {name!r} must be a callable and its arguments."
                    )
                trial[name] = float(distribution[0](*distribution[1:]))
            self._validate_scalar_parameters(trial)
            cash_flow = self._build_cash_flow(trial, self._production_data)
            npvs[index] = self._npv(cash_flow["cash_flow"], trial["discount_rate"])

        return {
            "mean": float(np.mean(npvs)),
            "std": float(np.std(npvs)),
            "p10": float(np.percentile(npvs, 10)),
            "p50": float(np.percentile(npvs, 50)),
            "p90": float(np.percentile(npvs, 90)),
        }
