import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  fetchProductionOverview: vi.fn(),
  fetchProductionWells: vi.fn(),
  auth: {
    user: { id: 2, username: "engineer" } as null | { id: number; username: string },
    openAuthDialog: vi.fn(),
  },
  onNavigate: vi.fn(),
}));

vi.mock("@/lib/api", () => ({
  fetchProductionOverview: mocks.fetchProductionOverview,
  fetchProductionWells: mocks.fetchProductionWells,
}));

vi.mock("@/lib/authContext", () => ({
  useAuth: () => mocks.auth,
}));

vi.mock("recharts", () => ({
  CartesianGrid: () => null,
  Legend: () => null,
  Line: () => null,
  LineChart: () => null,
  ResponsiveContainer: () => null,
  Tooltip: () => null,
  XAxis: () => null,
  YAxis: () => null,
}));

import ProductionOverview from "../ProductionOverview";

describe("ProductionOverview", () => {
  beforeEach(() => {
    mocks.auth.user = { id: 2, username: "engineer" };
    mocks.fetchProductionWells.mockReset().mockResolvedValue([
      { id: 1, name: "Well A", field: null, latitude: null, longitude: null },
      { id: 2, name: "Well B", field: null, latitude: null, longitude: null },
    ]);
    mocks.fetchProductionOverview.mockReset().mockResolvedValue({
      series: [
        { date: "2025-01-01", oil_rate: 10, gas_rate: 20, water_rate: 3 },
        { date: "2025-02-01", oil_rate: 13, gas_rate: 18, water_rate: 5 },
      ],
      latest_import_at: "2025-02-02T12:30:00+00:00",
      latest_well_rates: [
        {
          well_id: 1,
          well_name: "Well A",
          date: "2025-02-01",
          oil_rate: 8,
          gas_rate: 18,
          water_rate: 4,
        },
        {
          well_id: 2,
          well_name: "Well B",
          date: "2025-02-01",
          oil_rate: 5,
          gas_rate: null,
          water_rate: 1,
        },
      ],
    });
    mocks.auth.openAuthDialog.mockReset();
    mocks.onNavigate.mockReset();
  });

  it("loads private well data and displays production totals and latest rates", async () => {
    render(<ProductionOverview onNavigate={mocks.onNavigate} />);

    expect(await screen.findByText("Well A")).toBeInTheDocument();
    expect(screen.getByText("Well B")).toBeInTheDocument();
    expect(screen.getByText("Total Wells")).toBeInTheDocument();
    expect(screen.getByText("2", { selector: "p" })).toBeInTheDocument();
    expect(screen.getByText("Total Oil Rate")).toBeInTheDocument();
    expect(screen.getByText("13", { selector: "p" })).toBeInTheDocument();
    expect(screen.getByText("Total Gas Rate")).toBeInTheDocument();
    expect(screen.getByText("18", { selector: "p" })).toBeInTheDocument();
    expect(screen.getByText("Total Water Rate")).toBeInTheDocument();
    expect(screen.getByText("5", { selector: "p" })).toBeInTheDocument();
    expect(screen.getByText("Latest Import Date")).toBeInTheDocument();
    expect(mocks.fetchProductionWells).toHaveBeenCalledOnce();
    expect(mocks.fetchProductionOverview).toHaveBeenCalledOnce();

    fireEvent.click(screen.getByRole("button", { name: "Import production CSV" }));
    expect(mocks.onNavigate).toHaveBeenCalledWith("production-data-import");
  });

  it("shows a clear empty state and links to the CSV import view", async () => {
    mocks.fetchProductionWells.mockResolvedValue([]);
    mocks.fetchProductionOverview.mockResolvedValue({
      series: [],
      latest_import_at: null,
      latest_well_rates: [],
    });
    render(<ProductionOverview onNavigate={mocks.onNavigate} />);

    expect(await screen.findByText("No production data yet.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Import CSV now" }));
    expect(mocks.onNavigate).toHaveBeenCalledWith("production-data-import");
  });

  it("prompts signed-out users to authenticate instead of requesting private data", () => {
    mocks.auth.user = null;
    render(<ProductionOverview onNavigate={mocks.onNavigate} />);

    fireEvent.click(screen.getByRole("button", { name: "Sign in to view production" }));
    expect(mocks.auth.openAuthDialog).toHaveBeenCalledOnce();
    expect(mocks.fetchProductionWells).not.toHaveBeenCalled();
    expect(mocks.fetchProductionOverview).not.toHaveBeenCalled();
  });

  it("surfaces API errors and supports retrying", async () => {
    mocks.fetchProductionWells.mockRejectedValueOnce({ detail: "API unavailable" });
    render(<ProductionOverview onNavigate={mocks.onNavigate} />);

    expect(await screen.findByText("API unavailable")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(mocks.fetchProductionWells).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("Well A")).toBeInTheDocument();
  });
});
