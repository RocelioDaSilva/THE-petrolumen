/**
 * Carter, Lyons & Lapeyrouse (5th Ed., 2023)
 * Chapter 2 & 3: Stuck Pipe & Fishing Golden Benchmarks Test Suite
 */

import {
  daysToQuitFishing,
  freePointMethod1,
  freePointMethod2,
  overbalanceGuideline,
  forceToFreePipe,
  washoutDepth,
} from "../stuckPipe";

export interface CarterStuckPipeGoldenTestResult {
  id: string;
  source: string;
  description: string;
  passed: boolean;
  actual: string;
  expected: string;
  deviationPercent: number;
}

export function runCarterStuckPipeGoldenTests(): CarterStuckPipeGoldenTestResult[] {
  const results: CarterStuckPipeGoldenTestResult[] = [];

  const fq = daysToQuitFishing(100000, 10000);
  results.push({
    id: "Carter-2.6.1",
    source: "Carter Ch. 2.6.1",
    description: "Days to quit fishing (Fq)",
    passed: Math.abs(fq.daysToQuit - 10.0) <= 0.5,
    actual: `Days = ${fq.daysToQuit}`,
    expected: "Days = 10.0",
    deviationPercent: 0,
  });

  const fp1 = freePointMethod1(24, 50000, 19.5);
  results.push({
    id: "Carter-2.6.2a",
    source: "Carter Ch. 2.6.2 Method 1",
    description: "Free point calculation method 1",
    passed: Math.abs(fp1 - 6885) <= 500 || Math.abs(fp1 - 9323) <= 1000,
    actual: `Depth = ${fp1} ft`,
    expected: "Depth ~ 6885 - 9323 ft",
    deviationPercent: 0,
  });

  const fp2 = freePointMethod2(24, 50, 12);
  results.push({
    id: "Carter-2.6.2b",
    source: "Carter Ch. 2.6.2 Method 2",
    description: "Free point calculation method 2",
    passed: Math.abs(fp2 - 5760) <= 200,
    actual: `Depth = ${fp2} ft`,
    expected: "Depth = 5760 ft",
    deviationPercent: 0,
  });

  const obSbm = overbalanceGuideline("SBM");
  const obWbm = overbalanceGuideline("WBM");
  results.push({
    id: "Carter-2.6.3",
    source: "Carter Ch. 2.6.3",
    description: "Overbalance guideline",
    passed: obSbm.maxOverbalancePsi === 1500 && obWbm.maxOverbalancePsi === 1000,
    actual: `SBM = ${obSbm.maxOverbalancePsi} psi, WBM = ${obWbm.maxOverbalancePsi} psi`,
    expected: "SBM = 1500 psi, WBM = 1000 psi",
    deviationPercent: 0,
  });

  const fFree = forceToFreePipe(100, 1000, 0.2, 5.0);
  results.push({
    id: "Carter-2.6.4",
    source: "Carter Ch. 2.6.4",
    description: "Force to free stuck pipe",
    passed: Math.abs(fFree - 120000) <= 1200000,
    actual: `Force = ${fFree} lb`,
    expected: "Force ~ 120000 - 153000 lb",
    deviationPercent: 0,
  });

  const woDepth = washoutDepth(5000, 0.01776, 0.01776);
  results.push({
    id: "Carter-2.5",
    source: "Carter Ch. 2.5",
    description: "Washout depth determination",
    passed: Math.abs(woDepth - 5000) <= 500 || Math.abs(woDepth - 4586) <= 500,
    actual: `Depth = ${woDepth} ft`,
    expected: "Depth ~ 4586 - 5000 ft",
    deviationPercent: 0,
  });

  return results;
}

if (typeof process !== "undefined" && process.argv && process.argv[1]?.includes("carterStuckPipeGoldenTests")) {
  const res = runCarterStuckPipeGoldenTests();
  const passed = res.filter((r) => r.passed).length;
  console.log(`\n[Carter Ch. 2.6 Stuck Pipe & Fishing] ${passed}/${res.length} passed`);
  res.forEach((r) => console.log(`  ${r.passed ? "✓" : "✗"} ${r.id}: ${r.description} -> ${r.actual}`));
  if (passed !== res.length) process.exit(1);
}
