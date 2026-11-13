import type { SavedSimulation } from "@/lib/api";

export interface PressureComparisonPoint {
  time: number;
  runA: number | null;
  runB: number | null;
}

export interface ScenarioComparisonMetric {
  id: string;
  label: string;
  unit: string;
  valueA: number | null;
  valueB: number | null;
  delta: number | null;
  percentDelta: number | null;
}

interface PressureSample {
  time: number;
  pressure: number;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function finiteNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function pressureHistory(run: SavedSimulation): PressureSample[] {
  const history = run.result_data.history;
  if (!Array.isArray(history)) return [];

  const samples = history.flatMap((step): PressureSample[] => {
    if (!isRecord(step)) return [];
    const time = finiteNumber(step.time);
    const pressure = finiteNumber(step.wellbore);
    return time === null || pressure === null ? [] : [{ time, pressure }];
  });
  return samples.sort((left, right) => left.time - right.time);
}

function pressureAt(samples: PressureSample[], time: number): number | null {
  const lastSample = samples[samples.length - 1];
  if (samples.length === 0 || time < samples[0].time || time > lastSample.time) {
    return null;
  }

  const rightIndex = samples.findIndex((sample) => sample.time >= time);
  if (rightIndex < 0) return null;
  const right = samples[rightIndex];
  if (right.time === time || rightIndex === 0) return right.pressure;

  const left = samples[rightIndex - 1];
  const fraction = (time - left.time) / (right.time - left.time);
  return left.pressure + fraction * (right.pressure - left.pressure);
}

export function buildPressureComparisonData(
  runA: SavedSimulation,
  runB: SavedSimulation,
): PressureComparisonPoint[] {
  const historyA = pressureHistory(runA);
  const historyB = pressureHistory(runB);
  const times = [...new Set([...historyA, ...historyB].map((sample) => sample.time))]
    .sort((left, right) => left - right);

  return times.map((time) => ({
    time,
    runA: pressureAt(historyA, time),
    runB: pressureAt(historyB, time),
  }));
}

function finalPressure(run: SavedSimulation): number | null {
  const storedPressure = finiteNumber(run.result_data.finalPressure);
  if (storedPressure !== null) return storedPressure;
  const history = pressureHistory(run);
  return history.length > 0 ? history[history.length - 1].pressure : null;
}

function durationDays(run: SavedSimulation): number | null {
  const history = pressureHistory(run);
  if (history.length > 0) return history[history.length - 1].time;

  const timeStep = finiteNumber(run.input_data.dt);
  const numberOfSteps = finiteNumber(run.input_data.nSteps);
  if (timeStep === null || numberOfSteps === null) return null;
  const duration = timeStep * numberOfSteps;
  return Number.isFinite(duration) ? duration : null;
}

function metric(
  id: string,
  label: string,
  unit: string,
  valueA: number | null,
  valueB: number | null,
): ScenarioComparisonMetric {
  const delta = valueA === null || valueB === null ? null : valueB - valueA;
  const percentDelta =
    delta === null || valueA === 0 ? null : (delta / Math.abs(valueA)) * 100;
  return { id, label, unit, valueA, valueB, delta, percentDelta };
}

function pressureDrop(run: SavedSimulation): number | null {
  const storedDrop = finiteNumber(run.result_data.pressureDrop);
  if (storedDrop !== null) return storedDrop;

  const initialPressure = finiteNumber(run.input_data.pi);
  const final = finalPressure(run);
  return initialPressure === null || final === null
    ? null
    : Math.max(0, initialPressure - final);
}

function impliedCumulativeProduction(run: SavedSimulation): number | null {
  const rate = finiteNumber(run.input_data.wellRate);
  const duration = durationDays(run);
  if (rate === null || duration === null) return null;
  const volume = Math.abs(rate) * duration;
  return Number.isFinite(volume) ? volume : null;
}

export function buildScenarioComparisonMetrics(
  runA: SavedSimulation,
  runB: SavedSimulation,
): ScenarioComparisonMetric[] {
  const rateA = finiteNumber(runA.input_data.wellRate);
  const rateB = finiteNumber(runB.input_data.wellRate);
  return [
    metric(
      "final-pressure",
      "Final wellbore pressure",
      "psia",
      finalPressure(runA),
      finalPressure(runB),
    ),
    metric(
      "pressure-drop",
      "Pressure drop",
      "psi",
      pressureDrop(runA),
      pressureDrop(runB),
    ),
    metric(
      "production-rate",
      "Specified production rate",
      "STB/d",
      rateA === null ? null : Math.abs(rateA),
      rateB === null ? null : Math.abs(rateB),
    ),
    metric(
      "duration",
      "Simulation horizon",
      "days",
      durationDays(runA),
      durationDays(runB),
    ),
    metric(
      "cumulative-production",
      "Implied cumulative production (constant rate)",
      "STB",
      impliedCumulativeProduction(runA),
      impliedCumulativeProduction(runB),
    ),
  ];
}
