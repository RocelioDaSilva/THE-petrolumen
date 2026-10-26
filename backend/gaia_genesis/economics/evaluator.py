from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Union
import numpy as np
import numpy_financial as npf
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class EconomicParameters:
    capex: float  # Initial capital expenditure ($)
    capex_schedule: Optional[List[float]] = None  # Optional period-by-period CAPEX ($)
    oil_price: float = 70.0  # $/bbl
    gas_price: float = 3.0  # $/Mcf
    price_escalation_annual: float = 0.0  # Annual price escalation rate (e.g. 0.02 for 2%)
    opex_fixed_monthly: float = 1000.0  # $/month
    opex_var_oil: float = 5.0  # $/bbl oil
    opex_var_gas: float = 0.5  # $/Mcf gas
    opex_var_water: float = 1.0  # $/bbl water
    royalty_rate: float = 0.125  # Fraction (e.g., 12.5%)
    severance_tax_rate: float = 0.05  # Fraction (e.g., 5%)
    income_tax_rate: float = 0.21  # Fraction (e.g., 21%)
    discount_rate_annual: float = 0.10  # Fraction (e.g., 10%)
    period_frequency: str = "monthly"  # "monthly" or "annual"


@dataclass
class ProductionForecast:
    time_periods: List[float]  # Period indices or months/years
    oil_rates: List[float]  # bbl/period or bbl/day
    gas_rates: Optional[List[float]] = None  # Mcf/period or Mcf/day
    water_rates: Optional[List[float]] = None  # bbl/period or bbl/day
    rates_are_daily: bool = False  # If True, rates will be converted assuming 30.4375 days/month or 365 days/year


@dataclass
class CashFlowPeriod:
    period: int
    time: float
    oil_volume: float
    gas_volume: float
    water_volume: float
    oil_price: float
    gas_price: float
    gross_revenue: float
    net_revenue: float
    opex: float
    severance_tax: float
    ebitda: float
    taxable_income: float
    income_tax: float
    capex: float
    net_cash_flow: float
    cumulative_net_cash_flow: float
    discount_factor: float
    discounted_cash_flow: float
    cumulative_discounted_cash_flow: float


@dataclass
class EconomicResult:
    npv: float
    irr: float
    payout_period: float  # Period index (e.g. month or year) when cumulative cash flow becomes >= 0
    payout_months: float
    payout_years: float
    total_gross_revenue: float
    total_net_revenue: float
    total_opex: float
    total_capex: float
    total_net_cash_flow: float
    profitability_index: float
    return_on_investment: float
    cash_flow_periods: List[CashFlowPeriod]

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["cash_flows"] = [p["net_cash_flow"] for p in res["cash_flow_periods"]]
        res["cumulative_cash_flow"] = [
            p["cumulative_net_cash_flow"] for p in res["cash_flow_periods"]
        ]
        res["discounted_cash_flows"] = [
            p["discounted_cash_flow"] for p in res["cash_flow_periods"]
        ]
        return res


