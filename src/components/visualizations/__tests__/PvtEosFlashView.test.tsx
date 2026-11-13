import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  calculateEos: vi.fn(),
  calculateFlash: vi.fn(),
}));

vi.mock("@/lib/api", () => mocks);

import PvtEosFlashView from "../PvtEosFlashView";

describe("PvtEosFlashView", () => {
  beforeEach(() => {
    mocks.calculateEos.mockReset().mockResolvedValue({ z_factor: 0.92 });
    mocks.calculateFlash.mockReset().mockResolvedValue({
      phase: "two_phase",
      vapor_fraction: 0.4,
      liquid_composition: { methane: 0.6 },
      vapor_composition: { methane: 1 },
      K_values: { methane: 1.5 },
    });
  });

  it("submits the EOS request and displays its Z-factor", async () => {
    render(<PvtEosFlashView />);
    fireEvent.click(screen.getByRole("button", { name: "Calculate Z-factor" }));

    await waitFor(() => {
      expect(mocks.calculateEos).toHaveBeenCalledWith({
        pressure: 5_000_000,
        temperature: 250,
        eos_type: "PR",
        components: [{
          name: "methane",
          critical_pressure: 4_599_000,
          critical_temperature: 190.56,
          acentric_factor: 0.011,
        }],
        composition: { methane: 1 },
      });
    });
    expect(await screen.findByText("Z-factor: 0.920000")).toBeInTheDocument();
  });

  it("runs the flash endpoint and displays the phase result", async () => {
    render(<PvtEosFlashView />);
    fireEvent.click(screen.getByRole("button", { name: "Run flash" }));

    await waitFor(() => expect(mocks.calculateFlash).toHaveBeenCalledOnce());
    expect(await screen.findByText("two_phase")).toBeInTheDocument();
    expect(screen.getByText("0.40000")).toBeInTheDocument();
  });

  it("does not submit a mixture whose mole fractions do not sum to one", async () => {
    render(<PvtEosFlashView />);
    fireEvent.change(screen.getByLabelText("Mole fraction"), { target: { value: "0.5" } });
    fireEvent.click(screen.getByRole("button", { name: "Calculate Z-factor" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Mole fractions must be non-negative and sum to 1.");
    expect(mocks.calculateEos).not.toHaveBeenCalled();
  });
});
