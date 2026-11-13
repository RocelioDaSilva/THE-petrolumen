import type { ReactNode } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { SavedSimulation } from "@/lib/api";
import ScenarioComparisonView from "../ScenarioComparisonView";

vi.mock("recharts", () => ({
  CartesianGrid: () => null,
  Legend: () => null,
  Line: () => null,
  LineChart: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  ResponsiveContainer: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  Tooltip: () => null,
  XAxis: () => null,
  YAxis: () => null,
}));

const runs: [SavedSimulation, SavedSimulation] = [
  {
    id: 1,
    name: "Base case",
    simulation_type: "reservoir-simulation",
    created_at: "2026-11-13T10:00:00Z",
    input_data: { pi: 3000, dt: 5, nSteps: 10, wellRate: -100 },
    result_data: {
      finalPressure: 2600,
      pressureDrop: 400,
      history: [
        { time: 0, wellbore: 3000 },
        { time: 50, wellbore: 2600 },
      ],
    },
  },
  {
    id: 2,
    name: "High-rate case",
    simulation_type: "reservoir-simulation",
    created_at: "2026-11-13T11:00:00Z",
    input_data: { pi: 3000, dt: 10, nSteps: 5, wellRate: -200 },
    result_data: {
      finalPressure: 2400,
      pressureDrop: 600,
      history: [
        { time: 0, wellbore: 3000 },
        { time: 50, wellbore: 2400 },
      ],
    },
  },
];

describe("ScenarioComparisonView", () => {
  it("shows paired assumptions, pressure chart, and result deltas", () => {
    const { container } = render(
      <ScenarioComparisonView runs={runs} onReturnToSavedRuns={vi.fn()} />,
    );
    const text = container.textContent ?? "";

    expect(text).toContain("Scenario Comparison");
    expect(text).toContain("Base case");
    expect(text).toContain("High-rate case");
    expect(text).toContain("Input assumptions");
    expect(text).toContain("Pressure vs. time");
    expect(text).toContain("Final wellbore pressure");
    expect(text).toContain("Implied cumulative production (constant rate)");
    expect(text).toContain("100%");
  });

  it("offers a route back when no pair has been selected", () => {
    const onReturnToSavedRuns = vi.fn();
    render(<ScenarioComparisonView runs={null} onReturnToSavedRuns={onReturnToSavedRuns} />);

    fireEvent.click(screen.getByRole("button", { name: "Return to Saved Runs" }));

    expect(onReturnToSavedRuns).toHaveBeenCalledOnce();
  });
});
