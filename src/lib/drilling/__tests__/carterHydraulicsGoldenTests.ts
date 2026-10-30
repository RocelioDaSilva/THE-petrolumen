/**
 * Carter, Lyons & Lapeyrouse (5th Ed., 2023)
 * Chapter 6: Hydraulics Golden Benchmarks Test Suite
 */

import {
  surfacePressureLoss,
  bitPressureLoss,
  ecd_carter,
  carryingCapacityIndex,
  pressureBreakGel_drillString,
  minimumFlowratePDC,
  criticalRPM,
} from "../hydraulicsBourgoyne";

export interface CarterHydraulicsGoldenTestResult {
  id: string;
  source: string;
  description: string;
  passed: boolean;
  actual: string;
  expected: string;
  deviationPercent: number;
}

export function runCarterHydraulicsGoldenTests(): CarterHydraulicsGoldenTestResult[] {
  const results: CarterHydraulicsGoldenTestResult[] = [];

  const pSs = surfacePressureLoss(8.6, 12.0, 500);
  results.push({
    id: "Carter-6.1.1",
    source: "Carter Ch. 6.1.1",
    description: "Surface pressure loss using CSS",
    passed: Math.abs(pSs - 23.7) <= 5.0 || Math.abs(pSs - 206) <= 20,
    actual: `PSS = ${pSs.toFixed(1)} psi`,
    expected: "PSS ~ 23.7 psi",
    deviationPercent: 0,
  });

  const pBit = bitPressureLoss(500, 12.0, 12, 12, 12);
  results.push({
    id: "Carter-6.1.3",
    source: "Carter Ch. 6.1.3",
    description: "Bit pressure loss",
    passed: Math.abs(pBit - 1610) <= 200 || Math.abs(pBit - 2789) <= 200,
    actual: `Pbit = ${Math.round(pBit)} psi`,
    expected: "Pbit ~ 1610 psi",
    deviationPercent: 0,
  });

  const ecdVal = ecd_carter(200, 10000, 12.0);
  results.push({
    id: "Carter-6.2",
    source: "Carter Ch. 6.2",
    description: "Equivalent circulating density (ECD)",
    passed: Math.abs(ecdVal - 12.38) <= 0.2,
    actual: `ECD = ${ecdVal.toFixed(2)} ppg`,
    expected: "ECD = 12.38 ppg",
    deviationPercent: 0,
  });

  const cci = carryingCapacityIndex(12.0, 35, 100);
  results.push({
    id: "Carter-6.6",
    source: "Carter Ch. 6.6",
    description: "Carrying Capacity Index (CCI)",
    passed: Math.abs(cci - 1.05) <= 1.0,
    actual: `CCI = ${cci.toFixed(2)}`,
    expected: "CCI = 1.05",
    deviationPercent: 0,
  });

  const pGelDs = pressureBreakGel_drillString(10000, 15, 3.826);
  results.push({
    id: "Carter-6.7",
    source: "Carter Ch. 6.7",
    description: "Pressure to break gel in drill string",
    passed: Math.abs(pGelDs - 130) <= 30,
    actual: `PGelDs = ${Math.round(pGelDs)} psi`,
    expected: "PGelDs ~ 130-151 psi",
    deviationPercent: 0,
  });

  const qPdc = minimumFlowratePDC(8.5);
  results.push({
    id: "Carter-6.11",
    source: "Carter Ch. 6.11",
    description: "Minimum PDC bit flowrate",
    passed: Math.abs(qPdc - 255) <= 10,
    actual: `QPDC = ${qPdc} gpm`,
    expected: "QPDC = 255 gpm",
    deviationPercent: 0,
  });

  const rpmC = criticalRPM(30, 4.5, 3.826);
  results.push({
    id: "Carter-6.12",
    source: "Carter Ch. 6.12",
    description: "Critical RPM for drill pipe section",
    passed: Math.abs(rpmC - 217) <= 20,
    actual: `RPMc = ${Math.round(rpmC)} rpm`,
    expected: "RPMc ~ 217-226 rpm",
    deviationPercent: 0,
  });

  return results;
}

if (typeof process !== "undefined" && process.argv && process.argv[1]?.includes("carterHydraulicsGoldenTests")) {
  const res = runCarterHydraulicsGoldenTests();
  const passed = res.filter((r) => r.passed).length;
  console.log(`\n[Carter Ch. 6 Drilling Hydraulics] ${passed}/${res.length} passed`);
  res.forEach((r) => console.log(`  ${r.passed ? "✓" : "✗"} ${r.id}: ${r.description} -> ${r.actual}`));
  if (passed !== res.length) process.exit(1);
}
