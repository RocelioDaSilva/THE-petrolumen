import numpy as np
import numpy_financial as npf
from typing import Dict, List


def run_economics(
    forecast: List[Dict],
    oil_price: float,
    opex_fixed: float,
    opex_var: float,
    capex: float,
    tax_rate: float,
    discount_rate: float,
) -> Dict:
    """
    Calculates NPV, IRR, and Payout for a given production forecast.
    """
    # Assuming forecast is a list of {'time': ..., 'rate': ...}
    net_cash_flows = [-capex]

    for entry in forecast:
        rate = entry.get("rate", 0)
        revenue = rate * oil_price * 30.44  # Approximate monthly
        opex = opex_fixed + opex_var * rate
        tax = (revenue - opex) * tax_rate
        net_cf = revenue - opex - tax
        net_cash_flows.append(net_cf)

    try:
        npv_val = npf.npv(discount_rate / 12, net_cash_flows)
        irr_val = npf.irr(net_cash_flows)
        if irr_val is not None and not np.isnan(irr_val):
            irr_val = irr_val * 12
        else:
            irr_val = 0.0
    except:
        npv_val = 0.0
        irr_val = 0.0

    # Payout month
    cumulative_cf = np.cumsum(net_cash_flows)
    payout_month = np.where(cumulative_cf >= 0)[0]
    payout = int(payout_month[0]) if len(payout_month) > 0 else -1

    return {
        "npv": float(npv_val),
        "irr": float(irr_val),
        "payout_month": payout,
        "cash_flow_table": net_cash_flows,
    }
