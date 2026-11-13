import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  analyzeWellTestBuildup: vi.fn(),
  analyzeWellTestDrawdown: vi.fn(),
}));

vi.mock("@/lib/api", () => mocks);

import WellTestAnalysisView from "../WellTestAnalysisView";

describe("WellTestAnalysisView", () => {
  beforeEach(() => {
    mocks.analyzeWellTestDrawdown.mockReset().mockResolvedValue({
      permeability_md: 25,
      skin: 1.1,
      slope_psi_per_cycle: 120,
      intercept_psi: 30,
      p1hr_psi: 3200,
      radius_of_investigation_ft: 350,
      regimes: { radial: null, wellbore_storage: null, boundary: null, radial_slope: null, radial_std: null, notes: [] },
    });
    mocks.analyzeWellTestBuildup.mockReset();
  });

  it("submits drawdown data with the backend schema and displays results", async () => {
    render(<WellTestAnalysisView />);
    fireEvent.change(screen.getByLabelText(/Elapsed time/), {
      target: { value: "0.1, 0.2, 0.5" },
    });
    fireEvent.change(screen.getByLabelText(/Pressure/), {
      target: { value: "3400, 3320, 3250" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Analyze drawdown" }));

    await waitFor(() => {
      expect(mocks.analyzeWellTestDrawdown).toHaveBeenCalledWith({
        time: [0.1, 0.2, 0.5],
        pressure: [3400, 3320, 3250],
        rate: 500,
        viscosity: 1,
        total_compressibility: 0.00001,
        porosity: 0.2,
        wellbore_radius: 0.35,
        net_pay: 30,
        formation_volume_factor: 1.2,
        initial_pressure: 3500,
      });
    });
    expect(await screen.findByText("25.000 mD")).toBeInTheDocument();
  });

  it("rejects mismatched time and pressure arrays before making a request", async () => {
    render(<WellTestAnalysisView />);
    fireEvent.change(screen.getByLabelText(/Elapsed time/), {
      target: { value: "0.1, 0.2, 0.5" },
    });
    fireEvent.change(screen.getByLabelText(/Pressure/), {
      target: { value: "3400, 3320, 3250, 3200" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Analyze drawdown" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Time and pressure must contain the same number of values.",
    );
    expect(mocks.analyzeWellTestDrawdown).not.toHaveBeenCalled();
  });
});
