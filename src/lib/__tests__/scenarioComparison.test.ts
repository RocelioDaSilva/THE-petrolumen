import { describe, expect, it } from "vitest";
import type { SavedSimulation } from "@/lib/api";
import {
  buildPressureComparisonData,
  buildScenarioComparisonMetrics,
} from "@/lib/scenarioComparison";

function savedRun(
  id: number,
  input_data: Record<string, unknown>,
  result_data: Record<string, unknown>,
): SavedSimulation {
  return {
    id,
    name: `Scenario ${id}`,
    simulation_type: "reservoir-simulation",
    created_at: "2026-11-13T10:00:00Z",
    input_data,
    result_data,
  };
}

describe("scenario comparison calculations", () => {
  it("aligns pressure histories on elapsed time and interpolates different timesteps", () => {
    const runA = savedRun(1, {}, {
      history: [
        { time: 0, wellbore: 3000 },
        { time: 10, wellbore: 2800 },
      ],
    });
    const runB = savedRun(2, {}, {
      history: [
        { time: 0, wellbore: 2900 },
        { time: 5, wellbore: 2800 },
        { time: 10, wellbore: 2700 },
      ],
    });

    expect(buildPressureComparisonData(runA, runB)).toEqual([
      { time: 0, runA: 3000, runB: 2900 },
      { time: 5, runA: 2900, runB: 2800 },
      { time: 10, runA: 2800, runB: 2700 },
    ]);
  });

  it("computes result deltas and constant-rate cumulative production", () => {
    const runA = savedRun(
      1,
      { pi: 3000, dt: 5, nSteps: 10, wellRate: -100 },
      { finalPressure: 2600, pressureDrop: 400 },
    );
    const runB = savedRun(
      2,
      { pi: 3000, dt: 10, nSteps: 5, wellRate: -200 },
      { finalPressure: 2400, pressureDrop: 600 },
    );

    const metrics = buildScenarioComparisonMetrics(runA, runB);
    const finalPressure = metrics.find((item) => item.id === "final-pressure");
    expect(finalPressure).toMatchObject({
      valueA: 2600,
      valueB: 2400,
      delta: -200,
    });
    expect(finalPressure?.percentDelta).toBeCloseTo((-200 / 2600) * 100);
    expect(metrics.find((item) => item.id === "cumulative-production")).toMatchObject({
      valueA: 5000,
      valueB: 10000,
      delta: 5000,
      percentDelta: 100,
    });
  });

  it("reports an undefined percentage when the baseline is zero", () => {
    const runA = savedRun(1, {}, { finalPressure: 0 });
    const runB = savedRun(2, {}, { finalPressure: 250 });

    expect(buildScenarioComparisonMetrics(runA, runB)[0]).toMatchObject({
      delta: 250,
      percentDelta: null,
    });
  });
});
