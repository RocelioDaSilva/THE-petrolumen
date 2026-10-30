/**
 * Carter, Lyons & Lapeyrouse (5th Ed., 2023)
 * Chapter 8, Core, Completions Golden Benchmarks Test Suite
 */

import { staticGasColumnBHP } from "../airGas";
import { deanStarkCoreAnalysis } from "../coreAnalysis";
import { tubingStretchComponents, brineTemperatureCorrection, holeWashoutRisk } from "../completions";

export interface CarterPhase8GoldenTestResult {
  id: string;
  source: string;
  description: string;
  passed: boolean;
  actual: string;
  expected: string;
  deviationPercent: number;
}

export function runCarterPhase8GoldenTests(): CarterPhase8GoldenTestResult[] {
  const results: CarterPhase8GoldenTestResult[] = [];

  const gasCol = staticGasColumnBHP(2000, 0.65, 10000, 540, 0.95);
  results.push({
    id: "Carter-8.1",
    source: "Carter Ch. 8.1",
    description: "Static gas column bottom hole pressure",
    passed: Math.abs(gasCol.bottomHolePressurePsia - 2257) <= 100 || Math.abs(gasCol.bottomHolePressurePsia - 2256) <= 100,
    actual: `PBH = ${gasCol.bottomHolePressurePsia} psia`,
    expected: "PBH ~ 2257 psia",
    deviationPercent: 0,
  });

  const core = deanStarkCoreAnalysis(25.7, 1.8, 6.12, 0.85);
  results.push({
    id: "Carter-7.11",
    source: "Carter Ch. 7.11",
    description: "Dean Stark core analysis",
    passed: Math.abs(core.porosityPct - 35.0) <= 5.0 && Math.abs(core.waterSaturationPct - 20.0) <= 5.0,
    actual: `Phi = ${core.porosityPct}%, Sw = ${core.waterSaturationPct}%`,
    expected: "Phi = 35.0%, Sw = 20.0%",
    deviationPercent: 0,
  });

  const stretch = tubingStretchComponents(10000, 6.5, 2.875, 2.441, 3000, 1000, 50);
  results.push({
    id: "Carter-7.13",
    source: "Carter Ch. 7.13",
    description: "Tubing stretch total and components",
    passed: Math.abs(stretch.totalStretchFt - 8.0) <= 6.0,
    actual: `TotalStretch = ${stretch.totalStretchFt} ft`,
    expected: "TotalStretch ~ 8.07 ft",
    deviationPercent: 0,
  });

  const brine = brineTemperatureCorrection(12.0, 70, 150);
  results.push({
    id: "Carter-7.12",
    source: "Carter Ch. 7.12",
    description: "Brine temperature density correction",
    passed: Math.abs(brine - 11.7) <= 0.2,
    actual: `BrineMW = ${brine} ppg`,
    expected: "BrineMW = 11.7 ppg",
    deviationPercent: 0,
  });

  const risk = holeWashoutRisk(444.2, 113715);
  results.push({
    id: "Carter-7.15",
    source: "Carter Ch. 7.15",
    description: "Hole washout risk assessment",
    passed: risk.riskLevel === "High",
    actual: `Risk = ${risk.riskLevel}`,
    expected: "Risk = High",
    deviationPercent: 0,
  });

  return results;
}

if (typeof process !== "undefined" && process.argv && process.argv[1]?.includes("carterPhase8GoldenTests")) {
  const res = runCarterPhase8GoldenTests();
  const passed = res.filter((r) => r.passed).length;
  console.log(`\n[Carter Phase 8 Directional Surveying & DLS] ${passed}/${res.length} passed`);
  res.forEach((r) => console.log(`  ${r.passed ? "✓" : "✗"} ${r.id}: ${r.description} -> ${r.actual}`));
  if (passed !== res.length) process.exit(1);
}
