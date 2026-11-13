import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  calculateMaterialBalance: vi.fn(),
}));

vi.mock("@/lib/api", () => mocks);

import MaterialBalanceEnginePanel from "../MaterialBalanceEnginePanel";

describe("MaterialBalanceEnginePanel", () => {
  beforeEach(() => {
    mocks.calculateMaterialBalance.mockReset().mockResolvedValue({
      reservoir_type: "gas",
      ooip_or_ogip: 1_500_000,
      drive_indices: null,
      note: "scalar result",
    });
  });

  it("sends the entered pressure and production histories to the backend", async () => {
    render(<MaterialBalanceEnginePanel />);
    fireEvent.click(screen.getByRole("button", { name: "Run Havlena–Odeh" }));

    await waitFor(() => {
      expect(mocks.calculateMaterialBalance).toHaveBeenCalledWith({
        reservoir_type: "gas",
        pressure_history: [4000, 3200],
        production_history: [{ gas_prod: 5_000_000, water_prod: 100 }],
      });
    });
    expect(await screen.findByText("OGIP: 1.50000e+6")).toBeInTheDocument();
  });

  it("displays local validation failures instead of sending malformed history", async () => {
    render(<MaterialBalanceEnginePanel />);
    fireEvent.change(screen.getByLabelText("Pressure history (psia, comma-separated)"), {
      target: { value: "4000" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Run Havlena–Odeh" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Pressure history needs at least two values.",
    );
    expect(mocks.calculateMaterialBalance).not.toHaveBeenCalled();
  });
});
