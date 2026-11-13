import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  calculateReservoirOperation: vi.fn(),
}));

vi.mock("@/lib/api", () => mocks);

import ReservoirOperationsView from "../ReservoirOperationsView";

describe("ReservoirOperationsView", () => {
  beforeEach(() => {
    mocks.calculateReservoirOperation.mockReset().mockResolvedValue({
      p_wh: 850,
      method: "gilbert_eq_5_12",
    });
  });

  it("submits the selected operation with its documented fields", async () => {
    render(<ReservoirOperationsView />);

    fireEvent.click(screen.getByRole("button", { name: "Calculate" }));

    await waitFor(() => {
      expect(mocks.calculateReservoirOperation).toHaveBeenCalledWith(
        "choke/gilbert",
        { q_bpd: 1000, glr: 600, choke_64: 32 },
      );
    });
    expect(await screen.findByText("gilbert_eq_5_12")).toBeInTheDocument();
    expect(screen.getByText("850.00")).toBeInTheDocument();
  });

  it("makes every backend choke, tubing, and gas-lift calculation selectable", () => {
    render(<ReservoirOperationsView />);
    const options = screen.getByLabelText("Calculation").querySelectorAll("option");

    expect(Array.from(options, (option) => option.value)).toEqual([
      "choke/gilbert",
      "choke/critical-ratio",
      "choke/sonic-gas",
      "choke/subsonic-gas",
      "tubing/collapse-biaxial",
      "tubing/ballooning",
      "tubing/piston",
      "tubing/bending-stress",
      "gas-lift/valve-depth",
      "gas-lift/valve-open-close",
      "gas-lift/orifice-size",
      "gas-lift/injection-glr",
    ]);
  });
});