class EconomicsEvaluator:
    """
    Engine for comprehensive economic evaluations in petroleum engineering.
    Calculates period-by-period revenues, OPEX, taxes, Net Cash Flows, NPV, IRR, Payout Time, and ROI.
    """

    @classmethod
    def evaluate(
        cls,
        params: EconomicParameters,
        forecast: ProductionForecast,
    ) -> EconomicResult:
        """
        Executes period-by-period cash flow simulation and calculates key economic indicators.
        """
        num_periods = len(forecast.time_periods)
        if num_periods == 0:
            raise ValueError("Production forecast cannot be empty.")

        period_days = 30.4375 if params.period_frequency == "monthly" else 365.25
        periods_per_year = 12.0 if params.period_frequency == "monthly" else 1.0
        periodic_discount_rate = (1.0 + params.discount_rate_annual) ** (
            1.0 / periods_per_year
        ) - 1.0

        cash_flow_periods: List[CashFlowPeriod] = []
        cum_ncf = 0.0
        cum_dcf = 0.0

        gas_rates = forecast.gas_rates or [0.0] * num_periods
        water_rates = forecast.water_rates or [0.0] * num_periods

        total_gross_rev = 0.0
        total_net_rev = 0.0
        total_opex = 0.0
        total_capex = params.capex

        # Period 0 (Initial CAPEX)
        p0_capex = params.capex
        if params.capex_schedule and len(params.capex_schedule) > 0:
            p0_capex = params.capex_schedule[0]

        cum_ncf = -p0_capex
        cum_dcf = -p0_capex

        p0_cf = CashFlowPeriod(
            period=0,
            time=0.0,
            oil_volume=0.0,
            gas_volume=0.0,
            water_volume=0.0,
            oil_price=params.oil_price,
            gas_price=params.gas_price,
            gross_revenue=0.0,
            net_revenue=0.0,
            opex=0.0,
            severance_tax=0.0,
            ebitda=0.0,
            taxable_income=0.0,
            income_tax=0.0,
            capex=p0_capex,
            net_cash_flow=-p0_capex,
            cumulative_net_cash_flow=cum_ncf,
            discount_factor=1.0,
            discounted_cash_flow=-p0_capex,
            cumulative_discounted_cash_flow=cum_dcf,
        )
        cash_flow_periods.append(p0_cf)

        # Subsequent production periods
        for idx in range(num_periods):
            p_num = idx + 1
            t_val = forecast.time_periods[idx]

            # Volume calculation
            q_oil = forecast.oil_rates[idx]
            q_gas = gas_rates[idx] if idx < len(gas_rates) else 0.0
            q_water = water_rates[idx] if idx < len(water_rates) else 0.0

            vol_oil = q_oil * period_days if forecast.rates_are_daily else q_oil
            vol_gas = q_gas * period_days if forecast.rates_are_daily else q_gas
            vol_water = q_water * period_days if forecast.rates_are_daily else q_water

            # Price escalation per period
            year_frac = p_num / periods_per_year
            price_factor = (1.0 + params.price_escalation_annual) ** year_frac
            oil_p = params.oil_price * price_factor
            gas_p = params.gas_price * price_factor

            gross_rev = (vol_oil * oil_p) + (vol_gas * gas_p)
            net_rev = gross_rev * (1.0 - params.royalty_rate)

            # OPEX
            opex_fixed = (
                params.opex_fixed_monthly
                if params.period_frequency == "monthly"
                else params.opex_fixed_monthly * 12.0
            )
            opex_var = (
                (vol_oil * params.opex_var_oil)
                + (vol_gas * params.opex_var_gas)
                + (vol_water * params.opex_var_water)
            )
            opex_total = opex_fixed + opex_var

            # Severance tax
            sev_tax = net_rev * params.severance_tax_rate

            # EBITDA
            ebitda = net_rev - opex_total - sev_tax

            # Income tax
            taxable = max(0.0, ebitda)
            inc_tax = taxable * params.income_tax_rate

            # CAPEX for period if scheduled
            p_capex = 0.0
            if params.capex_schedule and p_num < len(params.capex_schedule):
                p_capex = params.capex_schedule[p_num]
                total_capex += p_capex

            ncf = ebitda - inc_tax - p_capex
            cum_ncf += ncf

            disc_factor = 1.0 / ((1.0 + periodic_discount_rate) ** p_num)
            dcf = ncf * disc_factor
            cum_dcf += dcf

            total_gross_rev += gross_rev
            total_net_rev += net_rev
            total_opex += opex_total

            cash_flow_periods.append(
                CashFlowPeriod(
                    period=p_num,
                    time=t_val,
                    oil_volume=vol_oil,
                    gas_volume=vol_gas,
                    water_volume=vol_water,
                    oil_price=oil_p,
                    gas_price=gas_p,
                    gross_revenue=gross_rev,
                    net_revenue=net_rev,
                    opex=opex_total,
                    severance_tax=sev_tax,
                    ebitda=ebitda,
                    taxable_income=taxable,
                    income_tax=inc_tax,
                    capex=p_capex,
                    net_cash_flow=ncf,
                    cumulative_net_cash_flow=cum_ncf,
                    discount_factor=disc_factor,
                    discounted_cash_flow=dcf,
                    cumulative_discounted_cash_flow=cum_dcf,
                )
            )

        # Economic Indicators
        npv_val = cum_dcf

        # IRR Calculation
        ncf_list = [p.net_cash_flow for p in cash_flow_periods]
        irr_val = cls._calculate_irr(ncf_list, periods_per_year)

        # Payout Period Interpolation
        payout_period, payout_months, payout_years = cls._calculate_payout(
            cash_flow_periods, params.period_frequency
        )

        # Profitability Index & ROI
        pi_val = (npv_val + total_capex) / total_capex if total_capex > 0 else 0.0
        roi_val = cum_ncf / total_capex if total_capex > 0 else 0.0

        return EconomicResult(
            npv=float(npv_val),
            irr=float(irr_val),
            payout_period=float(payout_period),
            payout_months=float(payout_months),
            payout_years=float(payout_years),
            total_gross_revenue=float(total_gross_rev),
            total_net_revenue=float(total_net_rev),
            total_opex=float(total_opex),
            total_capex=float(total_capex),
            total_net_cash_flow=float(cum_ncf),
            profitability_index=float(pi_val),
            return_on_investment=float(roi_val),
            cash_flow_periods=cash_flow_periods,
        )

    @classmethod
    def _calculate_irr(cls, ncf_list: List[float], periods_per_year: float) -> float:
        """Calculates annualized Internal Rate of Return (IRR)."""
        try:
            periodic_irr = npf.irr(ncf_list)
            if periodic_irr is not None and not np.isnan(periodic_irr) and not np.isinf(periodic_irr):
                # Convert periodic rate to effective annual rate
                annual_irr = ((1.0 + periodic_irr) ** periods_per_year) - 1.0
                return float(annual_irr)
        except Exception as e:
            logger.warning("IRR calculation did not converge", error=str(e))
        return 0.0

    @classmethod
    def _calculate_payout(
        cls, cash_flow_periods: List[CashFlowPeriod], frequency: str
    ) -> tuple[float, float, float]:
        """Linearly interpolates exact payout period, payout months, and payout years."""
        payout_idx = -1.0
        for i in range(1, len(cash_flow_periods)):
            prev_cf = cash_flow_periods[i - 1]
            curr_cf = cash_flow_periods[i]

            if curr_cf.cumulative_net_cash_flow >= 0.0:
                if prev_cf.cumulative_net_cash_flow < 0.0:
                    # Linear interpolation
                    y0 = prev_cf.cumulative_net_cash_flow
                    y1 = curr_cf.cumulative_net_cash_flow
                    fraction = (0.0 - y0) / (y1 - y0) if (y1 - y0) != 0 else 0.0
                    payout_idx = (i - 1) + fraction
                else:
                    payout_idx = float(i)
                break

        if payout_idx < 0:
            return -1.0, -1.0, -1.0

        if frequency == "monthly":
            months = payout_idx
            years = payout_idx / 12.0
        else:
            years = payout_idx
            months = payout_idx * 12.0

        return payout_idx, months, years
