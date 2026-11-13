import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  classifyFacies: vi.fn(),
  parseLasFile: vi.fn(),
  runOoipCalculation: vi.fn(),
  uploadOoipLas: vi.fn(),
}));

vi.mock("@/lib/api", () => mocks);
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

import WellDataViewer from "../WellDataViewer";

describe("WellDataViewer backend workflows", () => {
  beforeEach(() => {
    mocks.classifyFacies.mockReset().mockResolvedValue({
      facies_predictions: [1, 1, 3],
      classes: [1, 2, 3, 4],
      features_used: ["gamma", "resistivity", "density", "porosity"],
      training_samples_count: 8,
      classification_report: null,
    });
    mocks.parseLasFile.mockReset();
    mocks.runOoipCalculation.mockReset();
    mocks.uploadOoipLas.mockReset();
  });

  it("sends displayed well-log samples to the backend facies classifier", async () => {
    render(<WellDataViewer />);

    fireEvent.click(screen.getByRole("button", { name: /Classify 76 samples/ }));

    await waitFor(() => {
      expect(mocks.classifyFacies).toHaveBeenCalledOnce();
    });
    const samples = mocks.classifyFacies.mock.calls[0][0];
    expect(samples).toHaveLength(76);
    expect(samples[0]).toEqual(expect.objectContaining({
      gamma: expect.any(Number),
      resistivity: expect.any(Number),
      density: expect.any(Number),
      porosity: expect.any(Number),
      depth: 2800,
    }));
    expect(await screen.findByText("Facies 1")).toBeInTheDocument();
  });
});
