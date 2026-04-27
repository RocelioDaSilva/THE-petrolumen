import numpy as np
import numpy_financial as npf
from typing import Dict, List, Any

def run_economics(
    forecast_time: np.ndarray,
    forecast_rate: np.ndarray,
    oil_price: float,
    capex: float,
    opex_fixed: float,
    opex_var: float,
    discount_rate: float,
    tax_rate: float = 0.25
) -> Dict[str, Any]:
    """
    Simple economic model for a project.
    """
    revenue = forecast_rate * oil_price
    variable_opex = forecast_rate * opex_var
    total_opex = variable_opex + opex_fixed

    cash_flow = revenue - total_opex
    cash_flow[0] -= capex

    taxable_income = np.maximum(0, cash_flow)
    taxes = taxable_income * tax_rate
    net_cash_flow = cash_flow - taxes

    monthly_discount_rate = (1 + discount_rate)**(1/12) - 1
    npv = npf.npv(monthly_discount_rate, net_cash_flow)

    try:
        irr_monthly = npf.irr(net_cash_flow)
        irr_annual = (1 + irr_monthly)**12 - 1 if irr_monthly else 0
    except Exception:
        irr_annual = 0

    cum_cash_flow = np.cumsum(net_cash_flow)
    payout_month = np.where(cum_cash_flow >= 0)[0]
    payout = int(payout_month[0]) if len(payout_month) > 0 else None

    return {
        "npv": float(npv),
        "irr": float(irr_annual),
        "payout_month": payout,
        "net_cash_flow": net_cash_flow.tolist(),
        "cum_cash_flow": cum_cash_flow.tolist()
    }
