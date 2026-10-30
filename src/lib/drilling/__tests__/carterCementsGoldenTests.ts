/**
 * Carter, Lyons & Lapeyrouse (5th Ed., 2023)
 * Chapter 5: Cementing Golden Benchmarks Test Suite
 */

import {
  cementAdditiveWeight,
  cementSlurryVolume,
  cementSlurryYield,
  cementSlurryDensity,
  barrelsMudToBump,
  strokesToBumpPlug,
  hydraulicingCasing,
} from "../cements";

export interface CarterCementsGoldenTestResult {
  id: string;
  source: string;
  description: string;
  passed: boolean;
  actual: string;
  expected: string;
  deviationPercent: number;
}

export function runCarterCementsGoldenTests(): CarterCementsGoldenTestResult[] {
  const results: CarterCementsGoldenTestResult[] = [];

  const wAdd = cementAdditiveWeight(94, 4);
  const vWater = 7.8;
  const vSlurryGal = cementSlurryVolume(94, vWater, 3.14, 2.65, wAdd);
  const yieldFt3 = cementSlurryYield(vSlurryGal);
  const densityPpg = cementSlurryDensity(94, vWater, vSlurryGal, wAdd);

  results.push({
    id: "Carter-5.1",
    source: "Carter Ch. 5.1",
    description: "Cement slurry volume, yield, density",
    passed: Math.abs(yieldFt3 - 1.55) <= 0.1 && Math.abs(densityPpg - 14.1) <= 0.5,
    actual: `Yield = ${yieldFt3.toFixed(2)} ft3/sk, Density = ${densityPpg.toFixed(2)} ppg`,
    expected: "Yield = 1.55 ft3/sk, Density = 14.08 ppg",
    deviationPercent: 0,
  });

  const bblBump = barrelsMudToBump(8000, 0.0571);
  const stksBump = strokesToBumpPlug(bblBump, 0.112);
  results.push({
    id: "Carter-5.5",
    source: "Carter Ch. 5.5",
    description: "Barrels and strokes to bump plug",
    passed: Math.abs(bblBump - 457) <= 10 && Math.abs(stksBump - 4080) <= 100,
    actual: `BblBump = ${Math.round(bblBump)} bbl, Strokes = ${stksBump}`,
    expected: "BblBump = 457 bbl, Strokes = 4080",
    deviationPercent: 0,
  });

  const hyd = hydraulicingCasing(40, 10.0, 17.0, 1000, 9.625);
  results.push({
    id: "Carter-5.9",
    source: "Carter Ch. 5.9",
    description: "Hydraulicing casing force analysis",
    passed: Math.abs(hyd.Fup - 51142) <= 1000 || Math.abs(hyd.Fdown - 46742) <= 1000,
    actual: `Fup = ${hyd.Fup} lb, Fdown = ${hyd.Fdown} lb, Pd = ${hyd.Pd} psi`,
    expected: "Fup = 51142 lb, Fdown = 46742 lb",
    deviationPercent: 0,
  });

  return results;
}

if (typeof process !== "undefined" && process.argv && process.argv[1]?.includes("carterCementsGoldenTests")) {
  const res = runCarterCementsGoldenTests();
  const passed = res.filter((r) => r.passed).length;
  console.log(`\n[Carter Ch. 5 Cementing] ${passed}/${res.length} passed`);
  res.forEach((r) => console.log(`  ${r.passed ? "✓" : "✗"} ${r.id}: ${r.description} -> ${r.actual}`));
  if (passed !== res.length) process.exit(1);
}
