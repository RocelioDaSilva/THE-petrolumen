import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  runBlackOilSimulation: vi.fn(),
}));

vi.mock("@/lib/api", () => mocks);

import BlackOilSimulationView from "../BlackOilSimulationView";

describe("BlackOilSimulationView", () => {
  beforeEach(() => {
    mocks.runBlackOilSimulation.mockReset().mockResolvedValue({
      pressure: [2900, 3000],
      saturations: { water: [0.2, 0.2], gas: [0, 0] },
      wells: [],
    });
  });

  it("submits a schema-aligned grid payload and displays the returned final state", async () => {
    render(<BlackOilSimulationView />);
    fireEvent.click(screen.getByRole("button", { name: "Run black-oil solver" }));

    await waitFor(() => {
      expect(mocks.runBlackOilSimulation).toHaveBeenCalledWith({
        grid: { nx: 2, ny: 1, nz: 1, dx: 50, dy: 50, dz: 10 },
        porosity: [0.2, 0.2],
        permeability: [100, 100],
        rock_compressibility: 0,
        fluid_properties: {
          water_viscosity: 1,
          oil_viscosity: 2,
          gas_viscosity: 0.02,
        },
        initial_pressure: 3000,
        initial_water_saturation: [0.2, 0.2],
        initial_gas_saturation: [0, 0],
        timesteps: [1],
      });
    });
    expect(await screen.findByText("2900.00")).toBeInTheDocument();
    expect(screen.getByText("Engineering limitation: this backend solver is documented as simplified and non-conservative. Treat results as experimental, not design-grade predictions.")).toBeInTheDocument();
  });

  it("rejects per-cell arrays with the wrong number of entries before calling the API", async () => {
    render(<BlackOilSimulationView />);
    fireEvent.change(screen.getByLabelText("Porosity per cell"), { target: { value: "0.2" } });
    fireEvent.click(screen.getByRole("button", { name: "Run black-oil solver" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Porosity must contain exactly 2 finite comma-separated values.",
    );
    expect(mocks.runBlackOilSimulation).not.toHaveBeenCalled();
  });
});
