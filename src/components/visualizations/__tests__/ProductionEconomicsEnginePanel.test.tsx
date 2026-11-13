import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  calculateProductionEconomics: vi.fn(),
}));

vi.mock("@/lib/api", () => mocks);

import ProductionEconomicsEnginePanel from "../ProductionEconomicsEnginePanel";

describe("ProductionEconomicsEnginePanel", () => {
  beforeEach(() => {
    mocks.calculateProductionEconomics.mockReset().mockResolvedValue({
      npv: 25_000,
      irr: 12,
      payout: 2,
      roi: 15,
      cashflow: [-1_500_000, 500_000, 600_000, 700_000],
      cumulative_cashflow: [-1_500_000, -1_000_000, -400_000, 300_000],
      cash_flow_details: {
        revenue: { oil: [], gas: [], total: [] },
        costs: { opex: [], water_disposal: [], total: [], initial_capex: 1_500_000 },
        depreciation: [],
        ebitda: [],
        ebit: [],
        taxes: [],
        net_income: [],
        operating_cash_flow: [],
        cash_flow: [],
      },
    });
  });

  it("submits all economic assumptions and annual volume profiles", async () => {
    render(<ProductionEconomicsEnginePanel />);
    fireEvent.click(screen.getByRole("button", { name: "Run backend economics" }));

    await waitFor(() => {
      expect(mocks.calculateProductionEconomics).toHaveBeenCalledWith({
        oil_price: 70,
        gas_price: 3,
        discount_rate: 10,
        project_life: 3,
        capex: { initial_capex: 1_500_000 },
        opex: { annual_opex: 75_000 },
        tax_rate: 0.34,
        water_disposal_cost_per_bbl: 1.5,
        oil_production: [100_000, 80_000, 60_000],
        gas_production: [500_000, 400_000, 300_000],
        water_production: [20_000, 30_000, 40_000],
      });
    });
    expect(await screen.findByText(/NPV:/)).toBeInTheDocument();
    expect(screen.getByText("12.00%")).toBeInTheDocument();
  });

  it("rejects production profiles with different lengths", async () => {
    render(<ProductionEconomicsEnginePanel />);
    fireEvent.change(screen.getByLabelText("Gas volumes (Mscf/year)"), {
      target: { value: "500000" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Run backend economics" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Oil, gas, and water profiles must have the same number of annual volumes.",
    );
    expect(mocks.calculateProductionEconomics).not.toHaveBeenCalled();
  });
});
